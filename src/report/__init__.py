"""证据链报告（SPEC M8）：Markdown + HTML + 审计包 zip 导出。

接口面向阶段⑤ Streamlit 前端：build_report() 返回预览文本与路径，
export_audit_package() 返回 zip 路径供下载。
"""
from .report import build_report, export_audit_package

__all__ = ["build_report", "export_audit_package"]
