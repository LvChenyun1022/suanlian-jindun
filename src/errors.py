"""结构化异常（SPEC 第 5.1 节）。

所有异常携带 code 与 context；pipeline 捕获后写入 state.errors（f"{code}: {message}"）。
"""
from __future__ import annotations


class JinDunError(Exception):
    """基类：携带 code 与 context，message 面向日志。"""

    code = "JD_UNKNOWN"

    def __init__(self, message: str, *, code: str | None = None, context: dict | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.context = context or {}

    def to_log(self) -> str:
        return f"{self.code}: {self}"


class ParseError(JinDunError):
    """code="PARSE_*"：单据无法解析/要素缺失/校验失败。"""

    code = "PARSE_ERROR"


class VerificationError(JinDunError):
    """code="VERIFY_*"。"""

    code = "VERIFY_ERROR"


class LLMError(JinDunError):
    """code="LLM_*"：超时/限流/非法 JSON。"""

    code = "LLM_ERROR"


class GuardrailViolation(JinDunError):
    """code="GUARD_*"：护栏命中，终止处理。"""

    code = "GUARD_ERROR"


class AuditChainError(JinDunError):
    """code="AUDIT_*"：哈希链校验失败。"""

    code = "AUDIT_ERROR"
