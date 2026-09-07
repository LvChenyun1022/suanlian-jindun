"""GPU 示意性压力测试计算器（SPEC M5，参数见 config/asset.yaml）。"""
from .model import load_asset_config, run_stress_test

__all__ = ["load_asset_config", "run_stress_test"]
