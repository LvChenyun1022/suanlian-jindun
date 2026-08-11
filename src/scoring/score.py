"""风险评分实现：total = Σ(weight × raw) × 100 + 红线兜底，路由 <60/60–90/>90。

路由约定（config/scoring.yaml）：
- total < 60        → pass（建议通过）
- 60 ≤ total ≤ 90   → review（强制"待人工复核"，不得自动放行）
- total > 90        → reject（建议拒绝 + 理由）
"""
from __future__ import annotations

from pathlib import Path

import yaml

from ..schemas import (
    ResidualStressResult,
    RiskScore,
    RuleHit,
    ScoreComponent,
    UtilizationAlert,
    VerificationResult,
)

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "scoring.yaml"


def load_scoring_config(path: str | Path | None = None) -> dict:
    with open(path or _DEFAULT_CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    total_w = sum(cfg["weights"].values())
    assert abs(total_w - 1.0) < 1e-6, f"权重合计必须为 1.0，实际 {total_w}"
    return cfg


def score_case(
    case_id: str,
    verification: VerificationResult | None,
    rule_hits: list[RuleHit],
    stress: ResidualStressResult | None,
    alerts: list[UtilizationAlert],
    config: dict | None = None,
) -> RiskScore:
    """汇总四项分项为 0–100 风险分（越高越危险）并给出路由。"""
    cfg = config or load_scoring_config()
    w = cfg["weights"]
    reasons: list[str] = []

    # verification：raw = min(1, 失败项 × per_fail)
    if verification is not None and verification.checks:
        raw_v = min(1.0, verification.failed_count * float(cfg["raw"]["verification_per_fail"]))
        if verification.failed_count:
            reasons.append(f"三单核验 {verification.failed_count} 项未通过")
    else:
        raw_v = 1.0  # 缺核验结果按最高风险处理
        reasons.append("缺少三单核验结果")

    # rules：raw = 最高严重度 + 每多一条 bonus，封顶 1.0
    sev_map = cfg["raw"]["severity"]
    if rule_hits:
        raw_r = max(sev_map[h.severity] for h in rule_hits)
        raw_r = min(1.0, raw_r + float(cfg["raw"]["extra_rule_bonus"]) * (len(rule_hits) - 1))
        worst = max(rule_hits, key=lambda h: sev_map[h.severity])
        reasons.append(f"规则命中 {len(rule_hits)} 条（最重 {worst.rule_id}/{worst.severity}）")
    else:
        raw_r = 0.0

    # stress：取最严重突破情景
    breach_map = cfg["raw"]["stress_breach"]
    raw_s = 0.0
    if stress is not None:
        for sc in stress.scenarios:
            if sc.breach:
                raw_s = max(raw_s, float(breach_map[sc.scenario]))
        if raw_s:
            breached = [s.scenario for s in stress.scenarios if s.breach]
            reasons.append(f"压力测试突破阈值情景: {'/'.join(breached)}")

    # utilization：取最高预警级别
    level_map = cfg["raw"]["alert_level"]
    raw_u = max((float(level_map[a.level]) for a in alerts), default=0.0)
    if alerts:
        reasons.append(f"利用率预警 {len(alerts)} 条（最高 {max(alerts, key=lambda a: level_map[a.level]).level}）")

    components = [
        ScoreComponent(name="verification", weight=w["verification"], raw=round(raw_v, 4),
                       contribution=round(w["verification"] * raw_v * 100, 2)),
        ScoreComponent(name="rules", weight=w["rules"], raw=round(raw_r, 4),
                       contribution=round(w["rules"] * raw_r * 100, 2)),
        ScoreComponent(name="stress", weight=w["stress"], raw=round(raw_s, 4),
                       contribution=round(w["stress"] * raw_s * 100, 2)),
        ScoreComponent(name="utilization", weight=w["utilization"], raw=round(raw_u, 4),
                       contribution=round(w["utilization"] * raw_u * 100, 2)),
    ]
    total = round(sum(c.contribution for c in components), 2)

    # 红线兜底（一票进入人审/拒绝）
    if rule_hits:
        sev_set = {h.severity for h in rule_hits}
        if "block" in sev_set:
            total = max(total, float(cfg["overrides"]["block_min_score"]))
        elif "high" in sev_set:
            total = max(total, float(cfg["overrides"]["high_min_score"]))
    total = min(100.0, total)

    pass_max = float(cfg["routes"]["pass_max"])
    review_max = float(cfg["routes"]["review_max"])
    if total < pass_max:
        grade = "pass"
        reasons = reasons or ["各分项均未见显著风险"]
    elif total <= review_max:
        grade = "review"  # 强制待人工复核，不得自动放行
        reasons.insert(0, "风险分进入 60–90 区间，强制待人工复核")
    else:
        grade = "reject"
        reasons.insert(0, "风险分超过 90，建议拒绝")

    return RiskScore(case_id=case_id, total=total, components=components, grade=grade, reasons=reasons)
