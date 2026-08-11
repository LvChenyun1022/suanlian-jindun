"""消融基线单独重跑（消融基线有效性复核）。

只重跑基线、不动主系统：
- 主系统侧数字继承自修复前全量运行结果（--before，默认
  eval/results_live/eval_results_before_baseline_fix.json），不重跑 pipeline；
- 基线逐案调用 eval/baseline.py v2 固定 prompt（temperature=0），并发 2，
  指数退避 + jitter（2/4/8/16s，最多 3 次重试，逻辑在 baseline.py 内）；
- 写穿缓存 eval/results/baseline_cache.jsonl：成功（label != invalid）案件立即落盘，
  中断/限流后续跑只补失败案件；
- 全量逐案审计写入 eval/results/baseline_audit.jsonl（完整 prompt / raw response /
  解析后标签 / HTTP 状态 / finish_reason / token 用量 / 重试次数）；
- sanity gate：基线输出单一类别或 invalid_count > 0 → "欺诈检出率提升"记 invalid；
  基线召回 = 100% → 记 saturated/not informative（主系统召回不可能超过 100%，
  +15pp 数学上不可达），并补充 F1 / 精确率 / FPR / balanced accuracy / MCC；
- 结果落盘 eval/results_live/eval_results_after_baseline_fix.{json,md}，
  不覆盖 *_before_baseline_fix.*。
"""
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from config.settings import load_settings
from eval.baseline import (
    BASELINE_VERSION,
    predict_baseline_live,
    predict_baseline_mock,
)
from eval.run_eval import FRAUD_SCORE_THRESHOLD, _read_texts

CACHE_PATH = Path("eval/results/baseline_cache.jsonl")
AUDIT_PATH = Path("eval/results/baseline_audit.jsonl")

# 模板泄漏抽查线索词（正常案件文本不应出现）
LEAK_CUES = ["账期：0 天", "伪造", "虚假", "欺诈", "重复质押", "一单多押", "空转"]
LEAK_CHECK_N = 10


# ---------------------------------------------------------------- 缓存


def load_cache(path: Path) -> dict[str, dict]:
    """读取写穿缓存，只保留当前基线版本且判定有效（非 invalid）的记录。"""
    records: dict[str, dict] = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("baseline_version") != BASELINE_VERSION:
            continue
        if rec.get("label") in ("fraud", "normal"):
            records[rec["case_id"]] = rec
    return records


def append_cache(path: Path, rec: dict) -> None:
    """写穿追加：每条成功记录立即落盘（中断可续跑）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- 指标


def cm_metrics(pairs: list[tuple[bool, bool]]) -> dict:
    """由 (预测是否欺诈, 真实是否欺诈) 序列计算全套指标。

    含 precision / recall / F1 / FPR / balanced accuracy / MCC（分母为 0 时 MCC=0.0）。
    """
    tp = sum(1 for p, a in pairs if p and a)
    fp = sum(1 for p, a in pairs if p and not a)
    fn = sum(1 for p, a in pairs if not p and a)
    tn = sum(1 for p, a in pairs if not p and not a)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    balanced_acc = (recall + specificity) / 2
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denom if denom else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "specificity": round(specificity, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "mcc": round(mcc, 4),
    }


def cm_from_counts(cm: dict) -> dict:
    """由已有混淆矩阵计数（主系统侧，来自修复前结果）补全扩展指标。"""
    pairs: list[tuple[bool, bool]] = (
        [(True, True)] * cm["tp"] + [(True, False)] * cm["fp"]
        + [(False, True)] * cm["fn"] + [(False, False)] * cm["tn"]
    )
    return cm_metrics(pairs)


# ---------------------------------------------------------------- 模板泄漏抽查


def check_template_leakage(labels: list[dict], root: Path, n: int = LEAK_CHECK_N) -> dict:
    """抽查前 n 个正常案件文本，检查是否混入模板错误导致的欺诈线索词。"""
    normal = [r for r in labels if not r["is_fraud"]][:n]
    hits: list[dict] = []
    for row in normal:
        texts = _read_texts(root, row["files"])
        for doc_type, text in texts.items():
            for cue in LEAK_CUES:
                if cue in text:
                    hits.append({"case_id": row["case_id"], "doc": doc_type, "cue": cue})
    return {
        "checked_case_ids": [r["case_id"] for r in normal],
        "cue_words": LEAK_CUES,
        "hit_count": len(hits),
        "hits": hits,
        "note": "所有单据每页固定含合成数据免责声明（预期内，不计为泄漏）。",
    }


# ---------------------------------------------------------------- 主流程


def _mock_record(case_id: str, pred: bool) -> dict:
    return {
        "baseline_version": BASELINE_VERSION,
        "model": "mock-keywords",
        "prompt": None,
        "label": "fraud" if pred else "normal",
        "invalid_reason": None,
        "raw_response": None,
        "finish_reason": None,
        "http_status": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "retry_count": 0,
        "error": None,
        "saw_429": False,
        "case_id": case_id,
    }


def run_baseline_rerun(
    cases_dir: str | Path,
    mock: bool = False,
    *,
    limit: int | None = None,
    workers: int = 2,
    out_dir: str | Path = Path("eval/results_live"),
    before_path: str | Path = Path("eval/results_live/eval_results_before_baseline_fix.json"),
    cache_path: str | Path = CACHE_PATH,
    audit_path: str | Path = AUDIT_PATH,
) -> dict:
    root = Path(cases_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cache_path = Path(cache_path)
    audit_path = Path(audit_path)
    before_path = Path(before_path)

    labels = [
        json.loads(l)
        for l in (root / "labels.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    if limit:
        labels = labels[:limit]
    truth = {r["case_id"]: r for r in labels}

    settings = load_settings()
    mock = mock or settings.mock_mode

    # ---- 缓存：只重跑无成功记录的案件 ----
    cached = {} if mock else load_cache(cache_path)
    todo = [r for r in labels if r["case_id"] not in cached]
    t0 = time.perf_counter()

    def _one(row: dict) -> dict:
        cid = row["case_id"]
        texts = _read_texts(root, row["files"])
        if mock:
            return _mock_record(cid, predict_baseline_mock(texts))
        rec = predict_baseline_live(texts, settings, seed=f"{cid}:{BASELINE_VERSION}")
        rec["case_id"] = cid
        return rec

    new_records: list[dict] = []
    if todo:
        with ThreadPoolExecutor(max_workers=1 if mock else workers) as pool:
            for rec in pool.map(_one, todo):
                new_records.append(rec)
                if not mock and rec["label"] != "invalid":
                    append_cache(cache_path, rec)  # 写穿：成功立即落盘
    elapsed = time.perf_counter() - t0

    records: dict[str, dict] = dict(cached)
    for rec in new_records:
        # 新记录覆盖缓存（新 invalid 不覆盖已有的有效缓存，防御性逻辑）
        if rec["label"] != "invalid" or rec["case_id"] not in records:
            records[rec["case_id"]] = rec

    # ---- 逐案审计 JSONL（全量，含完整 prompt 与 raw response）----
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as f:
        for cid in sorted(records):
            rec = records[cid]
            row = truth[cid]
            f.write(json.dumps({
                "case_id": cid,
                "is_fraud": row["is_fraud"],
                "fraud_pattern": row["fraud_pattern"],
                **rec,
            }, ensure_ascii=False) + "\n")

    # ---- 指标（invalid 案件从分母剔除，单列统计）----
    label_dist = Counter(rec["label"] for rec in records.values())
    valid_pairs = [
        (records[cid]["label"] == "fraud", truth[cid]["is_fraud"])
        for cid in sorted(records)
        if records[cid]["label"] != "invalid"
    ]
    invalid_ids = sorted(cid for cid in records if records[cid]["label"] == "invalid")
    baseline_cm = cm_metrics(valid_pairs)

    pattern_recall: dict[str, dict] = {}
    for pattern in ("a_chengxing", "b_multi_pledge", "c_circular_trade"):
        cids = [c for c in records
                if truth[c]["fraud_pattern"] == pattern and records[c]["label"] != "invalid"]
        if cids:
            hit = sum(1 for c in cids if records[c]["label"] == "fraud")
            pattern_recall[pattern] = {"n_valid": len(cids), "recall": round(hit / len(cids), 4)}

    # ---- sanity gate ----
    valid_labels = {records[cid]["label"] for cid in records if records[cid]["label"] != "invalid"}
    single_class = len(valid_labels) == 1 and len(valid_pairs) > 0
    single_class_value = next(iter(valid_labels)) if single_class else None
    saturated = baseline_cm["recall"] >= 1.0 and not single_class
    if single_class:
        lift_status = "invalid"
        lift_note = (f"基线对评测集输出单一类别（全部 {single_class_value}），"
                     "召回提升指标无效，不能表述为达标或未达标。")
    elif invalid_ids:
        lift_status = "invalid"
        lift_note = (f"存在 {len(invalid_ids)} 个 invalid 案件（解析/调用失败），"
                     "本轮召回提升记为 invalid，不能表述为达标或未达标。")
    elif saturated:
        lift_status = "saturated_not_informative"
        lift_note = ("基线召回 = 100%，主系统召回数学上不可能超过 100%，"
                     "'召回提升 ≥15pp' 对该基线饱和、不具信息量；"
                     "应以 F1 / 精确率 / FPR / balanced accuracy / MCC 辅助对比，"
                     "不得宣称 +15pp 已达成。")
    else:
        lift_status = "valid"
        lift_note = "基线输出分布正常，召回提升指标有效。"

    # ---- 主系统侧（继承修复前全量运行结果，代码与数据均未变）----
    system_side = None
    if before_path.exists():
        before = json.loads(before_path.read_text(encoding="utf-8"))
        system_side = {
            "source": str(before_path),
            "note": "主系统指标继承自修复前全量运行（主系统代码/权重/标签/评测集均未改动）。",
            "fraud_cm": cm_from_counts(before["fraud_cm"]),
            "baseline_v1": {
                "version": before.get("baseline_version"),
                "cm": cm_from_counts(before["baseline"]["cm"]),
                "tokens": before["baseline"].get("tokens"),
                "note": "v1 仅持久化聚合混淆矩阵，逐案 raw response 未留存，无法逐一审计。",
            },
            "ablation_lift_pp_v1": before.get("ablation_lift_pp"),
        }
        system_cm = system_side["fraud_cm"]
    else:
        system_cm = None

    lift_pp = None
    if system_cm is not None and not single_class:
        lift_pp = round((system_cm["recall"] - baseline_cm["recall"]) * 100, 1)

    # ---- 模板泄漏抽查 ----
    leakage = check_template_leakage(labels, root)

    result = {
        "audit_type": "baseline_validity_review",
        "baseline_version": BASELINE_VERSION,
        "run_mode": "mock" if mock else "live",
        "cases": len(records),
        "cases_rerun_this_round": len(new_records),
        "cases_from_cache": len(cached),
        "rerun_elapsed_seconds": round(elapsed, 1),
        "invalid_count": len(invalid_ids),
        "invalid_case_ids": invalid_ids,
        "label_distribution": dict(label_dist),
        "retry_count_total": sum(r.get("retry_count", 0) for r in records.values()),
        "429_count": sum(1 for r in records.values() if r.get("saw_429")),
        "tokens": {
            "prompt": sum(r.get("prompt_tokens", 0) for r in records.values()),
            "completion": sum(r.get("completion_tokens", 0) for r in records.values()),
        },
        "baseline_cm": baseline_cm,
        "baseline_pattern_recall": pattern_recall,
        "sanity_gate": {
            "single_class_output": single_class,
            "single_class_value": single_class_value,
            "invalid_count": len(invalid_ids),
            "baseline_recall": baseline_cm["recall"],
            "lift_status": lift_status,
            "note": lift_note,
        },
        "ablation_lift_pp": lift_pp,
        "system_side": system_side,
        "template_leakage_check": leakage,
        "audit_jsonl": str(audit_path),
        "cache_file": str(cache_path) if not mock else None,
    }

    (out / "eval_results_after_baseline_fix.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_report(result)
    (out / "eval_results_after_baseline_fix.md").write_text(md, encoding="utf-8")
    return result


# ---------------------------------------------------------------- 报告


def _row(name: str, cm: dict) -> str:
    return (f"| {name} | {cm['recall']:.2%} | {cm['fpr']:.2%} | {cm['precision']:.2%} "
            f"| {cm['f1']:.4f} | {cm['balanced_accuracy']:.4f} | {cm['mcc']:.4f} |")


def render_report(r: dict) -> str:
    L: list[str] = []
    L.append(f"# 消融基线有效性复核报告（{r['run_mode']}，基线 {r['baseline_version']}）\n")
    g = r["sanity_gate"]
    L.append("## 基线审计摘要\n")
    L.append(f"- 评测案件：{r['cases']}（本轮新跑 {r['cases_rerun_this_round']}，缓存复用 {r['cases_from_cache']}）")
    L.append(f"- 标签分布：{json.dumps(r['label_distribution'], ensure_ascii=False)}")
    L.append(f"- invalid_count：{r['invalid_count']}"
             + (f"（{', '.join(r['invalid_case_ids'][:10])}{'…' if r['invalid_count'] > 10 else ''}）" if r["invalid_count"] else ""))
    L.append(f"- 重试总次数：{r['retry_count_total']}；遭遇 429 的案件数：{r['429_count']}")
    L.append(f"- token 用量：prompt {r['tokens']['prompt']} + completion {r['tokens']['completion']}"
             f" = {r['tokens']['prompt'] + r['tokens']['completion']}")
    L.append(f"- 本轮重跑耗时：{r['rerun_elapsed_seconds']}s")
    L.append(f"- 逐案审计：{r['audit_jsonl']}"
             + (f"；缓存：{r['cache_file']}" if r.get("cache_file") else ""))
    L.append("")
    L.append("## 模板泄漏抽查（10 个正常案件）\n")
    lk = r["template_leakage_check"]
    L.append(f"- 抽查案件：{', '.join(lk['checked_case_ids'])}")
    L.append(f"- 线索词：{', '.join(lk['cue_words'])}")
    L.append(f"- 命中数：{lk['hit_count']}" + ("（无模板泄漏）" if lk["hit_count"] == 0 else f" ⚠️ {lk['hits']}"))
    L.append(f"- 备注：{lk['note']}")
    L.append("")
    L.append("## Sanity gate\n")
    L.append(f"- 单一类别输出：{g['single_class_output']}" + (f"（{g['single_class_value']}）" if g["single_class_value"] else ""))
    L.append(f"- invalid_count > 0：{g['invalid_count'] > 0}")
    L.append(f"- 基线召回：{g['baseline_recall']:.2%}")
    L.append(f"- **召回提升状态：{g['lift_status']}**")
    L.append(f"- 说明：{g['note']}")
    L.append("")
    if r.get("system_side"):
        s = r["system_side"]
        L.append("## 修复前对比（基线 {}，仅聚合数字可查）\n".format(s["baseline_v1"]["version"]))
        L.append("| 方案 | 召回 | FPR | 精确率 | F1 | BA | MCC |")
        L.append("|---|---|---|---|---|---|---|")
        L.append(_row("本系统", s["fraud_cm"]))
        L.append(_row(f"纯 LLM 直判（{s['baseline_v1']['version']}）", s["baseline_v1"]["cm"]))
        L.append(f"| **召回差值** | **{r['ablation_lift_pp'] if False else s['ablation_lift_pp_v1']}pp** | | | | | |")
        L.append("")
        L.append(f"> {s['baseline_v1']['note']}")
        L.append("")
        L.append(f"## 修复后对比（基线 {r['baseline_version']}）\n")
        L.append("| 方案 | 召回 | FPR | 精确率 | F1 | BA | MCC |")
        L.append("|---|---|---|---|---|---|---|")
        L.append(_row("本系统", s["fraud_cm"]))
        L.append(_row(f"纯 LLM 直判（{r['baseline_version']}）", r["baseline_cm"]))
        lift_txt = f"{r['ablation_lift_pp']}pp" if r["ablation_lift_pp"] is not None else "N/A"
        L.append(f"| **召回差值** | **{lift_txt}** | 状态：{g['lift_status']} | | | | |")
        L.append("")
        L.append(f"> {s['note']}")
        L.append("")
    L.append("## 分造假模式基线召回（修复后，仅有效判定计入）\n")
    L.append("| 模式 | 有效样本数 | 基线召回 |")
    L.append("|---|---|---|")
    for pattern, pr in r["baseline_pattern_recall"].items():
        L.append(f"| {pattern} | {pr['n_valid']} | {pr['recall']:.2%} |")
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="eval.rerun_baseline")
    ap.add_argument("--cases", type=Path, default=Path("data/cases"))
    ap.add_argument("--mock", action="store_true", help="mock 关键词基线（不调 LLM）")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=2, help="基线并发（429 限流保护，默认 2）")
    ap.add_argument("--out", type=Path, default=Path("eval/results_live"))
    ap.add_argument("--before", type=Path,
                    default=Path("eval/results_live/eval_results_before_baseline_fix.json"))
    ap.add_argument("--cache", type=Path, default=CACHE_PATH)
    ap.add_argument("--audit", type=Path, default=AUDIT_PATH)
    args = ap.parse_args(argv)

    r = run_baseline_rerun(
        args.cases, args.mock, limit=args.limit, workers=args.workers,
        out_dir=args.out, before_path=args.before,
        cache_path=args.cache, audit_path=args.audit,
    )
    print(render_report(r))
    print(f"结果已落盘: {args.out / 'eval_results_after_baseline_fix.json'} / "
          f"{args.out / 'eval_results_after_baseline_fix.md'}")
    print(f"逐案审计: {args.audit}")
    return r


if __name__ == "__main__":
    main()
