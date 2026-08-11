"""合成数据生成（SPEC M1）。

用 faker(zh_CN) + f-string 模板 + reportlab(CID 中文字体) 生成三类数字文本 PDF：
购销合同 / 增值税专用发票 / 租赁物（GPU）清单，并同步产出真值标签 JSONL。
所有数据均为程序合成的虚构数据，敏感字段一律掩码（SPEC 第 1 节系统边界）。
"""

from .cases import CaseFactory, CaseSpec, DocSpec, ItemSpec

__all__ = ["CaseFactory", "CaseSpec", "DocSpec", "ItemSpec"]
