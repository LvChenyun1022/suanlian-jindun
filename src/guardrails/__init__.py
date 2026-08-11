"""合规护栏（SPEC M10）：Pipeline 第一环节与出口把关。

- 提示词注入检测：中英文模式库（可选 LLM 二次判定，live 模式）；
- 敏感数据检测：仅针对用户输入/外部文本（身份证/银行卡真实格式）；
  合成单据内证件号/银行账号均为掩码形式（含 `*`），不会被误拦；
- 工具白名单注册表：白名单外调用拒绝 + 留痕；
- 所有 AI 输出加显式标识。
"""
from .checks import (
    AI_OUTPUT_BANNER,
    check_user_text,
    label_ai_output,
)
from .tools import ToolRegistry

__all__ = [
    "AI_OUTPUT_BANNER",
    "check_user_text",
    "label_ai_output",
    "ToolRegistry",
]
