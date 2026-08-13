"""全部数据 schema 的 Pydantic v2 模型（SPEC.md 第 3 节的实现）。

与 SPEC 的差异（已记入 SPEC 修订记录 v0.2）：
- ContractEssentials.lessor 改为可选（购销合同腿不载明出租人，出租人为本系统使用方）；
- ContractEssentials.lease_term_months 改为可选，新增可选字段 account_days / subject；
- 其余字段名与 SPEC 完全一致。
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------- 通用 ----------

class DocType(str, Enum):
    CONTRACT = "contract"        # 购销合同
    INVOICE = "invoice"          # 发票
    LEASE_ITEMS = "lease_items"  # 租赁物清单


class BBox(BaseModel):
    """页面坐标（PDF 用户空间，左下原点，单位 pt）。"""

    x0: float
    y0: float
    x1: float
    y1: float


class FieldEvidence(BaseModel):
    """字段级证据：每个被抽取字段必须携带。"""

    field_name: str          # 要素模型字段名（点路径，如 "vendor.name"）
    page: int = Field(ge=1)  # 1-based 页码
    excerpt: str             # 原文片段（原样截取）
    bbox: BBox | None = None
    doc_type: DocType
    source_file: str         # 来源 PDF 相对路径


class Party(BaseModel):
    name: str                # 虚构企业/个人名
    credit_code: str | None = None  # 掩码统一社会信用代码
    role: Literal["lessor", "lessee", "vendor", "guarantor"]


class MoneyAmount(BaseModel):
    amount: float = Field(ge=0)
    currency: Literal["CNY"] = "CNY"


# ---------- 单据要素 ----------

class ContractEssentials(BaseModel):
    """购销合同要素（v0.2：lessor/lease_term_months 可选；新增 account_days/subject）。"""

    contract_no: str
    sign_date: date
    lessor: Party | None = None    # 出租人（购销合同腿不载明）
    lessee: Party                  # 买方（买受人/融资申请人）
    vendor: Party | None = None    # 卖方（出卖人）
    total_amount: MoneyAmount      # 合同总金额（含税）
    lease_term_months: int | None = Field(default=None, gt=0)
    rent_schedule: list[MoneyAmount] = []
    deposit: MoneyAmount | None = None
    is_sale_leaseback: bool = False
    account_days: int | None = Field(default=None, ge=0)  # 账期天数（v0.2 新增）
    subject: str | None = None                            # 标的物（v0.2 新增）


class InvoiceEssentials(BaseModel):
    """发票要素。"""

    invoice_no: str
    invoice_date: date
    seller: Party
    buyer: Party
    item_name: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    amount_excl_tax: MoneyAmount
    tax_amount: MoneyAmount
    amount_incl_tax: MoneyAmount   # excl + tax ≈ incl（核验勾稽点）


class LeaseItem(BaseModel):
    item_id: str
    model: str
    category: Literal["gpu", "server", "network", "storage", "other"]
    serial_no: str                 # 一单多押检测键
    quantity: int = Field(gt=0)
    purchase_price: MoneyAmount    # 条目总价
    delivery_date: date | None = None


class LeaseItemEssentials(BaseModel):
    """租赁物清单要素。"""

    list_no: str
    contract_no: str               # 关联合同号（三单核验关联键）
    items: list[LeaseItem]
    total_value: MoneyAmount


# ---------- 核验与规则 ----------

class FieldCheckResult(BaseModel):
    """单项交叉核验结论。"""

    check_name: str
    passed: bool
    detail: str
    evidences: list[FieldEvidence] = []


class VerificationResult(BaseModel):
    """三单核验结果。"""

    case_id: str
    checks: list[FieldCheckResult]
    passed_count: int
    failed_count: int

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0


class RuleHit(BaseModel):
    """规则命中。"""

    rule_id: str                   # 如 "R77-003"
    clause_ref: str                # 条款引用
    severity: Literal["block", "high", "medium", "low"]
    description: str
    evidences: list[FieldEvidence]  # 命中证据，非空
    detail: str = ""               # 命中说明（命中值/涉及案件等）


# ---------- 压力测试 / 预警 / 评分（后续阶段使用） ----------

class ScenarioResult(BaseModel):
    scenario: Literal["base", "stress", "extreme"]
    residual_value_ratio: float
    ltv: float
    dscr: float
    breach: bool
    detail: str = ""             # v0.3 新增：情景说明


class ResidualStressResult(BaseModel):
    case_id: str
    gpu_model: str
    depreciation_curve: list[float]
    scenarios: list[ScenarioResult]
    payback_months: float | None = None   # v0.3 新增：回本周期（月）


class UtilizationAlert(BaseModel):
    case_id: str
    # v0.3：新增 "sudden_drop"（环比骤降）
    alert_type: Literal["long_idle", "zero_delivery", "rent_divergence", "sudden_drop"]
    level: Literal["red", "orange", "yellow"]
    window: str
    detail: str
    metric_value: float


class ScoreComponent(BaseModel):
    name: Literal["verification", "rules", "stress", "utilization"]
    weight: float
    raw: float
    contribution: float


class RiskScore(BaseModel):
    case_id: str
    total: float = Field(ge=0, le=100)
    components: list[ScoreComponent]
    grade: Literal["pass", "review", "reject"]
    reasons: list[str] = []      # v0.3 新增：路由理由（review/reject 时非空）


# ---------- 审计日志 ----------


class ValidationFlag(BaseModel):
    """字段级交叉校验标记（v3）：解析层之后统一 validation 阶段的输出。

    severity="review" → 该字段置信度置 0，转人审路由（与 ocr_low_confidence 同路由）；
    severity="info"   → 仅记录（如无法交叉校验），不惩罚。
    """

    field_name: str                # 要素字段（如 contract.total_amount）
    reason_code: Literal[
        "amount_mismatch_daxie",        # 大写/小写金额不一致
        "amount_parse_failed",          # 写法存在但解析失败
        "amount_crosscheck_match",      # 交叉校验通过（info）
        "amount_crosscheck_unavailable",  # 只有一种写法，无法交叉（info）
        "term_out_of_bounds",           # 期限越出有效区间
        "term_inconsistent",            # 期限多值冲突或与起止日期矛盾
        "term_parse_failed",            # 期限文本无法解析为有效数字
    ]
    severity: Literal["review", "info"]
    detail: str
    raw_masked: str = ""           # 原始值（掩码）


class AuditLogRecord(BaseModel):
    """审计日志记录（哈希链）。"""

    seq: int = Field(ge=0)
    timestamp: datetime
    stage: str
    run_mode: Literal["mock", "live"]
    input_digest: str              # sha256 hex
    output_digest: str             # sha256 hex
    prev_hash: str                 # 首条为 "0"*64
    record_hash: str               # sha256(prev_hash + canonical_payload)

    @staticmethod
    def compute_hash(prev_hash: str, canonical_payload: str) -> str:
        return hashlib.sha256((prev_hash + canonical_payload).encode("utf-8")).hexdigest()


# ---------- 评测集标签 ----------

class FraudPattern(str, Enum):
    A_CHENGXING = "a_chengxing"        # 承兴系：伪造合同/单据、假冒对手方
    B_MULTI_PLEDGE = "b_multi_pledge"  # 一单多押：同一租赁物重复融资
    C_CIRCULAR = "c_circular_trade"    # 空转贸易：无真实交付的循环合同


# ---------- Pipeline 状态（SPEC 4.2） ----------

class PipelineState(BaseModel):
    """环节间传递的完整状态。各环节只写自己负责的字段。"""

    model_config = {"arbitrary_types_allowed": True}

    case_id: str
    run_mode: Literal["mock", "live"]
    files: dict[str, str]                       # DocType value -> PDF 相对路径

    contract: ContractEssentials | None = None
    invoice: InvoiceEssentials | None = None
    lease_items: LeaseItemEssentials | None = None
    evidences: list[FieldEvidence] = []

    verification: VerificationResult | None = None
    rule_hits: list[RuleHit] = []
    validation_flags: list[ValidationFlag] = []   # v3 新增：字段级交叉校验标记
    stress: ResidualStressResult | None = None
    alerts: list[UtilizationAlert] = []
    risk_score: RiskScore | None = None

    utilization_series: list[float] = []        # 合成遥测（mock 馈入）
    report_path: str | None = None
    report_html_path: str | None = None         # v0.3 新增
    audit_zip_path: str | None = None           # v0.3 新增
    stage_timings: dict[str, float] = {}        # v0.4 新增：各环节耗时（秒）
    errors: list[str] = []                      # 结构化异常的降级记录
