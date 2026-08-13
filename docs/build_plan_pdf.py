"""参赛项目书 Markdown → PDF（reportlab + CID 中文字体，无外部依赖）。

用法：python docs/build_plan_pdf.py [in.md] [out.pdf]
支持：#/##/### 标题、段落、- 列表、| 管道表格 |、``` 代码块、> 引用、**粗体**、`行内码`。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"

S = {
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=20, leading=26, spaceBefore=10, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName=FONT, fontSize=15, leading=20, spaceBefore=10, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName=FONT, fontSize=12.5, leading=17, spaceBefore=8, spaceAfter=4),
    "p": ParagraphStyle("p", fontName=FONT, fontSize=10.5, leading=15.5, spaceAfter=4),
    "bullet": ParagraphStyle("b", fontName=FONT, fontSize=10.5, leading=15.5, leftIndent=14, spaceAfter=2),
    "quote": ParagraphStyle("q", fontName=FONT, fontSize=9.5, leading=14, leftIndent=10,
                            textColor="#444444", spaceAfter=4),
    "code": ParagraphStyle("c", fontName="Courier", fontSize=8.5, leading=11.5,
                           leftIndent=8, backColor="#f4f4f4", spaceAfter=4),
    "cell": ParagraphStyle("tc", fontName=FONT, fontSize=9, leading=12.5),
    "cellh": ParagraphStyle("th", fontName=FONT, fontSize=9, leading=12.5, textColor="#ffffff"),
}


def inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9">\1</font>', text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # 链接只留文字
    return text


def render(md: str) -> list:
    flow: list = []
    lines = md.splitlines()
    i = 0
    para: list[str] = []

    def flush_para() -> None:
        if para:
            flow.append(Paragraph(inline(" ".join(para)), S["p"]))
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            flush_para()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i].rstrip() or " ")
                i += 1
            for cl in code:
                flow.append(Paragraph(cl.replace(" ", "&nbsp;"), S["code"]))
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-|]+\|$", lines[i + 1].strip()):
            flush_para()
            rows: list[list] = []
            header = [c.strip() for c in line.strip("|").split("|")]
            rows.append([Paragraph(inline(c), S["cellh"]) for c in header])
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                while len(cells) < len(header):
                    cells.append("")
                rows.append([Paragraph(inline(c), S["cell"]) for c in cells[: len(header)]])
                i += 1
            i -= 1
            ncol = len(header)
            width = 180 * mm
            tbl = Table(rows, colWidths=[width / ncol] * ncol, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), "#33507a"),
                ("GRID", (0, 0), (-1, -1), 0.4, "#999999"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), ["#ffffff", "#f2f5fa"]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            flow.append(tbl)
            flow.append(Spacer(1, 4))
        elif line.startswith("### "):
            flush_para(); flow.append(Paragraph(inline(line[4:]), S["h3"]))
        elif line.startswith("## "):
            flush_para(); flow.append(Paragraph(inline(line[3:]), S["h2"]))
        elif line.startswith("# "):
            flush_para(); flow.append(Paragraph(inline(line[2:]), S["h1"]))
        elif line.startswith("> "):
            flush_para(); flow.append(Paragraph(inline(line[2:]), S["quote"]))
        elif re.match(r"^[-*] ", line):
            flush_para(); flow.append(Paragraph("• " + inline(line[2:]), S["bullet"]))
        elif re.match(r"^\d+\. ", line):
            flush_para(); flow.append(Paragraph(inline(line), S["bullet"]))
        elif line.strip() == "---":
            flush_para(); flow.append(Spacer(1, 6))
        elif not line.strip():
            flush_para()
        else:
            para.append(line.strip())
        i += 1
    flush_para()
    return flow


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/plan_draft.md")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs/plan_final.pdf")
    doc = SimpleDocTemplate(
        str(dst), pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="算链金盾 · 参赛项目书",
    )
    doc.build(render(src.read_text(encoding="utf-8")))
    print(f"written: {dst} ({dst.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
