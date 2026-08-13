"""纯 Python 顺序 pipeline（SPEC 第 4 节）：串联护栏→解析→核验→规则→压力→预警→评分→报告。

- 全程写 SQLite 审计日志（append-only 哈希链）；
- LLM 统一封装于 src/parsing/llm.py（OpenAI-compatible），无 Key 时 mock 全链路可跑；
- LangGraph 等价编排见 src/pipeline_langgraph.py（可选，未安装不影响本模块）。

CLI：
    python -m src.pipeline --case data/cases/case_0001 --mock
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from config.settings import LLMSettings, load_settings

from .asset import run_stress_test
from .audit.sqlite_store import SqliteAuditStore
from .errors import GuardrailViolation, JinDunError
from .guardrails import ToolRegistry, check_user_text
from .monitoring import detect_alerts, fetch_external_signals, mock_telemetry_feed
from .parsing import parse_case
from .parsing.reader import PdfTextReader
from .report import build_report, export_audit_package
from .rules import CaseContext, CaseSummary, evaluate_rules, load_rules
from .schemas import PipelineState
from .scoring import score_case
from .verification import verify_case


@dataclass
class PipelineRuntime:
    """pipeline 运行上下文（配置/审计/跨案件索引/工具白名单）。"""

    settings: LLMSettings
    run_mode: str
    base_dir: Path
    audit: SqliteAuditStore
    tools: ToolRegistry
    item_index: dict[str, set[str]] = field(default_factory=dict)
    serial_index: dict[str, set[str]] = field(default_factory=dict)
    all_cases: list[CaseSummary] = field(default_factory=list)
    out_dir: Path | None = None
    guard_llm: bool = True  # 护栏 LLM 二次判定（可选；评测批跑时可关闭以控制时耗）


def build_default_registry(audit: SqliteAuditStore) -> ToolRegistry:
    """注册 pipeline 允许使用的工具白名单。"""
    reg = ToolRegistry(audit)
    reg.register("pdf_text_extract", lambda p: PdfTextReader(p).full_text())
    reg.register("telemetry_feed", mock_telemetry_feed)
    reg.register("external_signals", fetch_external_signals)
    return reg


def load_dataset_context(labels_path: str | Path) -> tuple[dict, dict, list[CaseSummary]]:
    """从 labels.jsonl 构建跨案件模拟登记索引与案件摘要（不解析 PDF，快速）。"""
    labels_path = Path(labels_path)
    item_index: dict[str, set[str]] = {}
    serial_index: dict[str, set[str]] = {}
    summaries: list[CaseSummary] = []
    if not labels_path.exists():
        return item_index, serial_index, summaries
    for line in labels_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cid = row["case_id"]
        for key, info in row["oracle"]["lease_items"]["fields"].items():
            if key.endswith(".item_id"):
                item_index.setdefault(info["value"], set()).add(cid)
            elif key.endswith(".serial_no"):
                serial_index.setdefault(info["value"], set()).add(cid)
        meta = row["metadata"]
        summaries.append(CaseSummary(
            case_id=cid,
            buyer=meta["buyer"],
            seller=meta["seller"],
            sign_date=date.fromisoformat(meta["sign_date"]),
            total_amount=float(meta["total_amount"]),
        ))
    return item_index, serial_index, summaries


# ---------- 各环节（SPEC 4.3 签名：state 进 / state 出） ----------

def stage_guardrail_in(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    """入口护栏：对单据外部文本做注入/敏感数据检测。命中则记录 errors 并中止。"""
    for doc_type, rel in state.files.items():
        text = rt.tools.call("pdf_text_extract", rt.base_dir / rel, case_id=state.case_id)
        check_user_text(text, use_llm=(state.run_mode == "live" and rt.guard_llm),
                        settings=rt.settings, audit=rt.audit, case_id=state.case_id)
    rt.audit.log("guardrail_in", {"case_id": state.case_id}, {"passed": True},
                 case_id=state.case_id)
    return state


def stage_parse(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    c, i, l, ev = parse_case(state.files, rt.base_dir, rt.settings)
    state.contract, state.invoice, state.lease_items, state.evidences = c, i, l, ev
    rt.audit.log("parsing", {"case_id": state.case_id},
                 {"fields": len(ev)}, case_id=state.case_id)
    return state


def stage_validate(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    """字段级交叉校验（v3）：金额大写/小写交叉 + 期限边界/一致性。

    挂在解析层之后，不改变抽取接口；review 级标记 = 字段置信度置 0 转人审
    （与 ocr_low_confidence 同路由），审计日志记录原始值掩码。
    """
    from .parsing.reader import PdfTextReader
    from .validation import validate_document

    flags = []
    for doc_kind in ("contract", "invoice"):
        rel = state.files.get(doc_kind)
        if not rel:
            continue
        reader = PdfTextReader(rt.base_dir / rel)
        text = reader.full_text()
        reader.close()
        flags += validate_document(text, doc_kind)
    state.validation_flags = flags
    rt.audit.log(
        "validation", {"case_id": state.case_id},
        {"review": [f.reason_code for f in flags if f.severity == "review"],
         "info": [f.reason_code for f in flags if f.severity == "info"],
         "raw_masked": [f.raw_masked for f in flags if f.severity == "review"]},
        case_id=state.case_id,
        detail="字段级交叉校验：" + ("；".join(
            f"{f.field_name}/{f.reason_code}" for f in flags if f.severity == "review"
        ) or "无 review 标记"))
    return state


def stage_verify(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    state.verification = verify_case(
        state.case_id, state.contract, state.invoice, state.lease_items, state.evidences,
        item_index=rt.item_index or None, serial_index=rt.serial_index or None,
    )
    rt.audit.log("verification", {"case_id": state.case_id},
                 {"passed": state.verification.passed_count, "failed": state.verification.failed_count},
                 case_id=state.case_id)
    return state


def stage_rules(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    ctx = CaseContext(
        case_id=state.case_id, contract=state.contract, invoice=state.invoice,
        lease_items=state.lease_items, verification=state.verification,
        evidences=state.evidences, item_index=rt.item_index or None,
        serial_index=rt.serial_index or None, all_cases=rt.all_cases,
    )
    state.rule_hits = evaluate_rules(ctx, load_rules())
    rt.audit.log("rules", {"case_id": state.case_id},
                 [h.rule_id for h in state.rule_hits], case_id=state.case_id)
    return state


def stage_stress(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    state.stress = run_stress_test(state.case_id, state.contract, state.lease_items)
    rt.audit.log("stress", {"case_id": state.case_id},
                 {"breach": [s.scenario for s in state.stress.scenarios if s.breach]},
                 case_id=state.case_id)
    return state


def stage_alerts(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    state.utilization_series = rt.tools.call("telemetry_feed", state.case_id, case_id=state.case_id)
    state.alerts = detect_alerts(state.case_id, state.utilization_series)
    # 合并模拟外部负面信号（模拟接口）
    parties = [state.contract.lessee.name]
    if state.contract.vendor:
        parties.append(state.contract.vendor.name)
    signals = rt.tools.call("external_signals", parties, case_id=state.case_id)
    if signals:
        from .schemas import UtilizationAlert

        state.alerts.append(UtilizationAlert(
            case_id=state.case_id, alert_type="rent_divergence", level="orange",
            window="external", metric_value=float(len(signals)),
            detail="外部负面信号（模拟接口）: " + "；".join(signals),
        ))
    rt.audit.log("alerts", {"case_id": state.case_id},
                 [a.alert_type + "/" + a.level for a in state.alerts], case_id=state.case_id)
    return state


def stage_score(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    state.risk_score = score_case(
        state.case_id, state.verification, state.rule_hits, state.stress, state.alerts
    )
    rt.audit.log("scoring", {"case_id": state.case_id},
                 state.risk_score.model_dump(), case_id=state.case_id)
    return state


def stage_report(state: PipelineState, rt: PipelineRuntime) -> PipelineState:
    out_dir = rt.out_dir or (rt.base_dir / state.case_id / "report")
    md_path, html_path, _md = build_report(state, out_dir)
    audit_jsonl = out_dir / f"{state.case_id}_audit.jsonl"
    rt.audit.export_case_jsonl(state.case_id, audit_jsonl)
    zip_path = export_audit_package(
        state, rt.base_dir, out_dir / f"{state.case_id}_audit_package.zip",
        audit_jsonl=audit_jsonl, report_paths=(md_path, html_path),
    )
    state.report_path = str(md_path)
    state.report_html_path = str(html_path)
    state.audit_zip_path = str(zip_path)
    rt.audit.log("report", {"case_id": state.case_id},
                 {"md": str(md_path), "zip": str(zip_path)}, case_id=state.case_id)
    return state


_STAGES = [
    ("guardrail_in", stage_guardrail_in),
    ("parse", stage_parse),
    ("validate", stage_validate),
    ("verify", stage_verify),
    ("rules", stage_rules),
    ("stress", stage_stress),
    ("alerts", stage_alerts),
    ("score", stage_score),
    ("report", stage_report),
]


def run_pipeline(
    case_id: str,
    files: dict[str, str],
    run_mode: str = "mock",
    *,
    base_dir: str | Path = ".",
    labels_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    settings: LLMSettings | None = None,
    guard_llm: bool = True,
) -> PipelineState:
    """顺序执行全部环节；结构化异常不中断主链，记入 state.errors（SPEC 5.2）。

    guard_llm=False 时关闭护栏的 LLM 二次判定（规则库检测仍生效），
    用于 live 模式批量评测控制时耗；交互场景保持默认开启。
    """
    base = Path(base_dir)
    s = settings or load_settings()
    if run_mode == "mock":
        s = LLMSettings(api_key=None, base_url=s.base_url, model=s.model)
    audit = SqliteAuditStore(audit_path or (base / "audit.db"), run_mode)
    rt = PipelineRuntime(settings=s, run_mode=run_mode, base_dir=base, audit=audit,
                         tools=build_default_registry(audit),
                         out_dir=Path(out_dir) if out_dir else None,
                         guard_llm=guard_llm)
    lp = Path(labels_path) if labels_path else base / "labels.jsonl"
    rt.item_index, rt.serial_index, rt.all_cases = load_dataset_context(lp)

    state = PipelineState(case_id=case_id, run_mode=run_mode, files=files)
    for name, stage in _STAGES:
        t0 = time.perf_counter()
        try:
            state = stage(state, rt)
        except GuardrailViolation as e:
            state.errors.append(e.to_log())
            audit.log(name, {"case_id": case_id}, {"error": e.to_log()},
                      case_id=case_id, event_type="guardrail")
            state.stage_timings[name] = round(time.perf_counter() - t0, 3)
            break  # 护栏命中：终止处理
        except JinDunError as e:
            state.errors.append(e.to_log())
            audit.log(name, {"case_id": case_id}, {"error": e.to_log()}, case_id=case_id)
            state.stage_timings[name] = round(time.perf_counter() - t0, 3)
            if name in ("parse",):  # 解析失败无后续
                break
        except Exception as e:  # 兜底：非结构化异常同样记录
            state.errors.append(f"UNEXPECTED: {type(e).__name__}: {e}")
            audit.log(name, {"case_id": case_id}, {"error": str(e)}, case_id=case_id)
            state.stage_timings[name] = round(time.perf_counter() - t0, 3)
            break
        else:
            state.stage_timings[name] = round(time.perf_counter() - t0, 3)
    chain_ok = audit.verify_chain()
    audit.log("pipeline_done", {"case_id": case_id},
              {"errors": state.errors, "chain_ok": chain_ok,
               "score": state.risk_score.total if state.risk_score else None},
              case_id=case_id)
    audit.close()
    return state


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="src.pipeline", description="单案件端到端 pipeline")
    ap.add_argument("--case", type=Path, required=True, help="案件目录，如 data/cases/case_0001")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--mock", action="store_true", help="mock 模式（不调 LLM）")
    mode.add_argument("--live", action="store_true", help="live 模式（需 LLM_API_KEY）")
    args = ap.parse_args(argv)

    case_dir = args.case
    case_id = case_dir.name
    base = case_dir.parent
    files = {
        "contract": f"{case_id}/contract.pdf",
        "invoice": f"{case_id}/invoice.pdf",
        "lease_items": f"{case_id}/lease_items.pdf",
    }
    run_mode = "live" if args.live else "mock"
    state = run_pipeline(case_id, files, run_mode, base_dir=base)

    print(f"===== Pipeline 端到端结果（{case_id}, {run_mode}）=====")
    if state.errors:
        print("异常/降级记录:")
        for e in state.errors:
            print(f"  - {e}")
    if state.risk_score:
        rs = state.risk_score
        grade_cn = {"pass": "建议通过", "review": "待人工复核（强制，不得自动放行）",
                    "reject": "建议拒绝"}[rs.grade]
        print(f"风险评分: {rs.total:.1f}/100 → {grade_cn}")
        for c in rs.components:
            print(f"  {c.name:<13} 权重 {c.weight:.2f} 原始 {c.raw:.2f} 贡献 {c.contribution:.1f}")
        print("理由: " + "；".join(rs.reasons))
    print(f"规则命中: {[h.rule_id for h in state.rule_hits] or '无'}")
    print(f"预警: {[a.alert_type + '/' + a.level for a in state.alerts] or '无'}")
    if state.verification:
        print(f"核验: 通过 {state.verification.passed_count} / 未通过 {state.verification.failed_count}")
    review_flags = [f for f in state.validation_flags if f.severity == "review"]
    if review_flags:
        print("字段级交叉校验（转人审）: " + "；".join(
            f"{f.field_name}/{f.reason_code}" for f in review_flags))
    print(f"报告: {state.report_path}")
    print(f"      {state.report_html_path}")
    print(f"审计包: {state.audit_zip_path}")


if __name__ == "__main__":
    main()
