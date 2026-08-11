"""风险评分（SPEC M7）：显式权重汇总 0–100 + 分项贡献 + 人审路由。"""
from .score import load_scoring_config, score_case

__all__ = ["load_scoring_config", "score_case"]
