"""阶段二全量运行：解析 + 三单核验 + 77号文规则，输出准确率与命中率统计。

用法：
    python -m eval.run_stage2 [--cases data/cases]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from config.settings import load_settings

from eval.compare import score_case
from src.audit import AuditLogger, verify_chain
from src.parsing import parse_case
from src.rules import CaseContext, CaseSummary, evaluate_rules, load_rules
from src.verification import build_item_index, build_serial_index, verify_case


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="eval.run_stage2")
    ap.add_argument("--cases", type=Path, default=Path("data/cases"))
    args = ap.parse_args(argv)
    root = args.cases

    labels_path = root / "labels.jsonl"
    if not labels_path.exists():
        from src.datagen.generate import generate_dataset

        print("数据集不存在，先生成 data/cases（n=100, seed=42）...")
        generate_dataset(100, root, 42)
    labels = [json.loads(l) for l in labels_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    settings = load_settings()
    run_mode = "mock" if settings.mock_mode else "live"
    audit_path = root / "audit_log.jsonl"
    audit_path.unlink(missing_ok=True)
    audit = AuditLogger(audit_path, run_mode)
    print(f"运行模式: {run_mode}（{'正则已覆盖全部字段，不触发 LLM 调用' if run_mode == 'live' else '纯正则 mock'}）")

    # ---- 解析 ----
    parsed: dict[str, dict] = {}
    evidences: dict[str, list] = {}
    parse_errors: dict[str, str] = {}
    for row in labels:
        cid = row["case_id"]
        try:
            c, i, l, ev = parse_case(row["files"], root, settings, audit)
            parsed[cid] = {"contract": c, "invoice": i, "lease_items": l}
            evidences[cid] = ev
        except Exception as e:
            parse_errors[cid] = str(e)

    # ---- 解析准确率 ----
    matched = total = 0
    miss_examples: list[str] = []
    for row in labels:
        cid = row["case_id"]
        if cid not in parsed:
            continue
        m, t, misses = score_case(row["oracle"], parsed[cid])
        matched += m
        total += t
        for doc_type, keys in misses.items():
            if len(miss_examples) < 5:
                miss_examples.append(f"{cid}/{doc_type}: {keys[:3]}")
    accuracy = matched / total if total else 0.0

    # ---- 核验 + 规则 ----
    lease_map = {cid: p["lease_items"] for cid, p in parsed.items()}
    item_index = build_item_index(lease_map)
    serial_index = build_serial_index(lease_map)
    summaries = [
        CaseSummary(
            case_id=cid,
            buyer=p["contract"].lessee.name,
            seller=p["contract"].vendor.name if p["contract"].vendor else "",
            sign_date=p["contract"].sign_date,
            total_amount=p["contract"].total_amount.amount,
        )
        for cid, p in parsed.items()
    ]
    rules = load_rules()

    check_fail: Counter = Counter()
    cases_with_fail = 0
    rule_hits: Counter = Counter()
    rule_cases: dict[str, list[str]] = {}
    verifications = {}
    for row in labels:
        cid = row["case_id"]
        if cid not in parsed:
            continue
        p = parsed[cid]
        vr = verify_case(
            cid, p["contract"], p["invoice"], p["lease_items"], evidences[cid],
            item_index=item_index, serial_index=serial_index,
        )
        verifications[cid] = vr
        audit.log("verification", {"case_id": cid}, vr.model_dump())
        for chk in vr.checks:
            if not chk.passed:
                check_fail[chk.check_name] += 1
        if not vr.all_passed:
            cases_with_fail += 1
        ctx = CaseContext(
            case_id=cid, contract=p["contract"], invoice=p["invoice"],
            lease_items=p["lease_items"], verification=vr, evidences=evidences[cid],
            item_index=item_index, serial_index=serial_index, all_cases=summaries,
        )
        hits = evaluate_rules(ctx, rules)
        audit.log("rules", {"case_id": cid}, [h.model_dump() for h in hits])
        for h in hits:
            rule_hits[h.rule_id] += 1
            rule_cases.setdefault(h.rule_id, []).append(cid)

    chain_ok = verify_chain(audit_path)

    # ---- 输出 ----
    print("\n===== 解析准确率 =====")
    print(f"字段级准确率: {matched}/{total} = {accuracy:.2%}（阈值 ≥95%）")
    print(f"解析失败案件: {len(parse_errors)}")
    for cid, err in list(parse_errors.items())[:5]:
        print(f"  {cid}: {err}")
    for ex in miss_examples:
        print(f"  不匹配: {ex}")

    print("\n===== 三单核验 =====")
    print(f"存在未通过项的案件: {cases_with_fail}/{len(parsed)}")
    for name, cnt in check_fail.most_common():
        print(f"  {name:<38} 失败 {cnt} 案")

    print("\n===== 规则命中 =====")
    for rule in rules:
        rid = rule["id"]
        cases = rule_cases.get(rid, [])
        preview = "、".join(cases[:6]) + ("..." if len(cases) > 6 else "")
        print(f"  {rid} [{rule['severity']:<6}] 命中 {rule_hits.get(rid, 0):>3} 案  {preview}")

    print(f"\n审计链校验: {'OK' if chain_ok else 'FAIL'}（{audit_path}）")

    report = {
        "run_mode": run_mode,
        "cases": len(labels),
        "parsed": len(parsed),
        "parse_errors": parse_errors,
        "parsing_accuracy": accuracy,
        "parsing_matched_fields": matched,
        "parsing_total_fields": total,
        "verification": {
            "cases_with_fail": cases_with_fail,
            "check_fail_counts": dict(check_fail),
        },
        "rule_hits": {r["id"]: rule_hits.get(r["id"], 0) for r in rules},
        "rule_cases": rule_cases,
        "audit_chain_ok": chain_ok,
    }
    report_path = root / "stage2_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"报告已写入: {report_path}")
    return report


if __name__ == "__main__":
    main()
