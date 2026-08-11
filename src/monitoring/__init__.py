"""利用率预警（SPEC M6）：合成遥测生成 + 规则预警 + 模拟外部信号接口。"""
from .alerts import detect_alerts, load_monitoring_config
from .generator import generate_series, mock_telemetry_feed
from .external_signals import fetch_external_signals

__all__ = [
    "detect_alerts",
    "load_monitoring_config",
    "generate_series",
    "mock_telemetry_feed",
    "fetch_external_signals",
]
