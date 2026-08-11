"""资产/预警/评分测试。"""
from __future__ import annotations

from src.asset import load_asset_config, run_stress_test
from src.monitoring import detect_alerts, generate_series, fetch_external_signals
from src.scoring import load_scoring_config, score_case
from src.schemas import RuleHit, UtilizationAlert
from tests.conftest import make_contract, make_invoice, make_lease, make_verification


# ---------- asset ----------

def test_depreciation_curve_shape() -> None:
    cfg = load_asset_config()
    result = run_stress_test("case_t", make_contract(), make_lease(), cfg)
    curve = result.depreciation_curve
    assert len(curve) == 49  # 0..48 月
    assert curve[0] == 1.0
    assert all(curve[i] >= curve[i + 1] for i in range(len(curve) - 1)), "曲线须单调不增"
    assert 0 < curve[-1] < 0.3  # 4 年末残值显著折损


def test_stress_scenarios() -> None:
    result = run_stress_test("case_t", make_contract(), make_lease())
    by_name = {s.scenario: s for s in result.scenarios}
    assert set(by_name) == {"base", "stress", "extreme"}
    assert not by_name["base"].breach, "基准情景不应突破阈值"
    assert by_name["stress"].breach      # 利用率 -20% → DSCR 跌破 1
    assert by_name["extreme"].breach     # 单客户违约（集中度 100%）
    assert by_name["stress"].dscr < by_name["base"].dscr
    assert result.payback_months and result.payback_months > 0


# ---------- monitoring ----------

def test_series_deterministic_and_profiles() -> None:
    s1 = generate_series("case_0001")
    s2 = generate_series("case_0001")
    assert s1 == s2 and len(s1) == 180
    idle = generate_series("case_x", profile="idle")
    assert max(idle) < 0.2


def test_alerts_levels() -> None:
    # 长期闲置 → 红
    idle = generate_series("case_idle", profile="idle")
    alerts = detect_alerts("case_idle", idle)
    assert any(a.alert_type in ("long_idle", "zero_delivery") and a.level == "red" for a in alerts)
    assert "T-" in alerts[0].detail  # T-N 天预警
    # 骤降 → 橙
    drop = generate_series("case_drop", profile="drop")
    alerts2 = detect_alerts("case_drop", drop)
    assert any(a.alert_type == "sudden_drop" and a.level == "orange" for a in alerts2)
    # 正常 → 绿（无预警）
    normal = generate_series("case_ok", profile="normal")
    assert detect_alerts("case_ok", normal) == []


def test_external_signals_mock() -> None:
    signals = fetch_external_signals(["华鼎科技（成都）有限公司", "无关公司"])
    assert signals and "模拟" in signals[0]
    assert fetch_external_signals(["无关公司"]) == []


# ---------- scoring ----------

def _hit(rule_id: str, severity: str) -> RuleHit:
    return RuleHit(rule_id=rule_id, clause_ref="77号文 第X条", severity=severity,
                   description="d", evidences=[], detail="t")


def test_scoring_weights_and_routing() -> None:
    cfg = load_scoring_config()
    vr_ok = make_verification(all_pass=True)
    vr_bad = make_verification(all_pass=False)

    # 正常：无命中无预警 → pass
    s0 = score_case("c0", vr_ok, [], None, [], cfg)
    assert s0.grade == "pass" and s0.total < 60
    assert abs(sum(c.contribution for c in s0.components) - s0.total) < 0.05

    # high 规则 → 兜底 ≥60 → review（强制人审）
    s1 = score_case("c1", vr_bad, [_hit("R77-003", "high")], None, [], cfg)
    assert 60 <= s1.total <= 90 and s1.grade == "review"
    assert any("人工复核" in r for r in s1.reasons)

    # block 规则 → 兜底 >90 → reject + 理由
    s2 = score_case("c2", vr_bad, [_hit("R77-005", "block")], None, [], cfg)
    assert s2.total > 90 and s2.grade == "reject" and s2.reasons

    # 红色预警推升但不越人审线以下
    alert = UtilizationAlert(case_id="c3", alert_type="long_idle", level="red",
                             window="D1-D20", detail="t", metric_value=0.05)
    s3 = score_case("c3", vr_ok, [], None, [alert], cfg)
    assert s3.components[3].contribution == 15.0 and s3.grade == "pass"


def test_scoring_deterministic() -> None:
    vr = make_verification(all_pass=False)
    a = score_case("c", vr, [_hit("R77-003", "high")], None, [])
    b = score_case("c", vr, [_hit("R77-003", "high")], None, [])
    assert a.total == b.total  # 同输入同输出
