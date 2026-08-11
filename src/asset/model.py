"""GPU 分代残值模型 + 三档压力情景。

- 残值曲线：年度锚点（config/asset.yaml，公开案例校准假设值）年内线性插值，48 个月加速折旧；
- DSCR = 租金回收现金流 / 融资本金；LTV = 剩余本金 / 租赁物残值；
- 压力情景：stress = 利用率 -20%（回收率同步 -20%）；extreme = 单一客户违约（按集中度加权，
  回收 = 已收租金 + 违约时点残值 × (1 - 处置折扣)）。
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..schemas import (
    ContractEssentials,
    LeaseItemEssentials,
    ResidualStressResult,
    ScenarioResult,
)

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "asset.yaml"


def load_asset_config(path: str | Path | None = None) -> dict:
    with open(path or _DEFAULT_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _generation_key(model: str, cfg: dict) -> str:
    m = model.upper()
    for key in cfg["generations"]:
        if key != "default" and re.search(rf"\b{re.escape(key.upper())}\b", m.replace("RTX 4090", "RTX4090")):
            return key
    return "default"


def depreciation_curve(model: str, cfg: dict) -> list[float]:
    """48 个月残值率曲线（首月 1.0，年末锚点间线性插值，单调不增）。"""
    anchors = cfg["generations"][_generation_key(model, cfg)]
    horizon = int(cfg["horizon_months"])
    points = [1.0] + [float(a) for a in anchors]  # 第 0/12/24/36/48 月
    curve: list[float] = []
    for mth in range(horizon + 1):
        seg = min(mth // 12, len(points) - 2)
        frac = (mth - seg * 12) / 12
        value = points[seg] + (points[seg + 1] - points[seg]) * frac
        curve.append(round(value, 4))
    return curve


def run_stress_test(
    case_id: str,
    contract: ContractEssentials,
    lease: LeaseItemEssentials,
    config: dict | None = None,
) -> ResidualStressResult:
    """对 GPU 租赁物执行残值与现金流压力测试。"""
    cfg = config or load_asset_config()
    gpu_model = lease.items[0].model if lease.items else "unknown"
    curve = depreciation_curve(gpu_model, cfg)

    purchase = lease.total_value.amount
    principal = purchase * float(cfg["financing_ratio"])
    term = contract.lease_term_months or int(cfg["default_lease_term"])
    rent_total = contract.total_amount.amount       # 合同额视为租金总额（含息）
    monthly_rent = rent_total / term
    payback_months = round(principal / monthly_rent, 1)

    ltv_limit = float(cfg["ltv_breach"])
    dscr_limit = float(cfg["dscr_breach"])
    shock = float(cfg["stress"]["utilization_shock"])
    haircut = float(cfg["stress"]["default_haircut"])
    concentration = float(cfg["stress"]["customer_concentration"])

    def ltv_at(month: int) -> float:
        # 本金摊还与残值曲线匹配（气球结构假设：租金前置覆盖折旧）
        remaining = principal * curve[min(month, len(curve) - 1)]
        residual = purchase * curve[min(month, len(curve) - 1)]
        return round(remaining / residual, 4) if residual > 0 else float("inf")

    scenarios: list[ScenarioResult] = []

    # base：正常回收，LTV 取租期中点
    dscr_base = rent_total / principal
    ltv_base = ltv_at(term // 2)
    scenarios.append(ScenarioResult(
        scenario="base",
        residual_value_ratio=curve[term] if term < len(curve) else curve[-1],
        ltv=ltv_base,
        dscr=round(dscr_base, 4),
        breach=ltv_base > ltv_limit or dscr_base < dscr_limit,
        detail=f"正常回收；月租金 {monthly_rent:,.0f} 元，回本 {payback_months} 个月",
    ))

    # stress：利用率 -20% → 租金回收率同步 -20%
    dscr_stress = dscr_base * (1 + shock)
    ltv_stress = ltv_at(term // 2) * (1 - shock / 2)  # 残值小幅下修
    scenarios.append(ScenarioResult(
        scenario="stress",
        residual_value_ratio=round(curve[min(term, len(curve) - 1)] * (1 + shock / 2), 4),
        ltv=round(ltv_stress, 4),
        dscr=round(dscr_stress, 4),
        breach=ltv_stress > ltv_limit or dscr_stress < dscr_limit,
        detail=f"利用率 {shock:+.0%}，租金回收率同步 {shock:+.0%}",
    ))

    # extreme：单一客户违约（按集中度加权），回收 = 已收租金 + 违约时点残值×(1-折扣)
    paid_months = int(cfg["default_months_paid"])
    residual_at_default = purchase * curve[min(paid_months, len(curve) - 1)]
    recovery = monthly_rent * paid_months + residual_at_default * (1 - haircut)
    dscr_extreme = concentration * recovery / principal
    ltv_extreme = principal / residual_at_default if residual_at_default > 0 else float("inf")
    scenarios.append(ScenarioResult(
        scenario="extreme",
        residual_value_ratio=round(curve[min(paid_months, len(curve) - 1)], 4),
        ltv=round(ltv_extreme, 4),
        dscr=round(dscr_extreme, 4),
        breach=ltv_extreme > ltv_limit or dscr_extreme < dscr_limit,
        detail=f"单一客户违约（集中度 {concentration:.0%}），第 {paid_months} 个月违约、处置折扣 {haircut:.0%}",
    ))

    return ResidualStressResult(
        case_id=case_id,
        gpu_model=gpu_model,
        depreciation_curve=curve,
        scenarios=scenarios,
        payback_months=payback_months,
    )
