"""评测主脚本（SPEC M12 / 第 6 节验收标准）。所有指标来自真实运行。

用法：
    python -m eval.run_eval --cases data/cases --mock     # 无 Key 全流程可跑
    python -m eval.run_eval --cases data/cases            # live（需 LLM_API_KEY）

口径（固定于本文件，不随主系统调参变动）：
- 欺诈判定：risk_score.total >= FRAUD_SCORE_THRESHOLD(60)
- 核验检出：verification.failed_count > 0
- 规则命中准确率：预测规则集合与按标签推定的期望集合完全一致的比例
- 证据链覆盖率：核验结论与规则命中中带有 ≥1 条字段级证据的比例
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from config.settings import load_settings

from eval.baseline import BASELINE_VERSION, predict_baseline_live, predict_baseline_mock
from eval.compare import score_case
from src.pipeline import run_pipeline
from src.parsing.reader import PdfTextReader

FRAUD_SCORE_THRESHOLD = 60.0  # 欺诈判定阈值（固定）

# 按标签推定的期望规则命中集合（数据集中账期均 ≤180 天，R77-001/002 不应命中；
# 主体无重名碰撞，R77-004 不应命中）
EXPECTED_RULES: dict[str | None, set] = {
    None: set(),
    "a_chengxing": {"R77-003"},
    "b_multi_pledge": {"R77-003", "R77-005"},
    "c_circular_trade": {"R77-003"},
}

TARGETS = {
    "extraction_accuracy": 0.95,
    "verification_f1": 0.90,
    "fraud_recall": 0.90,
    "fraud_fpr_max": 0.10,
    "rule_accuracy": 1.00,
    "evidence_coverage": 0.98,
    "adversarial_rate": 1.00,
    "case_seconds_max": 180.0,
    "cost_per_case_max": 0.5,
    "ablation_lift_min": 15.0,  # 百分点
}


def _prf(tp: int, fp: int, fn: int, tn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "fpr": round(fpr, 4),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _read_texts(cases_dir: Path, files: dict[str, str]) -> dict[str, str]:
    texts = {}
    for dt, rel in files.items():
        reader = PdfTextReader(cases_dir / rel)
        texts[dt] = reader.full_text()
        reader.close()
    return texts


def run_eval(
    cases_dir: str | Path,
    mock: bool = True,
    *,
    limit: int | None = None,
    out_dir: str | Path | None = None,
    price_per_1k_tokens: float = 0.0,
    baseline_workers: int = 2,  # 429 限流保护：基线并发固定为 2
) -> dict:
    root = Path(cases_dir)
    out = Path(out_dir) if out_dir else Path("eval/results")
    out.mkdir(parents=True, exist_ok=True)
    labels = [json.loads(l) for l in (root / "labels.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if limit:
        labels = labels[:limit]

    settings = load_settings()
    run_mode = "mock" if mock else "live"
    audit_path = out / "audit_eval.db"
    audit_path.unlink(missing_ok=True)

    # ---- 主系统：逐案跑 pipeline ----
    per_case = {}
    ext_m = ext_t = 0
    conclusions = covered = 0
    rule_exact = 0
    for row in labels:
        cid = row["case_id"]
        t0 = time.perf_counter()
        state = run_pipeline(
            cid, row["files"], run_mode,
            base_dir=root, audit_path=audit_path, out_dir=out / "reports" / cid,
            guard_llm=False,  # 批量评测关闭护栏 LLM 二次判定（规则库检测仍生效），控制时耗
        )
        elapsed = time.perf_counter() - t0

        m, t, _ = score_case(row["oracle"],
                             {"contract": state.contract, "invoice": state.invoice,
                              "lease_items": state.lease_items})
        ext_m += m
        ext_t += t
        checks = state.verification.checks if state.verification else []
        conclusions += len(checks) + len(state.rule_hits)
        covered += sum(1 for c in checks if c.evidences) + sum(1 for h in state.rule_hits if h.evidences)
        predicted_rules = {h.rule_id for h in state.rule_hits}
        if predicted_rules == EXPECTED_RULES[row["fraud_pattern"]]:
            rule_exact += 1
        per_case[cid] = {
            "is_fraud": row["is_fraud"],
            "fraud_pattern": row["fraud_pattern"],
            "score": state.risk_score.total if state.risk_score else None,
            "grade": state.risk_score.grade if state.risk_score else None,
            "verify_failed": state.verification.failed_count if state.verification else None,
            "rules": sorted(predicted_rules),
            "elapsed": round(elapsed, 3),
            "errors": state.errors,
        }

    # ---- 消融基线：纯 LLM 直判（mock 关键词），同一评测集 ----
    baseline_pred: dict[str, str] = {}  # case_id -> "fraud" / "normal" / "invalid"
    baseline_tokens = {"prompt": 0, "completion": 0}
    baseline_errors: list[str] = []

    def _baseline_one(row):
        cid = row["case_id"]
        texts = _read_texts(root, row["files"])
        if mock:
            return cid, ("fraud" if predict_baseline_mock(texts) else "normal"), 0, 0
        # v2：429/5xx 指数退避 + jitter（最多 3 次重试）在 baseline.py 内部完成；
        # invalid（解析失败/重试后仍失败/空响应）绝不默认映射为 fraud 或 normal。
        rec = predict_baseline_live(texts, settings, seed=f"{cid}:{BASELINE_VERSION}")
        if rec["label"] == "invalid":
            baseline_errors.append(
                f"{cid}: invalid: {rec.get('invalid_reason')}: {rec.get('error')}")
        return cid, rec["label"], rec["prompt_tokens"], rec["completion_tokens"]

    with ThreadPoolExecutor(max_workers=1 if mock else baseline_workers) as pool:
        for fut in pool.map(_baseline_one, labels):
            cid, pred, tp, tc = fut
            baseline_pred[cid] = pred
            baseline_tokens["prompt"] += tp
            baseline_tokens["completion"] += tc

    # ---- 指标 ----
    def _cm(pred_key):
        tp = fp = fn = tn = 0
        for cid, info in per_case.items():
            pred = pred_key(info)
            if pred and info["is_fraud"]:
                tp += 1
            elif pred and not info["is_fraud"]:
                fp += 1
            elif not pred and info["is_fraud"]:
                fn += 1
            else:
                tn += 1
        return _prf(tp, fp, fn, tn)

    verification_cm = _cm(lambda i: (i["verify_failed"] or 0) > 0)
    fraud_cm = _cm(lambda i: (i["score"] or 0) >= FRAUD_SCORE_THRESHOLD)
    # 基线混淆矩阵：invalid 案件从分母剔除，绝不默认映射为 fraud/normal
    baseline_invalid = sum(1 for c in per_case if baseline_pred[c] == "invalid")
    _bv = [(c, i) for c, i in per_case.items() if baseline_pred[c] != "invalid"]
    baseline_cm = _prf(
        sum(1 for c, i in _bv if baseline_pred[c] == "fraud" and i["is_fraud"]),
        sum(1 for c, i in _bv if baseline_pred[c] == "fraud" and not i["is_fraud"]),
        sum(1 for c, i in _bv if baseline_pred[c] == "normal" and i["is_fraud"]),
        sum(1 for c, i in _bv if baseline_pred[c] == "normal" and not i["is_fraud"]),
    )
    # sanity gate：单一类别输出或存在 invalid → 消融提升记 invalid/saturated，不算达标也不算未达标
    _valid_labels = {baseline_pred[c] for c, _ in _bv}
    baseline_single_class = len(_valid_labels) == 1 and len(_bv) > 0
    if baseline_single_class or baseline_invalid > 0:
        ablation_lift_status = "invalid"
    elif baseline_cm["recall"] >= 1.0:
        ablation_lift_status = "saturated_not_informative"  # 主系统召回不可能超过 100%
    else:
        ablation_lift_status = "valid"

    # 各造假模式召回（原因分析用）
    pattern_recall: dict[str, dict] = {}
    for pattern in ("a_chengxing", "b_multi_pledge", "c_circular_trade"):
        cases = [(c, i) for c, i in per_case.items() if i["fraud_pattern"] == pattern]
        if cases:
            hit = sum(1 for c, i in cases if (i["score"] or 0) >= FRAUD_SCORE_THRESHOLD)
            bhit = sum(1 for c, i in cases if baseline_pred[c] == "fraud")
            pattern_recall[pattern] = {
                "n": len(cases),
                "system_recall": round(hit / len(cases), 4),
                "baseline_recall": round(bhit / len(cases), 4),
            }

    from eval.adversarial.run import run_adversarial_suite

    adversarial = run_adversarial_suite()

    elapsed_list = [i["elapsed"] for i in per_case.values()]
    # 系统侧 LLM token：查审计库 llm_call 事件
    import sqlite3

    sys_tokens = 0
    if audit_path.exists():
        conn = sqlite3.connect(str(audit_path))
        row = conn.execute(
            "SELECT COALESCE(SUM(tokens_prompt),0) + COALESCE(SUM(tokens_completion),0)"
            " FROM audit_log WHERE event_type='llm_call'"
        ).fetchone()
        sys_tokens = row[0] if row else 0
        conn.close()
    n = len(per_case)
    sys_cost = sys_tokens / 1000 * price_per_1k_tokens
    baseline_total_tokens = baseline_tokens["prompt"] + baseline_tokens["completion"]

    metrics = {
        "run_mode": run_mode,
        "baseline_version": BASELINE_VERSION,
        "cases": n,
        "extraction_accuracy": round(ext_m / ext_t, 4) if ext_t else 0.0,
        "extraction_fields": f"{ext_m}/{ext_t}",
        "verification_f1": verification_cm["f1"],
        "verification_cm": verification_cm,
        "fraud_recall": fraud_cm["recall"],
        "fraud_fpr": fraud_cm["fpr"],
        "fraud_cm": fraud_cm,
        "rule_accuracy": round(rule_exact / n, 4) if n else 0.0,
        "evidence_coverage": round(covered / conclusions, 4) if conclusions else 0.0,
        "evidence_fields": f"{covered}/{conclusions}",
        "adversarial_rate": adversarial["rate"],
        "case_seconds_avg": round(sum(elapsed_list) / n, 3) if n else 0.0,
        "case_seconds_max": max(elapsed_list) if elapsed_list else 0.0,
        "system_llm_tokens": sys_tokens,
        "system_cost_yuan_total": round(sys_cost, 4),
        "system_cost_yuan_per_case": round(sys_cost / n, 6) if n else 0.0,
        "price_per_1k_tokens": price_per_1k_tokens,
        "baseline": {
            "type": "mock_keywords" if mock else "pure_llm",
            "recall": baseline_cm["recall"],
            "fpr": baseline_cm["fpr"],
            "cm": baseline_cm,
            "tokens": baseline_total_tokens,
            "invalid_count": baseline_invalid,
            "single_class_output": baseline_single_class,
        },
        "ablation_lift_pp": round((fraud_cm["recall"] - baseline_cm["recall"]) * 100, 1),
        "ablation_lift_status": ablation_lift_status,
        "pattern_recall": pattern_recall,
        "baseline_errors": baseline_errors,
        "per_case": per_case,
    }
    metrics["targets"] = TARGETS
    metrics["passed"] = {
        "extraction_accuracy": metrics["extraction_accuracy"] >= TARGETS["extraction_accuracy"],
        "verification_f1": metrics["verification_f1"] >= TARGETS["verification_f1"],
        "fraud_recall": metrics["fraud_recall"] >= TARGETS["fraud_recall"],
        "fraud_fpr": metrics["fraud_fpr"] <= TARGETS["fraud_fpr_max"],
        "rule_accuracy": metrics["rule_accuracy"] >= TARGETS["rule_accuracy"],
        "evidence_coverage": metrics["evidence_coverage"] >= TARGETS["evidence_coverage"],
        "adversarial_rate": metrics["adversarial_rate"] >= TARGETS["adversarial_rate"],
        "case_seconds": metrics["case_seconds_max"] <= TARGETS["case_seconds_max"],
        "cost_per_case": metrics["system_cost_yuan_per_case"] <= TARGETS["cost_per_case_max"],
        # 消融提升须先通过 sanity gate（非单一类别、无 invalid、非饱和）才谈达标
        "ablation_lift": ablation_lift_status == "valid"
        and metrics["ablation_lift_pp"] >= TARGETS["ablation_lift_min"],
    }
    return metrics


def render_tables(m: dict) -> str:
    """生成指标表 + 消融对比表（Markdown）。"""
    L = []
    p = m["passed"]
    L.append("| 指标 | 结果 | 目标 | 达标 |")
    L.append("|---|---|---|---|")
    rows = [
        ("要素抽取准确率", f"{m['extraction_accuracy']:.2%}（{m['extraction_fields']}）", "≥95%", p["extraction_accuracy"]),
        ("三单核验 F1", f"{m['verification_f1']:.4f}", "≥0.90", p["verification_f1"]),
        ("欺诈检出召回", f"{m['fraud_recall']:.2%}", "≥90%", p["fraud_recall"]),
        ("欺诈误报率", f"{m['fraud_fpr']:.2%}", "≤10%", p["fraud_fpr"]),
        ("规则命中准确率", f"{m['rule_accuracy']:.2%}", "100%", p["rule_accuracy"]),
        ("证据链覆盖率", f"{m['evidence_coverage']:.2%}（{m['evidence_fields']}）", "≥98%", p["evidence_coverage"]),
        ("对抗拦截率", f"{m['adversarial_rate']:.2%}", "100%", p["adversarial_rate"]),
        ("单案端到端时耗", f"均值 {m['case_seconds_avg']}s / 最大 {m['case_seconds_max']}s", "≤180s", p["case_seconds"]),
        ("LLM token 成本", f"{m['system_cost_yuan_per_case']} 元/案（{m['system_llm_tokens']} tokens，单价 {m['price_per_1k_tokens']} 元/K）", "≤0.5 元/案", p["cost_per_case"]),
    ]
    for name, val, target, ok in rows:
        L.append(f"| {name} | {val} | {target} | {'✅' if ok else '❌'} |")
    L.append("")
    L.append("### 消融对比：本系统 vs 纯 LLM 直判（基线 {}，{}）".format(
        m["baseline_version"], "mock 关键词" if m["baseline"]["type"] == "mock_keywords" else "真实 LLM"))
    L.append("")
    L.append("| 方案 | 欺诈召回 | 误报率 | 精确率 | F1 |")
    L.append("|---|---|---|---|---|")
    L.append(f"| 本系统 | {m['fraud_recall']:.2%} | {m['fraud_fpr']:.2%} | {m['fraud_cm']['precision']:.2%} | {m['fraud_cm']['f1']:.4f} |")
    L.append(f"| 纯 LLM 直判 | {m['baseline']['recall']:.2%} | {m['baseline']['fpr']:.2%} | {m['baseline']['cm']['precision']:.2%} | {m['baseline']['cm']['f1']:.4f} |")
    lift_status = m.get("ablation_lift_status", "valid")
    if lift_status == "valid":
        verdict = "✅" if p["ablation_lift"] else "❌"
    else:
        verdict = f"⚠️ {lift_status}（不计达标/未达标）"
    L.append(f"| **检出率（召回）差值** | **+{m['ablation_lift_pp']}pp** | | | 目标 ≥15pp：{verdict} |")
    L.append("")
    if m["baseline_errors"]:
        L.append(f"> 基线 invalid/失败 {len(m['baseline_errors'])} 次（已从指标分母剔除，未默认映射为 fraud/normal，见 JSON baseline_errors）。")
        L.append("")
    L.append("### 分造假模式召回")
    L.append("")
    L.append("| 模式 | 样本数 | 本系统召回 | 基线召回 |")
    L.append("|---|---|---|---|")
    for pattern, pr in m["pattern_recall"].items():
        L.append(f"| {pattern} | {pr['n']} | {pr['system_recall']:.2%} | {pr['baseline_recall']:.2%} |")
    L.append("")
    failed = [k for k, ok in p.items() if not ok]
    if failed:
        L.append(f"### 未达标项\n")
        for k in failed:
            L.append(f"- **{k}**：见 JSON 中 per_case 明细与 pattern_recall 分析")
    else:
        L.append("### 未达标项\n\n无。")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="eval.run_eval")
    ap.add_argument("--cases", type=Path, default=Path("data/cases"))
    ap.add_argument("--mock", action="store_true", help="mock 模式（不调 LLM，成本为 0）")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--price-per-1k-tokens", type=float, default=0.0,
                    help="API 公开单价（元/K tokens），用于成本折算；默认 0（仅统计 token 数）")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--rerun-baseline-only", action="store_true",
                    help="只重跑消融基线（复用修复前主系统结果，委托 eval/rerun_baseline.py）")
    args = ap.parse_args(argv)

    if args.rerun_baseline_only:
        from eval.rerun_baseline import main as rerun_main
        rargv = ["--cases", str(args.cases)]
        if args.mock:
            rargv.append("--mock")
        if args.limit:
            rargv += ["--limit", str(args.limit)]
        if args.out is not None:
            rargv += ["--out", str(args.out)]
        return rerun_main(rargv)

    out_dir = args.out or Path("eval/results")
    mock = args.mock or load_settings().mock_mode
    if not args.mock and load_settings().mock_mode:
        print("未配置 LLM_API_KEY，自动按 mock 模式评测")
    m = run_eval(args.cases, mock, limit=args.limit,
                 out_dir=out_dir, price_per_1k_tokens=args.price_per_1k_tokens)

    table = render_tables(m)
    print(f"\n===== 评测结果（{m['run_mode']} 模式，{m['cases']} 案）=====\n")
    print(table)

    (out_dir / "eval_results.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "eval_results.md").write_text(
        f"# 评测报告（{m['run_mode']} 模式）\n\n" + table + "\n", encoding="utf-8")
    print(f"\n结果已落盘: {out_dir / 'eval_results.json'} / {out_dir / 'eval_results.md'}")
    return m


if __name__ == "__main__":
    main()
