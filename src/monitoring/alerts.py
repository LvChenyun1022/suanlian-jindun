"""规则预警：连续 N 天低于阈值、环比骤降 → 绿/黄/红 + "T-N 天预警"。

绿 = 无预警（不产出 UtilizationAlert）；黄/橙/红 对应 UtilizationAlert.level。
"T-N 天" 为距下一租金支付日的提前量（按 config.monitoring.rent_interval_days）。
"""
from __future__ import annotations

from ..schemas import UtilizationAlert
from .generator import load_monitoring_config


def _lead_days(trigger_day: int, rent_interval: int) -> int:
    return rent_interval - (trigger_day % rent_interval)


def _max_run_below(series: list[float], threshold: float) -> tuple[int, int]:
    """最长连续低于阈值的天数与其结束日索引。"""
    best = cur = 0
    best_end = -1
    for i, v in enumerate(series):
        cur = cur + 1 if v < threshold else 0
        if cur > best:
            best, best_end = cur, i
    return best, best_end


def detect_alerts(
    case_id: str,
    series: list[float],
    config: dict | None = None,
) -> list[UtilizationAlert]:
    """对利用率序列执行规则预警，返回黄/橙/红预警列表（绿 = 空列表）。"""
    cfg = config or load_monitoring_config()
    rent_interval = int(cfg["rent_interval_days"])
    alerts: list[UtilizationAlert] = []

    if not series:
        return alerts

    # 全零/近零交付 → 红色 zero_delivery
    if all(v < float(cfg["low_threshold"]) for v in series):
        alerts.append(UtilizationAlert(
            case_id=case_id, alert_type="zero_delivery", level="red",
            window=f"D1-D{len(series)}",
            detail=f"全周期利用率低于 {cfg['low_threshold']:.0%}，疑似无真实算力交付"
                   f"（T-{_lead_days(len(series) - 1, rent_interval)} 天预警）",
            metric_value=max(series),
        ))
        return alerts

    # 连续低利用率 → 红/黄 long_idle
    run, end = _max_run_below(series, float(cfg["low_threshold"]))
    if run >= int(cfg["low_days"]):
        alerts.append(UtilizationAlert(
            case_id=case_id, alert_type="long_idle", level="red",
            window=f"D{end - run + 1}-D{end}",
            detail=f"连续 {run} 天利用率低于 {cfg['low_threshold']:.0%}"
                   f"（T-{_lead_days(end, rent_interval)} 天预警）",
            metric_value=round(sum(series[end - run + 1:end + 1]) / run, 4),
        ))
    else:
        run_mid, end_mid = _max_run_below(series, float(cfg["mid_threshold"]))
        if run_mid >= int(cfg["mid_days"]):
            alerts.append(UtilizationAlert(
                case_id=case_id, alert_type="long_idle", level="yellow",
                window=f"D{end_mid - run_mid + 1}-D{end_mid}",
                detail=f"连续 {run_mid} 天利用率低于 {cfg['mid_threshold']:.0%}"
                       f"（T-{_lead_days(end_mid, rent_interval)} 天预警）",
                metric_value=round(sum(series[end_mid - run_mid + 1:end_mid + 1]) / run_mid, 4),
            ))

    # 周环比骤降 → 橙色 sudden_drop
    drop_ratio = float(cfg["drop_ratio"])
    for w in range(7, len(series) - 6, 7):
        prev = sum(series[w - 7:w]) / 7
        cur = sum(series[w:w + 7]) / 7
        if prev >= 0.3 and cur < prev * (1 - drop_ratio):
            alerts.append(UtilizationAlert(
                case_id=case_id, alert_type="sudden_drop", level="orange",
                window=f"D{w - 6}-D{w + 7}",
                detail=f"周均利用率 {prev:.0%} → {cur:.0%}，环比骤降超 {drop_ratio:.0%}"
                       f"（T-{_lead_days(w, rent_interval)} 天预警）",
                metric_value=round(cur, 4),
            ))
            break
    return alerts
