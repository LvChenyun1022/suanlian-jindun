"""GPU 残值与现金流压力测试（SPEC M5，参数见 config/asset.yaml）。"""
from .model import load_asset_config, run_stress_test

__all__ = ["load_asset_config", "run_stress_test"]
