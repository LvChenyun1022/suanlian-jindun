"""要素解析器：正则优先、LLM 补充，产出 SPEC Pydantic 模型 + 字段级证据。

流程（SPEC M2 / 5.2）：
1. PdfTextReader 提取文本（PyMuPDF 优先，pdfplumber 备用）；
2. 标签正则抽取全部字段（mock 与 live 共用此路径）；
3. 有缺失且为 live 模式时调用 LLM 补抽（失败留审计并按 mock 回退）；
4. 仍缺失或 Pydantic 校验失败 → ParseError 并写审计日志。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from config.settings import LLMSettings, load_settings

from ..audit import AuditLogger
from ..errors import LLMError, ParseError
from ..schemas import (
    ContractEssentials,
    DocType,
    FieldEvidence,
    InvoiceEssentials,
    LeaseItem,
    LeaseItemEssentials,
    MoneyAmount,
    Party,
)
from .llm import llm_fill
from .reader import PdfTextReader, RawHit


@dataclass(frozen=True)
class FieldSpec:
    key: str         # oracle/内部键
    label: str       # PDF 标签
    field_name: str  # 证据字段名（模型点路径）
    kind: str        # str | money | int | float | date


CONTRACT_FIELDS: list[FieldSpec] = [
    FieldSpec("contract_no", "合同编号", "contract_no", "str"),
    FieldSpec("sign_date", "签订日期", "sign_date", "date"),
    FieldSpec("seller_name", "卖方（出卖人）", "vendor.name", "str"),
    FieldSpec("seller_credit_code", "卖方统一社会信用代码", "vendor.credit_code", "str"),
    FieldSpec("buyer_name", "买方（买受人）", "lessee.name", "str"),
    FieldSpec("buyer_credit_code", "买方统一社会信用代码", "lessee.credit_code", "str"),
    FieldSpec("subject", "标的物", "subject", "str"),
    FieldSpec("total_amount", "合同总金额（含税）", "total_amount.amount", "money"),
    FieldSpec("account_days", "账期", "account_days", "int"),
]

INVOICE_FIELDS: list[FieldSpec] = [
    FieldSpec("invoice_no", "发票号码", "invoice_no", "str"),
    FieldSpec("invoice_date", "开票日期", "invoice_date", "date"),
    FieldSpec("seller_name", "销售方名称", "seller.name", "str"),
    FieldSpec("buyer_name", "购买方名称", "buyer.name", "str"),
    FieldSpec("item_name", "货物或应税劳务、服务名称", "item_name", "str"),
    FieldSpec("quantity", "数量", "quantity", "float"),
    FieldSpec("unit_price", "单价（不含税）", "unit_price", "money"),
    FieldSpec("amount_excl_tax", "金额（不含税）", "amount_excl_tax.amount", "money"),
    FieldSpec("tax_amount", "税额", "tax_amount.amount", "money"),
    FieldSpec("amount_incl_tax", "价税合计（含税）", "amount_incl_tax.amount", "money"),
]

LEASE_SCALAR_FIELDS: list[FieldSpec] = [
    FieldSpec("list_no", "清单编号", "list_no", "str"),
    FieldSpec("contract_no", "关联合同编号", "contract_no", "str"),
    FieldSpec("delivery_date", "交付日期", "items.delivery_date", "date"),
    FieldSpec("total_value", "清单总价值", "total_value.amount", "money"),
]

ITEM_FIELD_PREFIXES: list[tuple[str, str, str, str]] = [
    ("item_id", "租赁物编号", "items.{k}.item_id", "str"),
    ("model", "GPU型号", "items.{k}.model", "str"),
    ("serial_no", "序列号", "items.{k}.serial_no", "str"),
    ("quantity", "数量", "items.{k}.quantity", "int"),
    ("unit_price", "单价", "items.{k}.unit_price", "money"),
    ("total", "总价", "items.{k}.purchase_price.amount", "money"),
]

# 各单据必填键（缺失即 ParseError；live 模式先尝试 LLM 补抽）
REQUIRED = {
    DocType.CONTRACT: {f.key for f in CONTRACT_FIELDS},
    DocType.INVOICE: {f.key for f in INVOICE_FIELDS},
    DocType.LEASE_ITEMS: {f.key for f in LEASE_SCALAR_FIELDS} | {"items"},
}

_DOC_NAMES = {
    DocType.CONTRACT: "购销合同",
    DocType.INVOICE: "增值税专用发票",
    DocType.LEASE_ITEMS: "租赁物（GPU）清单",
}


def convert(raw: str, kind: str, key: str) -> object:
    """原始字符串 -> 目标类型；失败抛 ParseError。"""
    try:
        if kind == "str":
            return raw
        if kind == "date":
            return date.fromisoformat(raw.strip())
        if kind in ("money", "float"):
            return float(re.sub(r"[,元\s]", "", raw))
        if kind == "int":
            m = re.search(r"-?\d+", raw.replace(",", ""))
            if not m:
                raise ValueError(raw)
            return int(m.group())
    except (ValueError, TypeError) as e:
        raise ParseError(
            f"字段 {key} 格式无法转换: {raw!r}", code="PARSE_FIELD_FORMAT", context={"field": key, "raw": raw}
        ) from e
    raise ParseError(f"未知字段类型 {kind}", code="PARSE_FIELD_FORMAT", context={"field": key})


class _DocParser:
    def __init__(
        self,
        path: str | Path,
        doc_type: DocType,
        settings: LLMSettings,
        audit: AuditLogger | None,
        source_file: str | None = None,
    ) -> None:
        self.reader = PdfTextReader(path)
        self.doc_type = doc_type
        self.settings = settings
        self.audit = audit
        self.source_file = source_file or Path(path).name
        self.evidences: list[FieldEvidence] = []

    def _evidence(self, hit: RawHit, field_name: str) -> FieldEvidence:
        ev = FieldEvidence(
            field_name=field_name,
            page=hit.page,
            excerpt=hit.excerpt,
            bbox=hit.bbox,
            doc_type=self.doc_type,
            source_file=self.source_file,
        )
        self.evidences.append(ev)
        return ev

    def extract_scalars(self, specs: list[FieldSpec]) -> dict[str, object]:
        raw: dict[str, RawHit] = {}
        for spec in specs:
            hit = self.reader.find(spec.label)
            if hit:
                raw[spec.key] = hit
        missing = [s for s in specs if s.key not in raw]
        if missing:
            self._llm_backfill(raw, [s.key for s in missing])
        still_missing = [s.key for s in specs if s.key not in raw]
        if still_missing:
            raise ParseError(
                f"{_DOC_NAMES[self.doc_type]} 缺失必填字段: {still_missing}",
                code="PARSE_FIELD_MISSING",
                context={"doc_type": self.doc_type.value, "fields": still_missing,
                         "file": self.source_file},
            )
        values: dict[str, object] = {}
        for spec in specs:
            hit = raw[spec.key]
            values[spec.key] = convert(hit.value, spec.kind, spec.key)
            self._evidence(hit, spec.field_name)
        return values

    def _llm_backfill(self, raw: dict[str, RawHit], missing_keys: list[str]) -> None:
        """live 模式下 LLM 补抽；任何失败按 mock 回退（记录审计，不抛出）。"""
        if self.settings.mock_mode:
            return
        try:
            filled = llm_fill(self.doc_type.value, self.reader.full_text(), missing_keys, self.settings)
        except LLMError as e:
            if self.audit:
                self.audit.log("parsing.llm_fallback", {"file": self.source_file}, e.to_log())
            return
        for key, value in filled.items():
            if key in missing_keys and key not in raw:
                hit = self.reader.locate_value(value)
                if hit:
                    raw[key] = hit
        if self.audit and filled:
            self.audit.log("parsing.llm_fill", {"file": self.source_file, "missing": missing_keys}, filled)

    def extract_items(self) -> list[dict[str, object]]:
        columns: dict[str, dict[int, RawHit]] = {}
        for key, prefix, _fn, _kind in ITEM_FIELD_PREFIXES:
            columns[key] = self.reader.find_indexed(prefix)
        n = max((len(c) for c in columns.values()), default=0)
        if n == 0:
            raise ParseError(
                "租赁物清单无明细条目", code="PARSE_FIELD_MISSING",
                context={"doc_type": self.doc_type.value, "fields": ["items"], "file": self.source_file},
            )
        items: list[dict[str, object]] = []
        for k in range(n):
            row: dict[str, object] = {}
            for key, _prefix, field_name, kind in ITEM_FIELD_PREFIXES:
                hit = columns[key].get(k)
                if hit is None:
                    raise ParseError(
                        f"租赁物第 {k + 1} 条缺失 {key}", code="PARSE_FIELD_MISSING",
                        context={"doc_type": self.doc_type.value, "fields": [f"items.{k}.{key}"],
                                 "file": self.source_file},
                    )
                row[key] = convert(hit.value, kind, f"items.{k}.{key}")
                self._evidence(hit, field_name.format(k=k))
            items.append(row)
        return items


def _build_model(doc_type: DocType, scalars: dict, items: list[dict] | None):
    if doc_type is DocType.CONTRACT:
        return ContractEssentials(
            contract_no=scalars["contract_no"],
            sign_date=scalars["sign_date"],
            lessor=None,  # 购销合同腿不载明出租人（SPEC v0.2）
            vendor=Party(name=scalars["seller_name"], credit_code=scalars["seller_credit_code"], role="vendor"),
            lessee=Party(name=scalars["buyer_name"], credit_code=scalars["buyer_credit_code"], role="lessee"),
            total_amount=MoneyAmount(amount=scalars["total_amount"]),
            account_days=scalars["account_days"],
            subject=scalars["subject"],
        )
    if doc_type is DocType.INVOICE:
        return InvoiceEssentials(
            invoice_no=scalars["invoice_no"],
            invoice_date=scalars["invoice_date"],
            seller=Party(name=scalars["seller_name"], role="vendor"),
            buyer=Party(name=scalars["buyer_name"], role="lessee"),
            item_name=scalars["item_name"],
            quantity=scalars["quantity"],
            unit_price=scalars["unit_price"],
            amount_excl_tax=MoneyAmount(amount=scalars["amount_excl_tax"]),
            tax_amount=MoneyAmount(amount=scalars["tax_amount"]),
            amount_incl_tax=MoneyAmount(amount=scalars["amount_incl_tax"]),
        )
    assert items is not None
    delivery = scalars["delivery_date"]
    return LeaseItemEssentials(
        list_no=scalars["list_no"],
        contract_no=scalars["contract_no"],
        items=[
            LeaseItem(
                item_id=row["item_id"],
                model=row["model"],
                category="gpu",
                serial_no=row["serial_no"],
                quantity=row["quantity"],
                purchase_price=MoneyAmount(amount=row["total"]),
                delivery_date=delivery,
            )
            for row in items
        ],
        total_value=MoneyAmount(amount=scalars["total_value"]),
    )


_SCALAR_SPECS = {
    DocType.CONTRACT: CONTRACT_FIELDS,
    DocType.INVOICE: INVOICE_FIELDS,
    DocType.LEASE_ITEMS: LEASE_SCALAR_FIELDS,
}


def parse_document(
    path: str | Path,
    doc_type: DocType | str,
    settings: LLMSettings | None = None,
    audit: AuditLogger | None = None,
    source_file: str | None = None,
) -> tuple[object, list[FieldEvidence]]:
    """解析单份 PDF 为要素模型 + 字段级证据。

    Raises:
        ParseError: 字段缺失/格式错误/模型校验失败（已写审计日志）。
    """
    dt = DocType(doc_type)
    s = settings or load_settings()
    try:
        parser = _DocParser(path, dt, s, audit, source_file)
    except Exception as e:
        err = ParseError(
            f"无法读取 PDF: {type(e).__name__}: {e}",
            code="PARSE_UNREADABLE",
            context={"file": str(path), "doc_type": dt.value},
        )
        if audit:
            audit.log("parsing.error", {"file": str(path), "doc_type": dt.value},
                      {"error": err.to_log()})
        raise err from e
    try:
        scalars = parser.extract_scalars(_SCALAR_SPECS[dt])
        items = parser.extract_items() if dt is DocType.LEASE_ITEMS else None
        try:
            model = _build_model(dt, scalars, items)
        except ValidationError as e:
            raise ParseError(
                f"{_DOC_NAMES[dt]} 要素模型校验失败: {e.error_count()} 个错误",
                code="PARSE_VALIDATION",
                context={"doc_type": dt.value, "file": parser.source_file,
                         "errors": e.errors(include_url=False)},
            ) from e
    except ParseError as e:
        if audit:
            audit.log("parsing.error", {"file": parser.source_file, "doc_type": dt.value},
                      {"error": e.to_log(), "context": e.context})
        raise
    finally:
        parser.reader.close()
    if audit:
        audit.log("parsing", {"file": parser.source_file, "doc_type": dt.value},
                  {"model": getattr(model, "model_dump", lambda: str(model))(),
                   "backend": parser.reader.backend})
    return model, parser.evidences


def parse_case(
    files: dict[str, str],
    base_dir: str | Path = ".",
    settings: LLMSettings | None = None,
    audit: AuditLogger | None = None,
) -> tuple[ContractEssentials, InvoiceEssentials, LeaseItemEssentials, list[FieldEvidence]]:
    """解析一个案件的三份单据。files: {"contract": rel, "invoice": rel, "lease_items": rel}。"""
    base = Path(base_dir)
    s = settings or load_settings()
    contract, ev1 = parse_document(base / files["contract"], DocType.CONTRACT, s, audit, files["contract"])
    invoice, ev2 = parse_document(base / files["invoice"], DocType.INVOICE, s, audit, files["invoice"])
    lease, ev3 = parse_document(base / files["lease_items"], DocType.LEASE_ITEMS, s, audit, files["lease_items"])
    return contract, invoice, lease, ev1 + ev2 + ev3  # type: ignore[return-value]
