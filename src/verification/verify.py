"""三单一致性核验实现。

每项核验输出 FieldCheckResult（pass/fail + 证据引用），汇总为 VerificationResult。
跨案件重复检测（一单多押）需先以 build_item_index/build_serial_index 建索引。
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..schemas import (
    ContractEssentials,
    FieldCheckResult,
    FieldEvidence,
    InvoiceEssentials,
    LeaseItemEssentials,
    VerificationResult,
)

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "verification.yaml"


def load_verify_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else _DEFAULT_CONFIG
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {"amount_tolerance": 1.0}


def normalize_name(name: str) -> str:
    """主体名称规范化：去空白、全角括号转半角、去常见后缀标点差异。"""
    s = re.sub(r"\s+", "", name)
    return s.replace("（", "(").replace("）", ")")


def build_item_index(parsed: dict[str, LeaseItemEssentials]) -> dict[str, set[str]]:
    """租赁物编号 -> 案件集合。"""
    index: dict[str, set[str]] = {}
    for case_id, lease in parsed.items():
        for item in lease.items:
            index.setdefault(item.item_id, set()).add(case_id)
    return index


def build_serial_index(parsed: dict[str, LeaseItemEssentials]) -> dict[str, set[str]]:
    """序列号 -> 案件集合。"""
    index: dict[str, set[str]] = {}
    for case_id, lease in parsed.items():
        for item in lease.items:
            index.setdefault(item.serial_no, set()).add(case_id)
    return index


class _EvidenceLookup:
    """(doc_type, field_name) -> FieldEvidence 查询。"""

    def __init__(self, evidences: list[FieldEvidence]) -> None:
        self._map = {(e.doc_type.value, e.field_name): e for e in evidences}

    def get(self, doc_type: str, *field_names: str) -> list[FieldEvidence]:
        return [self._map[(doc_type, f)] for f in field_names if (doc_type, f) in self._map]


def verify_case(
    case_id: str,
    contract: ContractEssentials,
    invoice: InvoiceEssentials,
    lease: LeaseItemEssentials,
    evidences: list[FieldEvidence],
    *,
    item_index: dict[str, set[str]] | None = None,
    serial_index: dict[str, set[str]] | None = None,
    tolerance: float | None = None,
) -> VerificationResult:
    """执行全部核验项，返回 VerificationResult。"""
    tol = tolerance if tolerance is not None else float(load_verify_config().get("amount_tolerance", 1.0))
    ev = _EvidenceLookup(evidences)
    checks: list[FieldCheckResult] = []

    def add(name: str, passed: bool, detail: str, evs: list[FieldEvidence]) -> None:
        checks.append(FieldCheckResult(check_name=name, passed=passed, detail=detail, evidences=evs))

    # 1. 主体名称一致性（规范化比对）
    c_seller = contract.vendor.name if contract.vendor else ""
    pair = ev.get("contract", "vendor.name") + ev.get("invoice", "seller.name")
    add(
        "contract_vs_invoice.seller_name",
        normalize_name(c_seller) == normalize_name(invoice.seller.name),
        f"合同卖方「{c_seller}」 vs 发票销售方「{invoice.seller.name}」",
        pair,
    )
    pair = ev.get("contract", "lessee.name") + ev.get("invoice", "buyer.name")
    add(
        "contract_vs_invoice.buyer_name",
        normalize_name(contract.lessee.name) == normalize_name(invoice.buyer.name),
        f"合同买方「{contract.lessee.name}」 vs 发票购买方「{invoice.buyer.name}」",
        pair,
    )

    # 2. 金额勾稽（容差可配）
    c_total = contract.total_amount.amount
    i_total = invoice.amount_incl_tax.amount
    l_total = lease.total_value.amount
    add(
        "amount.contract_vs_invoice",
        abs(c_total - i_total) <= tol,
        f"合同 {c_total:,.2f} vs 发票价税合计 {i_total:,.2f}（容差 {tol}）",
        ev.get("contract", "total_amount.amount") + ev.get("invoice", "amount_incl_tax.amount"),
    )
    add(
        "amount.contract_vs_lease",
        abs(c_total - l_total) <= tol,
        f"合同 {c_total:,.2f} vs 清单总价值 {l_total:,.2f}（容差 {tol}）",
        ev.get("contract", "total_amount.amount") + ev.get("lease_items", "total_value.amount"),
    )
    excl_tax = invoice.amount_excl_tax.amount + invoice.tax_amount.amount
    add(
        "invoice.tax_reconciliation",
        abs(excl_tax - i_total) <= tol,
        f"不含税 {invoice.amount_excl_tax.amount:,.2f} + 税额 {invoice.tax_amount.amount:,.2f} "
        f"vs 价税合计 {i_total:,.2f}",
        ev.get("invoice", "amount_excl_tax.amount", "tax_amount.amount", "amount_incl_tax.amount"),
    )

    # 3. 账期一致性：账期≥1 天且开票日期不晚于 签订日期+账期
    days = contract.account_days
    inv_delta = (invoice.invoice_date - contract.sign_date).days
    ok = days is not None and days >= 1 and inv_delta <= days
    add(
        "account_period.consistency",
        ok,
        f"账期 {days} 天；开票距签订 {inv_delta} 天"
        + ("" if ok else "（账期为 0 或开票超账期，交易节奏异常）"),
        ev.get("contract", "account_days", "sign_date") + ev.get("invoice", "invoice_date"),
    )

    # 4. 关联键：清单合同号 == 合同编号
    add(
        "lease.contract_no_link",
        lease.contract_no == contract.contract_no,
        f"清单关联合同号「{lease.contract_no}」 vs 合同编号「{contract.contract_no}」",
        ev.get("lease_items", "contract_no") + ev.get("contract", "contract_no"),
    )

    # 5. 跨案件租赁物重复（一单多押）：编号与序列号
    #    证据口径：无论通过与否，均挂上全部条目的被检字段证据（"已核对登记簿"的可追溯性）
    if item_index is not None:
        dup_items = sorted(
            {it.item_id for it in lease.items if len(item_index.get(it.item_id, set()) - {case_id}) > 0}
        )
        evs: list[FieldEvidence] = []
        for k, it in enumerate(lease.items):
            evs += ev.get("lease_items", f"items.{k}.item_id")
        others = {
            it: sorted(item_index[it] - {case_id}) for it in dup_items
        }
        add(
            "cross_case.item_id_duplicate",
            not dup_items,
            "无跨案件重复租赁物编号" if not dup_items else f"租赁物编号重复登记: {others}",
            evs,
        )
    if serial_index is not None:
        dup_serials = sorted(
            {it.serial_no for it in lease.items if len(serial_index.get(it.serial_no, set()) - {case_id}) > 0}
        )
        evs = []
        for k, it in enumerate(lease.items):
            evs += ev.get("lease_items", f"items.{k}.serial_no")
        others = {sn: sorted(serial_index[sn] - {case_id}) for sn in dup_serials}
        add(
            "cross_case.serial_no_duplicate",
            not dup_serials,
            "无跨案件重复序列号" if not dup_serials else f"序列号重复登记: {others}",
            evs,
        )

    passed = sum(1 for c in checks if c.passed)
    return VerificationResult(
        case_id=case_id, checks=checks, passed_count=passed, failed_count=len(checks) - passed
    )
