"""datagen 阶段测试：模板完整性、标签-PDF 一致性、欺诈分布、种子可复现性。"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf
import pytest

from src.datagen.generate import generate_dataset

REQUIRED_FIELDS = {
    "contract": [
        "contract_no", "sign_date", "seller_name", "buyer_name",
        "subject", "total_amount", "account_days",
    ],
    "invoice": [
        "invoice_no", "invoice_date", "seller_name", "buyer_name",
        "item_name", "quantity", "unit_price",
        "amount_excl_tax", "tax_amount", "amount_incl_tax", "remark",
    ],
    "lease_items": ["list_no", "contract_no", "items.0.item_id", "items.0.model",
                    "items.0.serial_no", "items.0.quantity", "items.0.unit_price",
                    "items.0.total", "total_value"],
}

ID_CARD_RE = re.compile(r"\d{17}[\dXx]")       # 身份证号样式
BANK_CARD_RE = re.compile(r"\d{16,19}")        # 银行卡号样式（长连续数字）


def read_labels(out: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (Path(out) / "labels.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def doc_text(pdf_path: Path) -> tuple[str, int]:
    with pymupdf.open(pdf_path) as doc:
        return "".join(page.get_text() for page in doc), doc.page_count


@pytest.fixture(scope="module")
def small_ds(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ds_small") / "cases"
    generate_dataset(12, out, 123)
    return out


@pytest.fixture(scope="module")
def full_ds(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ds_full") / "cases"
    generate_dataset(100, out, 42)
    return out


# ---------- 1. 模板字段完整性 ----------

def test_template_field_completeness(small_ds: Path) -> None:
    labels = read_labels(small_ds)
    assert len(labels) == 12
    for row in labels:
        assert re.fullmatch(r"case_\d{4}", row["case_id"])
        for doc_type, required in REQUIRED_FIELDS.items():
            fields = row["oracle"][doc_type]["fields"]
            for key in required:
                assert key in fields, f"{row['case_id']}/{doc_type} 缺字段 {key}"
            for key, info in fields.items():
                assert isinstance(info["value"], str) and info["value"], f"{row['case_id']}/{doc_type}/{key} 值为空"
                assert info["value"] in info["excerpt"], f"{row['case_id']}/{doc_type}/{key} excerpt 未含值"
        # 清单条目字段成组出现
        n_items = len([k for k in row["oracle"]["lease_items"]["fields"] if k.endswith(".item_id")])
        assert n_items >= 1


# ---------- 2. 标签与 PDF 内容一致性（PyMuPDF 读回核对） ----------

def test_label_pdf_consistency(small_ds: Path) -> None:
    for row in read_labels(small_ds):
        for doc_type, rel in row["files"].items():
            text, page_count = doc_text(small_ds / rel)
            for key, info in row["oracle"][doc_type]["fields"].items():
                assert info["value"] in text, (
                    f"{row['case_id']}/{doc_type}/{key} 值未在 PDF 文本中找到: {info['value']!r}"
                )
                assert 1 <= info["page"] <= page_count
                x0, y0, x1, y1 = info["bbox"]
                assert 0 <= x0 < x1 <= 600 and 0 <= y0 < y1 <= 850
                assert info["value"] in info["excerpt"]


def test_no_real_style_sensitive_numbers(small_ds: Path) -> None:
    """全文不得出现身份证/银行卡样式的长连续数字（敏感字段一律掩码）。"""
    all_text = ""
    for pdf in small_ds.rglob("*.pdf"):
        text, _ = doc_text(pdf)
        assert not ID_CARD_RE.search(text), f"{pdf} 出现身份证样式号码"
        assert not BANK_CARD_RE.search(text), f"{pdf} 出现银行卡样式长数字"
        all_text += text
    assert "*" in all_text  # 掩码确实存在


# ---------- 3. 欺诈标签分布与造假模式有效性 ----------

def test_fraud_distribution(full_ds: Path) -> None:
    labels = read_labels(full_ds)
    assert len(labels) == 100
    normal = [r for r in labels if not r["is_fraud"]]
    fraud = [r for r in labels if r["is_fraud"]]
    assert len(normal) == 70 and len(fraud) == 30
    for pattern in ("a_chengxing", "b_multi_pledge", "c_circular_trade"):
        assert sum(1 for r in fraud if r["fraud_pattern"] == pattern) == 10
        # 正常案件不得带模式标签；欺诈案件必须带
    assert all(r["fraud_pattern"] is None for r in normal)
    assert all(r["injected_adversarial"] is False for r in labels)


def test_fraud_a_party_mismatch(full_ds: Path) -> None:
    """承兴系：发票购买方 ≠ 合同买方，且为虚构核心企业。"""
    for row in read_labels(full_ds):
        if row["fraud_pattern"] != "a_chengxing":
            continue
        c_buyer = row["oracle"]["contract"]["fields"]["buyer_name"]["value"]
        i_buyer = row["oracle"]["invoice"]["fields"]["buyer_name"]["value"]
        assert c_buyer != i_buyer
        assert row["metadata"]["fraud_detail"]["fabricated_core_enterprise"] == i_buyer
        assert "invoice.buyer_name" in row["metadata"]["fraud_detail"]["mismatched_fields"]


def test_fraud_b_shared_item_across_cases(full_ds: Path) -> None:
    """一单多押：同一租赁物编号+序列号恰好出现在 2 个案件中。"""
    seen: dict[str, list[str]] = {}
    for row in read_labels(full_ds):
        if row["fraud_pattern"] != "b_multi_pledge":
            continue
        detail = row["metadata"]["fraud_detail"]
        fields = row["oracle"]["lease_items"]["fields"]
        assert fields["items.0.item_id"]["value"] == detail["shared_item_id"]
        assert fields["items.0.serial_no"]["value"] == detail["shared_serial_no"]
        seen.setdefault(detail["shared_item_id"], []).append(row["case_id"])
    assert len(seen) == 5
    assert all(len(cases) == 2 and len(set(cases)) == 2 for cases in seen.values())


def test_fraud_c_same_controller_and_closed_loop(full_ds: Path) -> None:
    """空转贸易：买卖双方名称含同一关联前缀，账期为 0，金额闭环一致。"""
    for row in read_labels(full_ds):
        if row["fraud_pattern"] != "c_circular_trade":
            continue
        token = row["metadata"]["fraud_detail"]["related_party_token"]
        seller = row["oracle"]["contract"]["fields"]["seller_name"]["value"]
        buyer = row["oracle"]["contract"]["fields"]["buyer_name"]["value"]
        assert token in seller and token in buyer and seller != buyer
        assert row["metadata"]["account_days"] == 0
        c_total = row["oracle"]["contract"]["fields"]["total_amount"]["value"]
        i_total = row["oracle"]["invoice"]["fields"]["amount_incl_tax"]["value"]
        l_total = row["oracle"]["lease_items"]["fields"]["total_value"]["value"]
        assert c_total == i_total == l_total


# ---------- 4. 种子可复现性 ----------

def test_seed_reproducibility(tmp_path: Path) -> None:
    out1, out2, out3 = tmp_path / "r1", tmp_path / "r2", tmp_path / "r3"
    generate_dataset(8, out1, 7)
    generate_dataset(8, out2, 7)
    generate_dataset(8, out3, 8)

    labels1 = (out1 / "labels.jsonl").read_text(encoding="utf-8")
    assert labels1 == (out2 / "labels.jsonl").read_text(encoding="utf-8")
    assert labels1 != (out3 / "labels.jsonl").read_text(encoding="utf-8")

    for rel in json.loads(labels1.splitlines()[0])["files"].values():
        t1, _ = doc_text(out1 / rel)
        t2, _ = doc_text(out2 / rel)
        assert t1 == t2 and t1.strip()
