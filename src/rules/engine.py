"""77号文规则执行器：读取 YAML 规则定义，按 condition.type 解释执行。

每条命中输出 RuleHit（规则编号 + 条款引用 + 证据，SPEC M4）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import yaml

from ..schemas import (
    ContractEssentials,
    FieldEvidence,
    InvoiceEssentials,
    LeaseItemEssentials,
    RuleHit,
    VerificationResult,
)

_DEFAULT_RULES = Path(__file__).resolve().parent.parent.parent / "config" / "rules_77.yaml"


@dataclass
class CaseSummary:
    """跨案件规则（R77-004）所需的案件摘要。"""

    case_id: str
    buyer: str
    seller: str
    sign_date: date
    total_amount: float


@dataclass
class CaseContext:
    """单案件规则评估上下文。"""

    case_id: str
    contract: ContractEssentials
    invoice: InvoiceEssentials
    lease_items: LeaseItemEssentials
    verification: VerificationResult
    evidences: list[FieldEvidence] = field(default_factory=list)
    item_index: dict[str, set[str]] | None = None      # 租赁物编号 -> 案件集合（模拟动产登记）
    serial_index: dict[str, set[str]] | None = None    # 序列号 -> 案件集合
    all_cases: list[CaseSummary] = field(default_factory=list)  # 全量案件摘要（R77-004）

    def ev(self, doc_type: str, *field_names: str) -> list[FieldEvidence]:
        m = {(e.doc_type.value, e.field_name): e for e in self.evidences}
        return [m[(doc_type, f)] for f in field_names if (doc_type, f) in m]


def load_rules(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else _DEFAULT_RULES
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["rules"]


# ---------- 条件函数：命中返回 (detail, evidences)，未命中返回 None ----------

def _cond_account_days_gt(ctx: CaseContext, params: dict) -> tuple[str, list[FieldEvidence]] | None:
    days = ctx.contract.account_days
    threshold = int(params["days"])
    if days is not None and days > threshold:
        return (
            f"账期 {days} 天 > {threshold} 天（合同 {ctx.contract.contract_no}）",
            ctx.ev("contract", "account_days", "sign_date"),
        )
    return None


def _cond_verification_failed(ctx: CaseContext, _params: dict) -> tuple[str, list[FieldEvidence]] | None:
    failed = [c for c in ctx.verification.checks if not c.passed]
    if not failed:
        return None
    evs = [e for c in failed for e in c.evidences][:8]
    detail = "；".join(f"[{c.check_name}] {c.detail}" for c in failed[:4])
    return (f"{len(failed)} 项核验未通过: {detail}", evs)


def _cond_split_amounts(ctx: CaseContext, params: dict) -> tuple[str, list[FieldEvidence]] | None:
    threshold = float(params["threshold"])
    proximity = float(params["proximity"])
    window = int(params["window_days"])
    min_count = int(params["min_count"])
    lo, hi = threshold * proximity, threshold

    self_sum = next((c for c in ctx.all_cases if c.case_id == ctx.case_id), None)
    if self_sum is None or not (lo <= self_sum.total_amount < hi):
        return None
    hits_detail: list[str] = []
    for role in ("buyer", "seller"):
        name = getattr(self_sum, role)
        peers = [
            c for c in ctx.all_cases
            if c.case_id != ctx.case_id
            and getattr(c, role) == name
            and abs((c.sign_date - self_sum.sign_date).days) <= window
            and lo <= c.total_amount < hi
        ]
        if len(peers) + 1 >= min_count:
            refs = "、".join(f"{p.case_id}({p.total_amount:,.0f}元)" for p in peers)
            hits_detail.append(
                f"主体「{name}」{window} 天内 {len(peers) + 1} 笔接近阈值 {threshold:,.0f} 元: 本案 + {refs}"
            )
    if not hits_detail:
        return None
    return ("；".join(hits_detail), ctx.ev("contract", "total_amount.amount", "lessee.name", "sign_date"))


def _cond_registry_conflict(ctx: CaseContext, _params: dict) -> tuple[str, list[FieldEvidence]] | None:
    if ctx.item_index is None and ctx.serial_index is None:
        return None
    conflicts: list[str] = []
    evs: list[FieldEvidence] = []
    for k, item in enumerate(ctx.lease_items.items):
        id_others = sorted((ctx.item_index or {}).get(item.item_id, set()) - {ctx.case_id})
        sn_others = sorted((ctx.serial_index or {}).get(item.serial_no, set()) - {ctx.case_id})
        if id_others or sn_others:
            parts = []
            if id_others:
                parts.append(f"编号 {item.item_id} 已登记于 {'、'.join(id_others)}")
            if sn_others:
                parts.append(f"序列号 {item.serial_no} 已登记于 {'、'.join(sn_others)}")
            conflicts.append(f"租赁物（{k + 1}）" + "；".join(parts))
            evs += ctx.ev("lease_items", f"items.{k}.item_id", f"items.{k}.serial_no")
    if not conflicts:
        return None
    return ("；".join(conflicts), evs)


_CONDITIONS: dict[str, Callable[[CaseContext, dict], tuple[str, list[FieldEvidence]] | None]] = {
    "account_days_gt": _cond_account_days_gt,
    "verification_failed": _cond_verification_failed,
    "split_amounts": _cond_split_amounts,
    "registry_conflict": _cond_registry_conflict,
}


def evaluate_rules(ctx: CaseContext, rules: list[dict] | None = None) -> list[RuleHit]:
    """对单案件解释执行全部规则，返回命中列表。"""
    hits: list[RuleHit] = []
    for rule in rules if rules is not None else load_rules():
        cond = rule["condition"]
        func = _CONDITIONS.get(cond["type"])
        if func is None:
            raise ValueError(f"未知规则条件类型: {cond['type']}（{rule['id']}）")
        params = {k: v for k, v in cond.items() if k != "type"}
        result = func(ctx, params)
        if result is None:
            continue
        detail, evidences = result
        if not evidences:
            # 证据兜底：命中必须携带证据（SPEC RuleHit.evidences 非空）
            evidences = ctx.ev("contract", "contract_no")
        hits.append(
            RuleHit(
                rule_id=rule["id"],
                clause_ref=rule["clause_ref"],
                severity=rule["severity"],
                description=rule["description"],
                evidences=evidences,
                detail=detail,
            )
        )
    return hits
