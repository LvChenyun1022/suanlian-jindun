"""证据链报告生成与审计包导出。"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ..guardrails import label_ai_output
from ..schemas import FieldEvidence, PipelineState


def _evidence_row(ev: FieldEvidence) -> str:
    bbox = f"({ev.bbox.x0:.0f},{ev.bbox.y0:.0f},{ev.bbox.x1:.0f},{ev.bbox.y1:.0f})" if ev.bbox else "-"
    excerpt = ev.excerpt.replace("|", "\\|")
    if len(excerpt) > 60:
        excerpt = excerpt[:57] + "..."
    return f"| {ev.field_name} | {ev.doc_type.value} | {ev.page} | {bbox} | {excerpt} |"


def render_markdown(state: PipelineState) -> str:
    """渲染证据链报告 Markdown（每条结论回溯字段级证据）。"""
    L: list[str] = []
    L.append(f"# 证据链报告 — {state.case_id}")
    L.append("")
    L.append(f"> 生成时间：{datetime.now(timezone.utc).isoformat()} ｜ 运行模式：{state.run_mode}")
    L.append("> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。")
    L.append("")

    if state.risk_score:
        rs = state.risk_score
        grade_cn = {"pass": "建议通过", "review": "待人工复核（强制）", "reject": "建议拒绝"}[rs.grade]
        L.append(f"## 风险评分：{rs.total:.1f} / 100 → **{grade_cn}**")
        L.append("")
        L.append("| 分项 | 权重 | 原始值 | 贡献 |")
        L.append("|---|---|---|---|")
        for c in rs.components:
            L.append(f"| {c.name} | {c.weight:.2f} | {c.raw:.2f} | {c.contribution:.1f} |")
        L.append("")
        L.append("**路由理由**：" + "；".join(rs.reasons))
        L.append("")

    if state.verification:
        v = state.verification
        L.append(f"## 三单核验（通过 {v.passed_count} / 未通过 {v.failed_count}）")
        L.append("")
        L.append("| 核验项 | 结论 | 说明 |")
        L.append("|---|---|---|")
        for chk in v.checks:
            L.append(f"| {chk.check_name} | {'✅ 通过' if chk.passed else '❌ 未通过'} | {chk.detail} |")
        L.append("")

    if state.rule_hits:
        L.append("## 规则命中")
        L.append("")
        L.append("| 规则编号 | 条款引用 | 严重度 | 说明 |")
        L.append("|---|---|---|---|")
        for h in state.rule_hits:
            L.append(f"| {h.rule_id} | {h.clause_ref} | {h.severity} | {h.detail or h.description} |")
        L.append("")
    else:
        L.append("## 规则命中\n\n无。\n")

    if state.stress:
        L.append(f"## 残值与现金流压力测试（{state.stress.gpu_model}）")
        L.append("")
        L.append("| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |")
        L.append("|---|---|---|---|---|---|")
        for s in state.stress.scenarios:
            L.append(f"| {s.scenario} | {s.residual_value_ratio:.2f} | {s.ltv:.2f} | {s.dscr:.2f} "
                     f"| {'是' if s.breach else '否'} | {s.detail} |")
        if state.stress.payback_months:
            L.append(f"\n回本周期：{state.stress.payback_months} 个月。")
        L.append("")

    if state.alerts:
        L.append("## 利用率预警")
        L.append("")
        L.append("| 类型 | 级别 | 窗口 | 指标 | 说明 |")
        L.append("|---|---|---|---|---|")
        for a in state.alerts:
            L.append(f"| {a.alert_type} | {a.level} | {a.window} | {a.metric_value:.2%} | {a.detail} |")
        L.append("")

    # 证据链明细
    L.append("## 证据链明细（字段级）")
    L.append("")
    L.append("| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |")
    L.append("|---|---|---|---|---|")
    for ev in state.evidences:
        L.append(_evidence_row(ev))
    L.append("")
    if state.errors:
        L.append("## 降级/异常记录")
        for e in state.errors:
            L.append(f"- {e}")
        L.append("")
    return "\n".join(L)


def render_html(md_text: str) -> str:
    """Markdown -> 自包含 HTML（内联样式，供预览/下载）。"""
    from markdown_it import MarkdownIt

    body = MarkdownIt("commonmark", {"html": False}).enable("table").render(md_text)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>证据链报告</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; max-width: 960px; margin: 24px auto; padding: 0 16px; color: #222; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #ccc; padding: 4px 8px; text-align: left; }}
th {{ background: #f2f4f8; }}
h1, h2 {{ border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; }}
blockquote {{ color: #666; border-left: 4px solid #ddd; margin: 0; padding-left: 12px; }}
</style></head><body>
{body}
</body></html>"""


def build_report(state: PipelineState, out_dir: str | Path) -> tuple[Path, Path, str]:
    """生成 Markdown + HTML 报告。返回 (md_path, html_path, md_text) 供前端预览。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_text = label_ai_output(render_markdown(state))
    md_path = out / f"{state.case_id}_report.md"
    html_path = out / f"{state.case_id}_report.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(render_html(md_text), encoding="utf-8")
    return md_path, html_path, md_text


def export_audit_package(
    state: PipelineState,
    base_dir: str | Path,
    zip_path: str | Path,
    audit_jsonl: str | Path | None = None,
    report_paths: tuple[Path, Path] | None = None,
) -> Path:
    """导出审计包 zip：输入文件清单 + 各环节输出 JSON + 审计日志 + 报告文件。"""
    base = Path(base_dir)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    outputs = {
        "outputs/contract.json": state.contract.model_dump(mode="json") if state.contract else None,
        "outputs/invoice.json": state.invoice.model_dump(mode="json") if state.invoice else None,
        "outputs/lease_items.json": state.lease_items.model_dump(mode="json") if state.lease_items else None,
        "outputs/verification.json": state.verification.model_dump(mode="json") if state.verification else None,
        "outputs/rule_hits.json": [h.model_dump(mode="json") for h in state.rule_hits],
        "outputs/stress.json": state.stress.model_dump(mode="json") if state.stress else None,
        "outputs/alerts.json": [a.model_dump(mode="json") for a in state.alerts],
        "outputs/risk_score.json": state.risk_score.model_dump(mode="json") if state.risk_score else None,
        "outputs/pipeline_errors.json": state.errors,
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 输入文件清单（含原件）
        manifest = []
        for doc_type, rel in state.files.items():
            src = base / rel
            manifest.append({"doc_type": doc_type, "path": rel, "exists": src.exists()})
            if src.exists():
                zf.write(src, f"inputs/{doc_type}.pdf")
        zf.writestr("inputs/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for name, payload in outputs.items():
            zf.writestr(name, json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        if audit_jsonl and Path(audit_jsonl).exists():
            zf.write(audit_jsonl, "audit/audit_log.jsonl")
        if report_paths:
            for p in report_paths:
                if Path(p).exists():
                    zf.write(p, f"report/{Path(p).name}")
    return zip_path
