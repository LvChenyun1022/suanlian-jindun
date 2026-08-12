"""无文本层（扫描件）检测与优雅降级的单元测试（通用能力，不依赖 data/external）。"""
from __future__ import annotations

import pymupdf
import pytest

from config.settings import LLMSettings
from src.errors import ParseError
from src.parsing.parser import parse_document
from src.parsing.reader import PdfTextReader
from src.schemas import DocType

MOCK = LLMSettings(api_key=None, base_url="", model="mock")


def _make_text_pdf(path) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "合同编号：HT-2025-0001\n卖方（出卖人）：测试有限公司")
    doc.save(path)
    doc.close()


def _make_scanned_pdf(path) -> None:
    """图片型 PDF：一页仅含一幅位图、无任何文本（模拟扫描件）。"""
    from PIL import Image

    img = Image.new("RGB", (400, 200), "white")
    png = path.with_suffix(".png")
    img.save(png)
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=200)
    page.insert_image(page.rect, filename=str(png))
    doc.save(path)
    doc.close()


def test_text_pdf_has_text_layer(tmp_path):
    p = tmp_path / "text.pdf"
    _make_text_pdf(p)
    r = PdfTextReader(p)
    assert r.has_text_layer is True
    assert r.text_layer_page_ratio == 1.0
    assert r.is_likely_scanned is False
    r.close()


def test_scanned_pdf_detected(tmp_path):
    p = tmp_path / "scan.pdf"
    _make_scanned_pdf(p)
    r = PdfTextReader(p)
    assert r.has_text_layer is False
    assert r.text_layer_page_ratio == 0.0
    assert r.is_likely_scanned is True  # 无文本但有图像页
    r.close()


def test_parse_document_scanned_raises_structured_error(tmp_path):
    p = tmp_path / "scan.pdf"
    _make_scanned_pdf(p)
    with pytest.raises(ParseError) as exc:
        parse_document(p, DocType.CONTRACT, MOCK)
    assert exc.value.code == "PARSE_NO_TEXT_LAYER"
    assert "OCR" in str(exc.value)
