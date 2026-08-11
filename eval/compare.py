"""解析准确率对照：oracle（labels.jsonl） vs 解析模型，字段级 exact-match。

数值规范化：去逗号/"元"后按 float 两位小数比对；其余按去空白字符串比对。
"""
from __future__ import annotations

import re
from typing import Any

# 各单据参与评比的 oracle 字段（与解析模型可对应的字段全集）
COMPARE_KEYS = {
    "contract": [
        "contract_no", "sign_date", "seller_name", "seller_credit_code",
        "buyer_name", "buyer_credit_code", "subject", "total_amount", "account_days",
    ],
    "invoice": [
        "invoice_no", "invoice_date", "seller_name", "buyer_name", "item_name",
        "quantity", "unit_price", "amount_excl_tax", "tax_amount", "amount_incl_tax",
    ],
    "lease_items": ["list_no", "contract_no", "delivery_date", "total_value"],
}


def get_parsed_value(model: Any, doc_type: str, key: str) -> Any:
    """按 oracle 键从解析模型取值。"""
    if key.startswith("items."):
        _prefix, k, sub = key.split(".")
        item = model.items[int(k)]
        if sub == "item_id":
            return item.item_id
        if sub == "model":
            return item.model
        if sub == "serial_no":
            return item.serial_no
        if sub == "quantity":
            return item.quantity
        if sub == "unit_price":
            return None  # oracle 单价为含税单价，模型未存该字段，不参与评比
        if sub == "total":
            return item.purchase_price.amount
        raise KeyError(key)
    if doc_type == "contract":
        m = {
            "contract_no": model.contract_no,
            "sign_date": model.sign_date.isoformat(),
            "seller_name": model.vendor.name if model.vendor else None,
            "seller_credit_code": model.vendor.credit_code if model.vendor else None,
            "buyer_name": model.lessee.name,
            "buyer_credit_code": model.lessee.credit_code,
            "subject": model.subject,
            "total_amount": model.total_amount.amount,
            "account_days": model.account_days,
        }
    elif doc_type == "invoice":
        m = {
            "invoice_no": model.invoice_no,
            "invoice_date": model.invoice_date.isoformat(),
            "seller_name": model.seller.name,
            "buyer_name": model.buyer.name,
            "item_name": model.item_name,
            "quantity": model.quantity,
            "unit_price": model.unit_price,
            "amount_excl_tax": model.amount_excl_tax.amount,
            "tax_amount": model.tax_amount.amount,
            "amount_incl_tax": model.amount_incl_tax.amount,
        }
    else:
        m = {
            "list_no": model.list_no,
            "contract_no": model.contract_no,
            "delivery_date": model.items[0].delivery_date.isoformat() if model.items else None,
            "total_value": model.total_value.amount,
        }
    return m[key]


def _num(s: str) -> float | None:
    """提取字符串中的首个数值（容忍逗号、"元"/"天"等单位）。"""
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return round(float(m.group().replace(",", "")), 2)
    except ValueError:
        return None


def values_equal(oracle_value: str, parsed_value: Any) -> bool:
    if parsed_value is None:
        return False
    a, b = oracle_value.strip(), str(parsed_value).strip()
    if a == b:
        return True
    na, nb = _num(a), _num(b)
    return na is not None and nb is not None and na == nb


def iter_comparable_fields(oracle_doc: dict, doc_type: str):
    """产出 (key, oracle_value)：标量字段 + 明细条目字段（跳过不参与评比的单价）。"""
    fields = oracle_doc["fields"]
    for key in COMPARE_KEYS[doc_type]:
        if key in fields:
            yield key, fields[key]["value"]
    if doc_type == "lease_items":
        for key, info in fields.items():
            if key.startswith("items.") and not key.endswith(".unit_price"):
                yield key, info["value"]


def score_case(oracle: dict, parsed: dict[str, Any]) -> tuple[int, int, dict[str, list[str]]]:
    """返回 (匹配数, 总数, 各单据不匹配字段列表)。"""
    matched = total = 0
    misses: dict[str, list[str]] = {}
    for doc_type, model in parsed.items():
        for key, oracle_value in iter_comparable_fields(oracle[doc_type], doc_type):
            total += 1
            if values_equal(oracle_value, get_parsed_value(model, doc_type, key)):
                matched += 1
            else:
                misses.setdefault(doc_type, []).append(key)
    return matched, total, misses
