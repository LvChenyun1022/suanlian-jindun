"""77号文规则引擎测试：每条规则的命中/不命中用例。"""
from __future__ import annotations

from datetime import date, timedelta

from src.rules import CaseContext, CaseSummary, evaluate_rules, load_rules
from tests.conftest import make_contract, make_invoice, make_lease, make_verification


def make_ctx(**overrides) -> CaseContext:
    ctx = CaseContext(
        case_id=overrides.pop("case_id", "case_9001"),
        contract=overrides.pop("contract", make_contract()),
        invoice=overrides.pop("invoice", make_invoice()),
        lease_items=overrides.pop("lease_items", make_lease()),
        verification=overrides.pop("verification", make_verification()),
        **overrides,
    )
    return ctx


def _hits(ctx: CaseContext):
    return {h.rule_id: h for h in evaluate_rules(ctx)}


def test_rules_yaml_loads() -> None:
    rules = load_rules()
    ids = [r["id"] for r in rules]
    assert ids == ["R77-001", "R77-002", "R77-003", "R77-004", "R77-005"]
    for r in rules:
        assert r["clause_ref"].startswith("银发〔2025〕77号")
        assert r["severity"] in ("block", "high", "medium", "low")


def test_r77_001_account_days_hint() -> None:
    ctx = make_ctx(contract=make_contract(account_days=200))
    hits = _hits(ctx)
    assert "R77-001" in hits and "R77-002" not in hits
    assert hits["R77-001"].severity == "medium"
    assert "183" in hits["R77-001"].description or "183" in hits["R77-001"].detail

    ctx_no = make_ctx(contract=make_contract(account_days=180))
    assert "R77-001" not in _hits(ctx_no)


def test_r77_002_account_days_violation() -> None:
    ctx = make_ctx(contract=make_contract(account_days=400))
    hits = _hits(ctx)
    assert "R77-002" in hits and "R77-001" in hits
    assert hits["R77-002"].severity == "high"

    ctx_no = make_ctx(contract=make_contract(account_days=365))
    assert "R77-002" not in _hits(ctx_no)


def test_r77_003_verification_failed() -> None:
    ctx = make_ctx(verification=make_verification(all_pass=False))
    hits = _hits(ctx)
    assert "R77-003" in hits
    assert hits["R77-003"].clause_ref == "银发〔2025〕77号 第十条（真实贸易背景审查）"

    ctx_ok = make_ctx(verification=make_verification(all_pass=True))
    assert "R77-003" not in _hits(ctx_ok)


def test_r77_004_split_amounts() -> None:
    d0 = date(2025, 6, 1)
    summaries = [
        CaseSummary("case_9001", "乙承租人有限公司", "甲供应商有限公司", d0, 4_500_000.0),
        CaseSummary("case_9002", "乙承租人有限公司", "丙公司", d0 + timedelta(days=10), 4_600_000.0),
        CaseSummary("case_9003", "其他公司", "丁公司", d0 + timedelta(days=5), 4_700_000.0),
    ]
    ctx = make_ctx(contract=make_contract(total=4_500_000.0), all_cases=summaries)
    hits = _hits(ctx)
    assert "R77-004" in hits
    assert "case_9002" in hits["R77-004"].detail
    assert "case_9003" not in hits["R77-004"].detail  # 主体不同不计入

    # 本案金额低于阈值*0.8 → 不命中
    low = [
        CaseSummary("case_9001", "乙承租人有限公司", "甲供应商有限公司", d0, 1_000_000.0),
        CaseSummary("case_9002", "乙承租人有限公司", "丙公司", d0 + timedelta(days=10), 4_600_000.0),
    ]
    ctx_low = make_ctx(contract=make_contract(total=1_000_000.0), all_cases=low)
    assert "R77-004" not in _hits(ctx_low)

    # 窗口外 → 不命中
    far = [
        CaseSummary("case_9001", "乙承租人有限公司", "甲供应商有限公司", d0, 4_500_000.0),
        CaseSummary("case_9004", "乙承租人有限公司", "丙公司", d0 + timedelta(days=60), 4_600_000.0),
    ]
    ctx_far = make_ctx(contract=make_contract(total=4_500_000.0), all_cases=far)
    assert "R77-004" not in _hits(ctx_far)


def test_r77_005_registry_conflict() -> None:
    lease = make_lease(item_id="ZL-POOL-001", serial_no="SN8CC278CT")
    ctx = make_ctx(
        lease_items=lease,
        item_index={"ZL-POOL-001": {"case_9001", "case_0002"}},
        serial_index={"SN8CC278CT": {"case_9001", "case_0002"}},
    )
    hits = _hits(ctx)
    assert "R77-005" in hits
    assert hits["R77-005"].severity == "block"
    assert "case_0002" in hits["R77-005"].detail

    ctx_ok = make_ctx(
        item_index={"ZL-9001-A": {"case_9001"}},
        serial_index={"SNTEST0001": {"case_9001"}},
    )
    assert "R77-005" not in _hits(ctx_ok)


def test_normal_case_no_hits() -> None:
    """完全正常的案件（短账期、核验通过、无重复登记、金额远离阈值）不命中任何规则。"""
    ctx = make_ctx(
        item_index={"ZL-9001-A": {"case_9001"}},
        serial_index={"SNTEST0001": {"case_9001"}},
        all_cases=[CaseSummary("case_9001", "乙承租人有限公司", "甲供应商有限公司",
                               date(2025, 6, 1), 1_000_000.0)],
    )
    assert _hits(ctx) == {}

