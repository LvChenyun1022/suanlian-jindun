"""三单核验测试：正常全过、欺诈识别、容差可配、跨案件重复检测。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.settings import LLMSettings
from src.parsing import parse_case
from src.verification import (
    build_item_index,
    build_serial_index,
    normalize_name,
    verify_case,
)
from tests.conftest import make_contract, make_invoice, make_lease


def read_labels(root: Path) -> list[dict]:
    return [json.loads(l) for l in (root / "labels.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def verified20(ds20: Path):
    """解析 20 案并建跨案件索引。"""
    s = LLMSettings(api_key=None, base_url="", model="")
    parsed, evidences = {}, {}
    for row in read_labels(ds20):
        c, i, l, ev = parse_case(row["files"], ds20, settings=s)
        parsed[row["case_id"]] = (c, i, l)
        evidences[row["case_id"]] = ev
    lease_map = {cid: t[2] for cid, t in parsed.items()}
    return {
        "parsed": parsed,
        "evidences": evidences,
        "item_index": build_item_index(lease_map),
        "serial_index": build_serial_index(lease_map),
        "labels": {r["case_id"]: r for r in read_labels(ds20)},
    }


def _check_map(vr):
    return {c.check_name: c for c in vr.checks}


def test_normal_case_all_pass(verified20: dict) -> None:
    normal = [cid for cid, r in verified20["labels"].items() if not r["is_fraud"]]
    assert normal
    for cid in normal:
        c, i, l = verified20["parsed"][cid]
        vr = verify_case(
            cid, c, i, l, verified20["evidences"][cid],
            item_index=verified20["item_index"], serial_index=verified20["serial_index"],
        )
        assert vr.all_passed, f"{cid}: {[c.detail for c in vr.checks if not c.passed]}"
        for chk in vr.checks:
            assert chk.evidences or chk.passed  # 通过项允许无证据（如跨案件无重复）


def test_fraud_a_buyer_mismatch_detected(verified20: dict) -> None:
    frauds = [cid for cid, r in verified20["labels"].items() if r["fraud_pattern"] == "a_chengxing"]
    assert frauds, "小数据集应含承兴系样本"
    for cid in frauds:
        c, i, l = verified20["parsed"][cid]
        vr = verify_case(cid, c, i, l, verified20["evidences"][cid])
        cm = _check_map(vr)
        assert not cm["contract_vs_invoice.buyer_name"].passed
        assert not vr.all_passed
        # 证据引用须含双方案头字段
        names = {e.field_name for e in cm["contract_vs_invoice.buyer_name"].evidences}
        assert {"lessee.name", "buyer.name"} <= names


def test_fraud_c_account_period_detected(verified20: dict) -> None:
    frauds = [cid for cid, r in verified20["labels"].items() if r["fraud_pattern"] == "c_circular_trade"]
    assert frauds
    for cid in frauds:
        c, i, l = verified20["parsed"][cid]
        vr = verify_case(cid, c, i, l, verified20["evidences"][cid])
        assert not _check_map(vr)["account_period.consistency"].passed


def test_fraud_b_duplicate_item_detected_with_index(verified20: dict) -> None:
    frauds = [cid for cid, r in verified20["labels"].items() if r["fraud_pattern"] == "b_multi_pledge"]
    assert frauds
    for cid in frauds:
        c, i, l = verified20["parsed"][cid]
        # 无索引时单据内部一致，不判重复
        vr_no_idx = verify_case(cid, c, i, l, verified20["evidences"][cid])
        assert "cross_case.item_id_duplicate" not in _check_map(vr_no_idx)
        # 有索引时识别一单多押
        vr = verify_case(
            cid, c, i, l, verified20["evidences"][cid],
            item_index=verified20["item_index"], serial_index=verified20["serial_index"],
        )
        cm = _check_map(vr)
        assert not cm["cross_case.item_id_duplicate"].passed
        assert not cm["cross_case.serial_no_duplicate"].passed
        assert cm["cross_case.item_id_duplicate"].evidences


def test_amount_tolerance_configurable() -> None:
    """容差由配置/参数控制：差 0.5 元在 tol=1.0 通过、tol=0.1 不通过。"""
    contract = make_contract(total=1_000_000.0)
    invoice = make_invoice(total=1_000_000.5)
    lease = make_lease(total=1_000_000.0)
    vr = verify_case("case_t", contract, invoice, lease, [], tolerance=1.0)
    assert _check_map(vr)["amount.contract_vs_invoice"].passed
    vr2 = verify_case("case_t", contract, invoice, lease, [], tolerance=0.1)
    assert not _check_map(vr2)["amount.contract_vs_invoice"].passed


def test_name_normalization() -> None:
    assert normalize_name(" 甲 公司（北京）有限公司 ") == normalize_name("甲公司(北京)有限公司")
    assert normalize_name("甲公司") != normalize_name("甲公司分公司")
