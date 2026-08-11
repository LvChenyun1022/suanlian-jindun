"""reportlab PDF 写入器：注册 CID 中文字体并逐字段记录页码与近似坐标。

坐标系：PDF 用户空间，左下原点，单位 pt（与 SPEC BBox 一致）。
输出为数字文本 PDF（非扫描件），PyMuPDF 可直接提取文本。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FONT_NAME = "STSong-Light"
_registered = False


def ensure_cid_font() -> None:
    """注册 CID 中文字体（幂等）。"""
    global _registered
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
        _registered = True


@dataclass
class FieldPos:
    """字段在 PDF 中的位置（近似坐标）。"""

    page: int  # 1-based 页码
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    excerpt: str  # 整行原文（标签：值）


class SimplePdfWriter:
    """按行渲染"标签：值"字段，记录每个字段的页码与 bbox。"""

    MARGIN_X = 56.0
    RIGHT_MARGIN = 40.0
    TOP_Y = A4[1] - 56.0
    BOTTOM_Y = 56.0
    LINE_H = 18.0
    FONT_SIZE = 12
    MIN_FONT_SIZE = 8

    def _fit_size(self, text: str, indent: float = 0.0) -> float:
        """长行自动缩小字号，确保整行不超出页面右边界（避免提取时丢字）。"""
        max_w = A4[0] - self.MARGIN_X - indent - self.RIGHT_MARGIN
        w = pdfmetrics.stringWidth(text, FONT_NAME, self.FONT_SIZE)
        if w <= max_w:
            return self.FONT_SIZE
        return max(self.MIN_FONT_SIZE, int(self.FONT_SIZE * max_w / w))

    def __init__(self, path: str | Path, title: str) -> None:
        ensure_cid_font()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._c = canvas.Canvas(str(self.path), pagesize=A4)
        self.page = 1
        self.y = self.TOP_Y
        self.positions: dict[str, FieldPos] = {}
        self._draw_title(title)

    def _draw_title(self, title: str) -> None:
        size = 16
        self._c.setFont(FONT_NAME, size)
        w = pdfmetrics.stringWidth(title, FONT_NAME, size)
        self._c.drawString((A4[0] - w) / 2, self.y, title)
        self.y -= 32

    def _check_page(self) -> None:
        if self.y < self.BOTTOM_Y:
            self._c.showPage()
            self.page += 1
            self.y = self.TOP_Y

    def line(self, text: str, indent: float = 0.0) -> None:
        """渲染一行普通文本（不作为字段记录）。"""
        self._check_page()
        self._c.setFont(FONT_NAME, self._fit_size(text, indent))
        self._c.drawString(self.MARGIN_X + indent, self.y, text)
        self.y -= self.LINE_H

    def field_line(self, key: str, label: str, value: str, indent: float = 0.0) -> None:
        """渲染"标签：值"并记录字段位置；value 的 bbox 仅覆盖值部分。"""
        self._check_page()
        text = f"{label}：{value}"
        size = self._fit_size(text, indent)
        x = self.MARGIN_X + indent
        self._c.setFont(FONT_NAME, size)
        self._c.drawString(x, self.y, text)
        label_w = pdfmetrics.stringWidth(f"{label}：", FONT_NAME, size)
        value_w = pdfmetrics.stringWidth(str(value), FONT_NAME, size)
        self.positions[key] = FieldPos(
            page=self.page,
            bbox=(x + label_w, self.y - 3.0, x + label_w + value_w, self.y + size),
            excerpt=text,
        )
        self.y -= self.LINE_H

    def save(self) -> None:
        self._c.save()
