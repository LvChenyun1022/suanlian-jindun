"""三单核验（SPEC M3）：主体/金额/账期/关联键一致性 + 跨案件租赁物重复检测。"""
from .verify import (
    build_item_index,
    build_serial_index,
    load_verify_config,
    normalize_name,
    verify_case,
)

__all__ = [
    "build_item_index",
    "build_serial_index",
    "load_verify_config",
    "normalize_name",
    "verify_case",
]
