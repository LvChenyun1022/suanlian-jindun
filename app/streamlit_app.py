"""算链金盾（suanlian-jindun）Streamlit Demo（SPEC M11）。

仅本地 localhost 运行（见 .streamlit/config.toml），不做任何公网部署。
启动：
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.audit.sqlite_store import SqliteAuditStore  # noqa: E402
from src.guardrails import AI_OUTPUT_BANNER  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.report.report import render_html  # noqa: E402
from src.schemas import PipelineState  # noqa: E402

CASES_ROOT = Path(os.environ.get("JINDUN_CASES_ROOT", ROOT / "data" / "cases"))
UPLOAD_ROOT = ROOT / "data" / "uploads"
DOC_LABELS = {"contract": "购销合同", "invoice": "增值税发票", "lease_items": "租赁物清单"}

st.set_page_config(page_title="算链金盾 · 算力融资租赁风控 Demo", layout="wide")


# ---------------- 侧边栏：案件选择与运行 ----------------

def sidebar() -> None:
    st.sidebar.title("案件选择")
    source = st.sidebar.radio("案件来源", ["合成库选择", "上传 PDF 三件套"], key="source")
    mock = st.sidebar.toggle("使用 mock LLM（无 Key 也能演示）", value=True, key="mock_toggle")

    case_id = files = base_dir = None
    if source == "合成库选择":
        cases = sorted(d.name for d in CASES_ROOT.iterdir()
                       if d.is_dir() and d.name.startswith("case_")) if CASES_ROOT.exists() else []
        if not cases:
            st.sidebar.error("未找到 data/cases，请先运行 python -m src.datagen.generate")
            return
        case_id = st.sidebar.selectbox("案件", cases, key="case_select")
        base_dir = CASES_ROOT
        files = {dt: f"{case_id}/{dt}.pdf" for dt in DOC_LABELS}
    else:
        uploads = {}
        for dt, label in DOC_LABELS.items():
            uploads[dt] = st.sidebar.file_uploader(f"{label} PDF", type=["pdf"], key=f"up_{dt}")
        if all(uploads.values()):
            case_id = "case_upload"
            base_dir = UPLOAD_ROOT
            case_dir = UPLOAD_ROOT / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            files = {}
            for dt, uf in uploads.items():
                (case_dir / f"{dt}.pdf").write_bytes(uf.getvalue())
                files[dt] = f"{case_id}/{dt}.pdf"
            st.sidebar.caption("上传文件的文本将经过入口护栏（注入/敏感数据检测）。")

    ready = case_id is not None
    if st.sidebar.button("运行 Pipeline", key="run_btn", type="primary", disabled=not ready):
        run_mode = "mock" if mock else "live"
        with st.spinner(f"正在以 {run_mode} 模式运行全链路..."):
            state = run_pipeline(case_id, files, run_mode, base_dir=base_dir)
        st.session_state["state"] = state
        st.session_state["base_dir"] = str(base_dir)
        st.session_state.pop("manual_decision", None)


# ---------------- 结果面板 ----------------

def panel_stages(state: PipelineState) -> None:
    st.subheader("① 环节状态与耗时")
    done = set(state.stage_timings)
    all_stages = ["guardrail_in", "parse", "verify", "rules", "stress", "alerts", "score", "report"]
    df = pd.DataFrame([
        {"环节": s, "状态": "✅ 完成" if s in done else "— 未执行",
         "耗时(s)": state.stage_timings.get(s, "")}
        for s in all_stages
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    if state.errors:
        st.error("异常/降级记录：" + "；".join(state.errors))


def panel_verification(state: PipelineState) -> None:
    st.subheader("② 三单核验")
    v = state.verification
    if not v:
        st.info("无核验结果")
        return
    df = pd.DataFrame([
        {"核验项": c.check_name, "结论": "✅ pass" if c.passed else "❌ fail", "说明": c.detail}
        for c in v.checks
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    for c in v.checks:
        if not c.passed:
            with st.expander(f"证据：{c.check_name}"):
                _evidence_table(c.evidences)


def _evidence_table(evidences) -> None:
    if not evidences:
        st.caption("（无字段级证据）")
        return
    df = pd.DataFrame([
        {"字段": e.field_name, "单据": e.doc_type.value, "页码": e.page,
         "坐标": f"({e.bbox.x0:.0f},{e.bbox.y0:.0f},{e.bbox.x1:.0f},{e.bbox.y1:.0f})" if e.bbox else "-",
         "原文片段": e.excerpt}
        for e in evidences
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def panel_rules(state: PipelineState) -> None:
    st.subheader("③ 77号文规则命中")
    if not state.rule_hits:
        st.success("无规则命中")
        return
    df = pd.DataFrame([
        {"规则编号": h.rule_id, "条款引用": h.clause_ref, "严重度": h.severity,
         "说明": h.detail or h.description}
        for h in state.rule_hits
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    for h in state.rule_hits:
        with st.expander(f"证据：{h.rule_id}（{h.clause_ref}）"):
            _evidence_table(h.evidences)


def panel_stress(state: PipelineState) -> None:
    st.subheader("④ 残值曲线与压力测试")
    if not state.stress:
        st.info("无压力测试结果")
        return
    s = state.stress
    st.line_chart(pd.DataFrame({"残值率": s.depreciation_curve}))
    df = pd.DataFrame([
        {"情景": sc.scenario, "残值率": sc.residual_value_ratio, "LTV": sc.ltv,
         "DSCR": sc.dscr, "突破阈值": "是" if sc.breach else "否", "说明": sc.detail}
        for sc in s.scenarios
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"GPU 型号：{s.gpu_model} ｜ 回本周期：{s.payback_months} 个月 ｜ 参数为公开案例校准假设值")


def panel_alerts(state: PipelineState) -> None:
    st.subheader("⑤ 利用率预警")
    if state.utilization_series:
        st.line_chart(pd.DataFrame({"GPU 利用率": state.utilization_series}))
    if not state.alerts:
        st.success("绿色：无预警")
        return
    icon = {"red": "🔴", "orange": "🟠", "yellow": "🟡"}
    df = pd.DataFrame([
        {"等级": f"{icon.get(a.level, '')} {a.level}", "类型": a.alert_type,
         "窗口": a.window, "指标": a.metric_value, "说明": a.detail}
        for a in state.alerts
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def panel_score(state: PipelineState) -> None:
    st.subheader("⑥ 风险评分与人审路由")
    rs = state.risk_score
    if not rs:
        st.info("无评分结果")
        return
    col1, col2 = st.columns([1, 2])
    col1.metric("风险评分（越高越危险）", f"{rs.total:.1f} / 100")
    comp = pd.DataFrame({"贡献": [c.contribution for c in rs.components]},
                        index=[c.name for c in rs.components])
    col2.bar_chart(comp)

    if rs.grade == "pass":
        st.success("路由结论：<60，建议通过。")
    elif rs.grade == "review":
        st.warning("路由结论：60–90，**强制人工复核**（不得自动放行）。")
    else:
        st.error("路由结论：>90，建议拒绝。")
    st.caption("理由：" + "；".join(rs.reasons))

    st.markdown("**人工复核操作**（写入审计日志）")
    decision = st.session_state.get("manual_decision")
    if decision:
        st.info(f"已记录人工复核结论：**{decision}**（见审计时间线 manual_op 事件）")
    else:
        b1, b2 = st.columns(2)
        approve = b1.button("人工复核：通过", key="review_approve")
        reject = b2.button("人工复核：拒绝", key="review_reject")
        if rs.grade != "review":
            st.caption("本案非强制人审区间，按钮为可选操作；操作同样留痕。")
        if approve or reject:
            decision_text = "通过" if approve else "拒绝"
            store = SqliteAuditStore(Path(st.session_state["base_dir"]) / "audit.db",
                                     state.run_mode)
            store.log("manual_review", {"case_id": state.case_id},
                      {"decision": decision_text},
                      case_id=state.case_id, event_type="manual_op",
                      detail=f"人工复核结论: {decision_text}")
            store.close()
            st.session_state["manual_decision"] = decision_text
            st.rerun()


def panel_report(state: PipelineState) -> None:
    st.subheader("⑦ 证据链报告与审计")
    if not state.report_path:
        st.info("未生成报告")
        return
    md_text = Path(state.report_path).read_text(encoding="utf-8")
    tab_md, tab_html, tab_ev = st.tabs(["报告预览 (Markdown)", "报告预览 (HTML)", "证据明细"])
    with tab_md:
        st.markdown(md_text)
    with tab_html:
        st.components.v1.html(render_html(md_text), height=600, scrolling=True)
    with tab_ev:
        _evidence_table(state.evidences)

    col1, col2 = st.columns(2)
    if state.audit_zip_path and Path(state.audit_zip_path).exists():
        col1.download_button(
            "下载审计包 zip",
            data=Path(state.audit_zip_path).read_bytes(),
            file_name=Path(state.audit_zip_path).name,
            mime="application/zip",
            key="zip_dl",
        )
    with col2.expander("审计日志时间线"):
        store = SqliteAuditStore(Path(st.session_state["base_dir"]) / "audit.db", state.run_mode)
        events = store.list_case_events(state.case_id)
        chain_ok = store.verify_chain()
        store.close()
        st.caption(f"哈希链校验：{'✅ OK' if chain_ok else '❌ FAIL'} ｜ 事件数：{len(events)}")
        if events:
            df = pd.DataFrame(events)[["seq", "ts", "stage", "event_type", "detail"]]
            st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------- 主流程 ----------------

def main() -> None:
    st.title("算链金盾 · 算力融资租赁智能风控 Demo")
    st.caption(AI_OUTPUT_BANNER)
    sidebar()
    state: PipelineState | None = st.session_state.get("state")
    if state is None:
        st.info("请在左侧选择案件（或上传三件套）并点击「运行 Pipeline」。")
    else:
        st.markdown(f"### 案件 {state.case_id}（{state.run_mode} 模式）")
        panel_stages(state)
        st.divider()
        col_l, col_r = st.columns(2)
        with col_l:
            panel_verification(state)
            panel_rules(state)
        with col_r:
            panel_stress(state)
            panel_alerts(state)
        st.divider()
        panel_score(state)
        st.divider()
        panel_report(state)

    st.divider()
    st.caption("本系统输出为 AI 辅助意见，不构成授信或投资建议；演示数据均为合成数据。")


main()
