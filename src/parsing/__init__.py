"""单据解析（SPEC M2）：PyMuPDF 提取 + 正则优先/LLM 补充 + 字段级证据。"""
from .parser import parse_document, parse_case
from .reader import PdfTextReader

__all__ = ["parse_document", "parse_case", "PdfTextReader"]
