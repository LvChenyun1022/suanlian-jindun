"""环境配置加载。

读取 .env（若存在）中的 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL。
未配置 LLM_API_KEY 时，系统运行在 mock 模式（不调用外部 LLM API）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMSettings:
    """LLM 连接配置。"""

    api_key: str | None
    base_url: str
    model: str

    @property
    def mock_mode(self) -> bool:
        """未配置 API Key 时即为 mock 模式。"""
        return not self.api_key


def load_settings(env_path: str | None = None) -> LLMSettings:
    """加载环境变量并返回 LLM 配置。

    Args:
        env_path: .env 文件路径；为 None 时自动向上查找。

    Returns:
        LLMSettings：mock_mode=True 表示应使用本地 mock 实现。
    """
    load_dotenv(env_path) if env_path else load_dotenv()
    return LLMSettings(
        api_key=os.getenv("LLM_API_KEY") or None,
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )
