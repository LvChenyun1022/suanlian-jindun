"""合成 GPU 利用率时序生成器：趋势 + 突变噪声，按 case_id 确定性产出。

遥测画像由 case_id 哈希分桶决定（normal/idle/drop），不读取任何标签，避免信息泄漏。
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "monitoring.yaml"


def load_monitoring_config(path: str | Path | None = None) -> dict:
    with open(path or _DEFAULT_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _profile_for(case_id: str) -> str:
    """哈希分桶：~10% idle（长期闲置）、~8% drop（中段骤降），其余 normal。"""
    bucket = int(hashlib.md5(case_id.encode()).hexdigest(), 16) % 100
    if bucket < 10:
        return "idle"
    if bucket < 18:
        return "drop"
    return "normal"


def generate_series(case_id: str, days: int = 180, profile: str | None = None) -> list[float]:
    """生成日级利用率序列 [0,1]，含趋势项与突变噪声；同 case_id 结果可复现。"""
    profile = profile or _profile_for(case_id)
    rng = random.Random(int(hashlib.md5(f"telemetry:{case_id}".encode()).hexdigest(), 16))
    series: list[float] = []
    drift = rng.uniform(-0.0005, 0.0005)          # 缓慢趋势
    base = {"normal": rng.uniform(0.65, 0.85), "idle": rng.uniform(0.02, 0.06),
            "drop": rng.uniform(0.65, 0.8)}[profile]
    drop_start = rng.randint(days // 3, days // 2) if profile == "drop" else -1
    for d in range(days):
        level = base + drift * d
        if profile == "drop" and d >= drop_start:
            level = base * 0.15 + drift * d       # 骤降后长期低位
        noise = rng.gauss(0, 0.05)
        if rng.random() < 0.02:                    # 突变噪声尖峰
            noise += rng.choice([-1, 1]) * rng.uniform(0.1, 0.25)
        series.append(round(min(1.0, max(0.0, level + noise)), 4))
    return series


def mock_telemetry_feed(case_id: str, days: int = 180) -> list[float]:
    """模拟接口：真实系统中此处对接算力调度平台遥测 API；本演示返回本地合成序列。"""
    return generate_series(case_id, days)
