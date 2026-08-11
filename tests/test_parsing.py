"""解析阶段测试：准确率≥95%（mock 同口径）、证据完整性、结构化错误与审计。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.settings import load_settings
from eval.compare import score_case
from src.audit import AuditLogger
from src.datagen.pdfdoc import SimplePdfWriter
from src.errors import ParseError
from src.parsing import parse_case, parse_document
from src.schemas import DocType


def read_labels(root: Path) -> list[dict]:
    return [json.loads(l) for l in (root / "labels.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def parsed20(ds20: Path):
    """mock 模式（显式无 Key 配置，纯正则路径）解析 20 案全集。"""
    from config.settings import LLMSettings

    mock_settings = LLMSettings(api_key=None, base_url="", model="")
    assert mock_settings.mock_mode
    result = {}
    for row in read_labels(ds20):
        c, i, l, ev = parse_case(row["files"], ds20, settings=mock_settings)
        result[row["case_id"]] = {"parsed": {"contract": c, "invoice": i, "lease_items": l}, "ev": ev}
    return result


def test_parsing_accuracy_mock(parsed20: dict, ds20: Path) -> None:
    """mock（纯正则）模式字段级准确率 ≥95%（SPEC 指标 1）。"""
    matched = total = 0
    for row in read_labels(ds20):
        m, t, _misses = score_case(row["oracle"], parsed20[row["case_id"]]["parsed"])
        matched += m
        total += t
    accuracy = matched / total
    assert accuracy >= 0.95, f"准确率 {accuracy:.2%} 低于 95%"
    assert accuracy == 1.0, f"模板化合成数据应达 100%，实际 {accuracy:.2%}"


def test_parse_spot_check_vs_oracle(parsed20: dict, ds20: Path) -> None:
    row = next(r for r in read_labels(ds20) if not r["is_fraud"])
    p = parsed20[row["case_id"]]["parsed"]
    oc = row["oracle"]["contract"]["fields"]
    assert p["contract"].contract_no == oc["contract_no"]["value"]
    assert p["contract"].sign_date.isoformat() == oc["sign_date"]["value"]
    assert p["contract"].vendor.name == oc["seller_name"]["value"]
    oi = row["oracle"]["invoice"]["fields"]
    assert p["invoice"].invoice_no == oi["invoice_no"]["value"]
    ol = row["oracle"]["lease_items"]["fields"]
    n_items = len([k for k in ol if k.endswith(".item_id")])
    assert len(p["lease_items"].items) == n_items
    assert p["lease_items"].items[0].serial_no == ol["items.0.serial_no"]["value"]


def test_every_field_has_evidence(parsed20: dict) -> None:
    """每个抽取字段必须携带证据：页码≥1、excerpt 非空且含值、pymupdf 后端 bbox 非空。"""
    for cid, bundle in parsed20.items():
        evs = bundle["ev"]
        assert evs, f"{cid} 无证据"
        for ev in evs:
            assert ev.page >= 1
            assert ev.excerpt.strip()
            assert ev.bbox is not None, f"{cid}/{ev.field_name} 缺坐标"
            assert ev.source_file.endswith(".pdf")
        # 关键字段的证据必须存在
        names = {e.field_name for e in evs}
        assert {"contract_no", "total_amount.amount"} & names


def test_structured_error_and_audit(tmp_path: Path) -> None:
    """缺字段 PDF → ParseError(PARSE_FIELD_MISSING) 且写入审计日志。"""
    bad = tmp_path / "bad.pdf"
    w = SimplePdfWriter(bad, "购销合同")
    w.field_line("contract_no", "合同编号", "HT-2025-9999")
    w.save()
    from config.settings import LLMSettings

    mock_settings = LLMSettings(api_key=None, base_url="", model="")  # 不触发 LLM
    audit = AuditLogger(tmp_path / "audit.jsonl", "mock")
    with pytest.raises(ParseError) as exc_info:
        parse_document(bad, DocType.CONTRACT, settings=mock_settings, audit=audit)
    assert exc_info.value.code == "PARSE_FIELD_MISSING"
    assert exc_info.value.context["fields"]
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["stage"] == "parsing.error"


def test_unreadable_pdf_structured_error(tmp_path: Path) -> None:
    garbage = tmp_path / "garbage.pdf"
    garbage.write_bytes(b"not a pdf at all \x00\x01\x02")
    with pytest.raises(ParseError) as exc_info:
        parse_document(garbage, DocType.CONTRACT)
    assert exc_info.value.code in ("PARSE_UNREADABLE", "PARSE_FIELD_MISSING")


def test_mock_mode_when_no_key(ds20: Path) -> None:
    """无 LLM_API_KEY 时自动回退纯正则 mock 模式（SPEC 5.2）。"""
    from config.settings import LLMSettings

    mock_settings = LLMSettings(api_key=None, base_url="", model="")
    assert mock_settings.mock_mode is True
    row = read_labels(ds20)[0]
    c, i, l, ev = parse_case(row["files"], ds20, settings=mock_settings)
    assert c.contract_no == row["oracle"]["contract"]["fields"]["contract_no"]["value"]
