"""Streamlit 原始单据预览的回归测试。"""
from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pymupdf
import pytest
from PIL import Image

from app.streamlit_app import _evidence_boxes, _render_doc_image
from src.schemas import BBox, DocType, FieldEvidence


def _evidence(doc_type: DocType = DocType.CONTRACT) -> FieldEvidence:
    return FieldEvidence(
        field_name="contract_no",
        page=1,
        excerpt="合同编号：HT-001",
        bbox=BBox(x0=40, y0=80, x1=160, y1=120),
        doc_type=doc_type,
        source_file=f"case_0001/{doc_type.value}.pdf",
    )


def test_evidence_boxes_groups_and_deduplicates() -> None:
    contract = _evidence()
    invoice = _evidence(DocType.INVOICE)
    state = SimpleNamespace(
        verification=SimpleNamespace(
            checks=[SimpleNamespace(evidences=[contract, invoice])]
        ),
        rule_hits=[SimpleNamespace(evidences=[contract])],
    )

    boxes = _evidence_boxes(state)

    assert list(boxes) == ["contract", "invoice", "lease_items"]
    assert boxes["contract"] == [contract]
    assert boxes["invoice"] == [invoice]
    assert boxes["lease_items"] == []


def test_render_doc_image_supports_pages_and_draws_evidence(tmp_path) -> None:
    pdf_path = tmp_path / "contract.pdf"
    with pymupdf.open() as doc:
        first = doc.new_page(width=200, height=200)
        first.insert_text((40, 100), "HT-001")
        second = doc.new_page(width=200, height=200)
        second.insert_text((40, 100), "PAGE 2")
        doc.save(pdf_path)

    first_png = _render_doc_image(pdf_path, [_evidence()], page_number=1, zoom=1.0)
    second_png = _render_doc_image(pdf_path, [], page_number=2, zoom=1.0)

    first_image = Image.open(BytesIO(first_png)).convert("RGB")
    second_image = Image.open(BytesIO(second_png)).convert("RGB")
    assert first_image.size == (200, 200)
    assert second_image.size == (200, 200)
    assert any(r > 180 and g < 100 and b < 100 for r, g, b in first_image.getdata())

    with pytest.raises(ValueError, match="超出 PDF 范围"):
        _render_doc_image(pdf_path, [], page_number=3)
