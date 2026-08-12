"""PDF 文本读取：PyMuPDF 优先，pdfplumber 备用；按行检索并给出证据坐标。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..schemas import BBox


@dataclass
class RawHit:
    """一次标签命中：值 + 证据定位。"""

    value: str
    page: int            # 1-based
    excerpt: str         # 整行原文
    bbox: BBox | None


class PdfTextReader:
    """按"标签：值"行检索字段。坐标统一转为 PDF 用户空间（左下原点）。

    通用健壮性（外部效度 mini-test 阶段新增）：记录逐页文本/图像统计，
    可识别"无文本层"的扫描件/图片型 PDF（has_text_layer / is_likely_scanned），
    供解析层给出显式降级信号而不是静默空抽取。
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.backend = "pymupdf"
        self._doc = None
        self._page_heights: list[float] = []
        self.pages_text: list[list[str]] = []
        self.page_char_counts: list[int] = []   # 逐页去空白字符数
        self.page_image_counts: list[int] = []  # 逐页嵌入图像数（pymupdf 可得时）
        self._read()

    def _read(self) -> None:
        try:
            import pymupdf

            doc = pymupdf.open(self.path)
            pages = [page.get_text().splitlines() for page in doc]
            self.page_char_counts = [len("".join(lines).strip()) for lines in pages]
            self.page_image_counts = [len(page.get_images()) for page in doc]
            if any(line.strip() for page in pages for line in page):
                self._doc = doc
                self._page_heights = [page.rect.height for page in doc]
                self.pages_text = pages
                self.backend = "pymupdf"
                return
            doc.close()  # 无文本层：落入 pdfplumber 备用（统计已保留）
        except Exception:
            pass
        # 备用：pdfplumber（无坐标检索，bbox=None）
        import pdfplumber

        with pdfplumber.open(self.path) as pdf:
            self.pages_text = [(p.extract_text() or "").splitlines() for p in pdf.pages]
        if not self.page_char_counts:
            self.page_char_counts = [len("".join(lines).strip()) for lines in self.pages_text]
        self.backend = "pdfplumber"

    @property
    def page_count(self) -> int:
        return len(self.pages_text)

    @property
    def has_text_layer(self) -> bool:
        """是否存在"有意义文本"的页（>20 字符，排除空白页/纯图页）。"""
        return any(c > 20 for c in self.page_char_counts)

    @property
    def text_layer_page_ratio(self) -> float:
        """有意义文本页占比（0–1）；无页时返回 0。"""
        if not self.page_char_counts:
            return 0.0
        return sum(1 for c in self.page_char_counts if c > 20) / len(self.page_char_counts)

    @property
    def is_likely_scanned(self) -> bool:
        """无有意义文本层但含嵌入图像页 → 疑似扫描件/图片型 PDF。"""
        return not self.has_text_layer and any(self.page_image_counts)

    def full_text(self) -> str:
        return "\n".join(line for page in self.pages_text for line in page)

    def _search_bbox(self, page_no: int, needle: str) -> BBox | None:
        """在指定页检索值文本的坐标（转左下原点）。pdfplumber 后端返回 None。"""
        if self._doc is None or not needle:
            return None
        rects = self._doc[page_no - 1].search_for(needle)
        if not rects:
            return None
        r = rects[0]
        h = self._page_heights[page_no - 1]
        return BBox(x0=r.x0, y0=h - r.y1, x1=r.x1, y1=h - r.y0)

    def find(self, label: str) -> RawHit | None:
        """精确匹配行首"标签：值"（全行匹配，取首个命中）。"""
        pattern = re.compile(rf"^\s*{re.escape(label)}：\s*(?P<value>.+?)\s*$")
        for pno, lines in enumerate(self.pages_text, start=1):
            for line in lines:
                m = pattern.match(line)
                if m:
                    value = m.group("value")
                    return RawHit(value, pno, line.strip(), self._search_bbox(pno, value))
        return None

    def find_indexed(self, label_prefix: str) -> dict[int, RawHit]:
        """匹配"标签前缀（k）：值"，返回 {k-1: RawHit}（k 为 1-based 序号）。"""
        pattern = re.compile(rf"^\s*{re.escape(label_prefix)}（(?P<idx>\d+)）：\s*(?P<value>.+?)\s*$")
        hits: dict[int, RawHit] = {}
        for pno, lines in enumerate(self.pages_text, start=1):
            for line in lines:
                m = pattern.match(line)
                if m:
                    value = m.group("value")
                    hits[int(m.group("idx")) - 1] = RawHit(
                        value, pno, line.strip(), self._search_bbox(pno, value)
                    )
        return hits

    def locate_value(self, value: str) -> RawHit | None:
        """按值文本定位（LLM 补抽结果的证据回填用）：返回包含该值的首行。"""
        for pno, lines in enumerate(self.pages_text, start=1):
            for line in lines:
                if value and value in line:
                    return RawHit(value, pno, line.strip(), self._search_bbox(pno, value))
        return None

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None
