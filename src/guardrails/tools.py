"""工具白名单注册表：白名单外调用拒绝 + 留痕。"""
from __future__ import annotations

from typing import Callable

from ..audit.sqlite_store import SqliteAuditStore
from ..errors import GuardrailViolation


class ToolRegistry:
    """工具白名单。pipeline 内所有工具调用必须经注册表转发。"""

    def __init__(self, audit: SqliteAuditStore | None = None) -> None:
        self._tools: dict[str, Callable] = {}
        self.audit = audit

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def is_allowed(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, *args, case_id: str | None = None, **kwargs):
        """白名单内执行并留痕；白名单外拒绝 + 留痕。"""
        if name not in self._tools:
            if self.audit:
                self.audit.log("guardrail.tool_denied", {"tool": name}, None,
                               case_id=case_id, event_type="guardrail",
                               detail=f"白名单外工具调用被拒绝: {name}")
            raise GuardrailViolation(
                f"工具 {name!r} 不在白名单，调用被拒绝",
                code="GUARD_TOOL_DENIED",
                context={"tool": name},
            )
        result = self._tools[name](*args, **kwargs)
        if self.audit:
            self.audit.log("tool_call", {"tool": name}, {"ok": True},
                           case_id=case_id, event_type="tool_call")
        return result
