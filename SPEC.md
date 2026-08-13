# SPEC — suanlian-jindun（算链金盾）：算力融资租赁智能风控演示系统

> 版本：v0.8（外部效度 v2/v3：OCR 可选链路 + 字段级交叉校验）
> 本文档是后续所有实现阶段的唯一规格依据。接口、schema、指标口径以本文为准。

### 修订记录

- **v0.8**（外部效度 v2/v3，2026-08-13）：
  - **OCR 可选链路**（v2）：`src/parsing/ocr.py`——PaddleOCR 中文模型、250DPI、逐页写穿缓存、
    关键页选择、行置信度 <0.80 字段转人工（`ocr_low_confidence`）；默认关闭，仅
    `eval/run_external.py --ocr` 或 `ENABLE_OCR=1` 启用；未安装 paddleocr 行为不变。
    `requirements-optional.txt` 固定 `paddlepaddle==3.2.2`（3.3.x 有已知 CPU 推理 bug）。
  - **字段级交叉校验**（v3）：`src/parsing/chinese_amount.py`（中文大写金额/阿拉伯金额解析，
    0 token）+ `src/validation/field_validation.py`（统一 validation 阶段：金额大写/小写交叉、
    期限边界 [1,120] 月可配置于 `config/settings.py`、多值冲突与起止日期一致性）；
    review 级标记 = 字段置信度置 0 转人审（`amount_mismatch_daxie` / `amount_parse_failed` /
    `term_out_of_bounds` / `term_inconsistent` / `term_parse_failed`），绝不静默替换值；
    info 级记录（`amount_crosscheck_match` / `amount_crosscheck_unavailable`）不惩罚。
  - schema 新增 `ValidationFlag`；`PipelineState` 新增 `validation_flags`；
    pipeline 新增 `stage_validate`（解析层之后，见 4.3）；审计日志记录原始值掩码；
    Streamlit 人审面板显示原因码。
  - 外部效度结果：v1 纯文本层 0/23；v2 OCR 24/34（71%）；v3 在 v2 基础上 contract_C
    `term_months` 由静默错值（OCR 144→44）转为 `term_inconsistent` 拦截转人审（真阳），
    contract_B 180 月触发 `term_out_of_bounds`（假阳·规则边界，已人工核对记录）。
    报告：`eval/results/external_validity{,_v2,_v3}.{md,json}`（v1 口径复跑逐字段冻结一致）。

- **v0.7**（文档与提交材料阶段）：
  - 交付 README（合规红线/架构/真实评测表/已知局限）、`docs/compliance.md`（监管条款→功能对照）、
    `docs/demo_script.md`（3 分钟路演）、`docs/plan_draft.md`（四章项目书骨架，市场数字均标"待核实"）。

- **v0.6**（消融基线有效性复核）：
  - `eval/baseline.py` 升级 v2-fixed-2026-08-11（冻结）：严格 JSON 输出（`{"is_fraud","confidence","evidence"}`）、
    "无充分证据必须判正常"、temperature=0、max_tokens=300、`response_format=json_object`；
    解析失败/空响应/重试后仍失败一律 `invalid`，不默认映射为 fraud/normal；逐案完整记录持久化。
  - 新增 `eval/rerun_baseline.py`：并发 2、指数退避+jitter（2/4/8/16s，最多 3 次）、写穿缓存续跑、
    逐案审计 `eval/results/baseline_audit.jsonl`、sanity gate（单一类别输出或 invalid>0 → 提升记 invalid；
    基线召回 100% → saturated/not informative，补 F1/精确率/FPR/BA/MCC）。
  - `eval/run_eval.py` 新增 `--rerun-baseline-only`；invalid 从指标分母剔除；`passed.ablation_lift` 须过 sanity gate。
  - 修复后 live 基线（100 案、0 invalid）：召回 36.67%/FPR 1.43%/精确率 91.67%/F1 0.5238；
    消融提升 +63.3pp（valid）✅。修复前结果保留于 `eval_results_before_baseline_fix.*`，未覆盖。

- **v0.5**（评测阶段）：
  - `eval/run_eval.py` 全指标评测（口径固定于该文件：欺诈判定阈值 60、期望规则集合按标签推定）；
    `eval/baseline.py` 消融基线（BASELINE_VERSION=v1-fixed-2026-08-11，冻结）。
  - `run_pipeline` 新增 `guard_llm` 开关：批量评测关闭护栏 LLM 二次判定（规则库检测仍生效），交互场景默认开启。
  - 核验的跨案件检查项（通过时）也挂全部条目证据，证据链覆盖率口径 = 核验结论与规则命中中带证据比例。
  - live 实测发现：真实 LLM 消融基线退化为"逢案必报"（召回 100%/误报 100%），SPEC 指标 9 在 live 口径
    不达标（+0.0pp），mock 口径达标（+66.7pp）；如实记录于 README 与 eval/results_live。

- **v0.4**（Streamlit Demo 阶段）：
  - M11 实现为 `app/streamlit_app.py`（仅 localhost，见 `.streamlit/config.toml`）；`PipelineState` 新增 `stage_timings` 可选字段。
  - `SqliteAuditStore` 新增 `list_case_events`（时间线查询）；人工复核操作以 `manual_op` 事件写入审计链。
  - 预览适配：`package.json` + `scripts/dev.js` 将 `npm run dev -- --host/--port` 转发至 Streamlit（强制回环地址）。

- **v0.3**（Pipeline + 资产/预警/评分 + 审计与护栏阶段）：
  - M5 实现路径为 `src/asset`（原规划名 `src/stress`）；M6 为 `src/monitoring`。
  - `UtilizationAlert.alert_type` 新增 `"sudden_drop"`（环比骤降）。
  - `ScenarioResult` 新增 `detail`；`ResidualStressResult` 新增 `payback_months`；`RiskScore` 新增 `reasons`（均为带默认值的可选字段）。
  - `PipelineState` 落地于 `src/schemas.py`（新增 `report_html_path`、`audit_zip_path` 可选字段；`files` 键为 DocType 值字符串）。
  - 审计升级为 SQLite append-only 存储（`src/audit/sqlite_store.py`，UPDATE/DELETE 触发器禁止）；JSONL 版保留用于阶段②③与按案件导出。
  - 评分含红线兜底（config/scoring.yaml `overrides`）：high 命中总分 ≥60 强制人审，block 命中 ≥91 建议拒绝。
  - 压力测试本金摊还采用与残值曲线匹配的气球结构假设；极端情景在 100% 单客户集中度下恒突破（结构性结论）。
  - LangGraph 编排实现为 `src/pipeline_langgraph.py`（惰性导入；未安装 langgraph 不影响运行）。

- **v0.2**（解析核验规则阶段）：
  - `ContractEssentials.lessor` 改为可选（购销合同腿不载明出租人，出租人为本系统使用方）；`lease_term_months` 改为可选；新增可选字段 `account_days`（账期天数）、`subject`（标的物）。
  - `RuleHit` 新增 `detail: str = ""`（命中说明）。
  - 核心依赖新增 `pyyaml`（rules_77.yaml / verification.yaml 解析）。
  - M1 实现路径为 `src/datagen`；M2/M3/M4 实现路径为 `src/parsing`、`src/verification`、`src/rules`；核验容差配置在 `config/verification.yaml`。

---

## 1. 系统边界（不可逾越）

1. **合成数据演示系统**：系统全部输入为程序合成的虚构数据，仅用于演示与评测风控方法，不面向生产业务。
2. **不做授信/投资决定**：系统输出的风险评分与预警仅供研究参考，不构成任何授信、投资或法律意见，不得用于真实决策。
3. **不接真实交易系统**：不与任何真实核心系统、交易系统、支付系统、登记系统对接；无任何外发写操作。
4. **不用真实个人敏感数据**：禁止使用真实身份证号、手机号、银行账户、人脸/声纹等个人敏感信息；所有人名、企业名、证件号均由 Faker 合成且显式标注为虚构。
5. **不公网部署**：仅本地/内网运行，Streamlit 绑定 localhost，不暴露到公网，不收集任何遥测数据。

---

## 2. 功能模块（12 个）

每个模块职责单一、可独立测试；模块间仅通过第 3 节的 schema 传递数据。

### M1 合成数据生成（`src/datagen`）
- **职责**：生成融资租赁业务的合成单据与评测集，包括正常案例与三类造假模式（a 承兴系伪造合同与单据、b 一单多押同一租赁物重复融资、c 空转贸易无真实交付的循环合同）。产出文本型 PDF（reportlab）与对应的结构化真值标签。
- **输入**：生成配置（案例数、欺诈比例、造假模式配比、随机种子、输出目录）。
- **输出**：PDF 文件集（合同/发票/租赁物清单）+ `labels.jsonl`（EvalLabel 序列）+ 结构化源数据（用于评测 oracle）。

### M2 单据解析（`src/parsing`）
- **职责**：从 PDF 单据中抽取结构化要素，并为每个字段产出字段级证据（页码/原文片段/坐标）。文本型 PDF 用 pymupdf/pdfplumber；扫描件可经 paddleocr（可选）。要素抽取优先规则/模板，LLM 作为兜底与歧义消解；mock 模式下全部走规则路径。
- **输入**：PDF 文件路径 + 单据类型提示（合同/发票/租赁物清单）。
- **输出**：`ContractEssentials` / `InvoiceEssentials` / `LeaseItemEssentials` 之一 + `list[FieldEvidence]`；解析失败抛 `ParseError`。

### M3 三单核验（`src/verification`）
- **职责**：对同一案例的合同、发票、租赁物清单做字段级交叉一致性核验：主体名称、金额（价税合计勾稽）、租赁物型号/数量/序列号、日期逻辑、对手方关系。
- **输入**：三份单据的要素模型及其证据。
- **输出**：`VerificationResult`（逐项核验结论 + 不一致项的证据对）。

### M4 77号文规则引擎（`src/rules`）
- **职责**：以可解释的规则集编码监管/内控红线（下称"77号文规则集"，为本演示虚构编号的规则包，条款文本存于 `config/rules_77.yaml`），对要素与核验结果做确定性命中判定。规则纯函数、可单元测试，每条命中必须携带条款引用与证据。
- **输入**：三单要素 + `VerificationResult`。
- **输出**：`list[RuleHit]`（规则编号/条款引用/证据/严重度）。

### M5 GPU 残值与现金流压力测试（`src/stress`）
- **职责**：对 GPU 类租赁物建立残值衰减曲线（代际折旧 + 算力价格情景），在基准/压力/极端三档情景下测算租金现金流覆盖倍数与 LTV，输出压力测试结论。
- **输入**：租赁物清单要素（GPU 型号/数量/购置价/租期/租金计划）+ 情景参数（内置默认值，可覆盖）。
- **输出**：`ResidualStressResult`。

### M6 利用率预警（`src/alerts`）
- **职责**：基于合成遥测时序（GPU 利用率）检测空转/闲置异常：长期低利用率、租约生效后零交付流量、与租金支付节奏背离等，分级预警。
- **输入**：租赁物清单要素 + 合成利用率时序（由 M1 生成，`pandas.Series`/DataFrame）。
- **输出**：`list[UtilizationAlert]`。

### M7 风险评分（`src/scoring`）
- **职责**：将核验结果、规则命中、压力测试、预警按透明权重汇总为 0–100 风险分（越高越危险），并给出各分项贡献，保证可解释、可复算（同输入同输出）。
- **输入**：`VerificationResult` + `list[RuleHit]` + `ResidualStressResult` + `list[UtilizationAlert]`。
- **输出**：`RiskScore`（总分 + 分项贡献 + 建议处置等级）。

### M8 证据链报告（`src/report`）
- **职责**：把全流程产物汇编为可审计的证据链报告（Markdown/HTML/PDF 任选其一，默认 Markdown）：每个结论回链到字段级证据（页码+原文+坐标），并附审计日志链哈希头尾值。
- **输入**：`PipelineState` 全量产物。
- **输出**：报告文件路径 + 覆盖率统计（有证据链支撑的结论数/总结论数）。

### M9 审计日志（`src/audit`）
- **职责**：各环节进出数据追加写入不可篡改审计链：每条记录含 `prev_hash`，当前哈希 = sha256(prev_hash + 规范序列化载荷)。提供整链校验函数。
- **输入**：各环节事件（环节名、输入摘要、输出摘要、时间戳、运行模式 mock/live）。
- **输出**：`audit_log.jsonl`（`AuditLogRecord` 序列）+ 链校验结果布尔值。

### M10 合规护栏（`src/guardrails`）
- **职责**：进出双向护栏。入口：检测并拒绝真实个人敏感数据模式（身份证/手机号/银行卡正则 + 校验位）、对抗性 prompt 注入（单据文本中嵌入的指令）；出口：所有对外文本强制附加"合成演示数据、不构成授信/投资建议"声明，拦截任何决策性措辞（如"应予放款"）。
- **输入**：原始文件文本 / 待输出文本。
- **输出**：放行或 `GuardrailViolation`（含命中模式）；出口为净化后文本。

### M11 Streamlit Demo（`app`）
- **职责**：本地交互演示：选择/生成案例 → 逐环节可视化（要素、证据高亮、规则命中、压力曲线、评分构成、证据链报告下载）。绑定 localhost。
- **输入**：用户交互（案例选择、参数调节）。
- **输出**：页面渲染 + 报告文件下载。

### M12 评测脚本（`eval`）
- **职责**：加载评测集标签，运行全 pipeline，计算第 6 节全部指标；内置"纯 LLM 消融基线"（跳过核验/规则/压力/评分，仅让 LLM 直接判欺诈，提示词与判定阈值硬编码在 eval 代码中，固定不变）；输出指标对比表。
- **输入**：评测集目录 + 运行模式（mock/live）。
- **输出**：`eval_report.json` + 控制台表格（含与基线的 pp 差值）。

---

## 3. 数据 Schema（Pydantic v2 模型定义）

> 实现位置：`src/schemas.py`（单一文件，后续阶段直接 import）。以下为冻结规格，字段名不得更改；允许新增带默认值的可选字段。

```python
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------- 通用 ----------

class DocType(str, Enum):
    CONTRACT = "contract"        # 融资租赁合同
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
    field_name: str          # 所属要素模型的字段名（点路径，如 "lessor.name"）
    page: int = Field(ge=1)  # 1-based 页码
    excerpt: str             # 原文片段（原样截取，不做改写）
    bbox: BBox | None = None # 文本型 PDF 必填；OCR 路径允许为空
    doc_type: DocType
    source_file: str         # 来源 PDF 文件名（相对路径）


class Party(BaseModel):
    name: str                # 虚构企业/个人名
    credit_code: str | None = None  # 虚构统一社会信用代码（合成）
    role: Literal["lessor", "lessee", "vendor", "guarantor"]


class MoneyAmount(BaseModel):
    amount: float = Field(ge=0)
    currency: Literal["CNY"] = "CNY"


# ---------- 单据要素 ----------

class ContractEssentials(BaseModel):
    """合同要素。"""
    contract_no: str
    sign_date: date
    lessor: Party                  # 出租人
    lessee: Party                  # 承租人
    vendor: Party | None = None    # 出卖人（直租场景）
    total_amount: MoneyAmount      # 租赁本金
    lease_term_months: int = Field(gt=0)
    rent_schedule: list[MoneyAmount]  # 各期租金
    deposit: MoneyAmount | None = None
    is_sale_leaseback: bool = False   # 是否售后回租


class InvoiceEssentials(BaseModel):
    """发票要素。"""
    invoice_no: str
    invoice_date: date
    seller: Party
    buyer: Party
    item_name: str                 # 货物/服务名称
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    amount_excl_tax: MoneyAmount
    tax_amount: MoneyAmount
    amount_incl_tax: MoneyAmount   # 应满足 excl + tax ≈ incl（核验勾稽点）


class LeaseItem(BaseModel):
    item_id: str                   # 清单内序号
    model: str                     # 如 "NVIDIA H100 80GB SXM"
    category: Literal["gpu", "server", "network", "storage", "other"]
    serial_no: str                 # 序列号（一单多押检测键）
    quantity: int = Field(gt=0)
    purchase_price: MoneyAmount
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
    check_name: str                # 如 "contract_vs_invoice.buyer_name"
    passed: bool
    detail: str
    evidences: list[FieldEvidence] = []  # 参与比对的证据对（至少 2 条当比对两单）


class VerificationResult(BaseModel):
    """三单核验结果。"""
    case_id: str
    checks: list[FieldCheckResult]
    passed_count: int
    failed_count: int

    @property
    def all_passed(self) -> bool: ...


class RuleHit(BaseModel):
    """规则命中。"""
    rule_id: str                   # 如 "R77-003"
    clause_ref: str                # 条款引用，如 "77号文 第十二条 第(二)项"
    severity: Literal["block", "high", "medium", "low"]
    description: str
    evidences: list[FieldEvidence]  # 命中证据，非空


# ---------- 压力测试 / 预警 / 评分 ----------

class ScenarioResult(BaseModel):
    scenario: Literal["base", "stress", "extreme"]
    residual_value_ratio: float    # 期末残值率 [0,1]
    ltv: float                     # 在租余额 / 租赁物估值
    dscr: float                    # 租金现金流覆盖倍数
    breach: bool                   # 是否突破阈值（ltv 或 dscr）


class ResidualStressResult(BaseModel):
    """残值与现金流压力测试结果。"""
    case_id: str
    gpu_model: str
    depreciation_curve: list[float]  # 按月残值率序列
    scenarios: list[ScenarioResult]  # 三档情景


class UtilizationAlert(BaseModel):
    """利用率预警。"""
    case_id: str
    alert_type: Literal["long_idle", "zero_delivery", "rent_divergence"]
    level: Literal["red", "orange", "yellow"]
    window: str                    # 触发时间窗，如 "2026-01~2026-03"
    detail: str
    metric_value: float            # 触发指标值（如月均利用率）


class ScoreComponent(BaseModel):
    """风险评分分项贡献。"""
    name: Literal["verification", "rules", "stress", "utilization"]
    weight: float                  # 权重（四项合计 1.0）
    raw: float                     # 分项原始值 [0,1]
    contribution: float            # 对总分的贡献点数 [0,100]


class RiskScore(BaseModel):
    """风险评分：0–100，越高越危险。"""
    case_id: str
    total: float = Field(ge=0, le=100)
    components: list[ScoreComponent]  # 分项贡献之和 = total（±0.01）
    grade: Literal["pass", "review", "reject"]  # 处置建议（演示用，非决策）


# ---------- 审计日志 ----------

class AuditLogRecord(BaseModel):
    """审计日志记录（哈希链）。"""
    seq: int = Field(ge=0)
    timestamp: datetime
    stage: str                     # 环节名，如 "parsing"
    run_mode: Literal["mock", "live"]
    input_digest: str              # 输入规范序列化的 sha256（hex）
    output_digest: str             # 输出规范序列化的 sha256（hex）
    prev_hash: str                 # 上一条记录的 record_hash；首条为 "0"*64
    record_hash: str               # sha256(prev_hash + canonical_payload)

    @staticmethod
    def compute_hash(prev_hash: str, canonical_payload: str) -> str: ...


# ---------- 评测集标签 ----------

class FraudPattern(str, Enum):
    A_CHENGXING = "a_chengxing"    # 承兴系：伪造合同/单据、假冒对手方
    B_MULTI_PLEDGE = "b_multi_pledge"  # 一单多押：同一租赁物重复融资
    C_CIRCULAR = "c_circular_trade"    # 空转贸易：无真实交付的循环合同


class EvalLabel(BaseModel):
    """评测集标签（labels.jsonl 每行一条）。"""
    case_id: str
    is_fraud: bool                 # True=欺诈，False=正常
    fraud_pattern: FraudPattern | None = None  # is_fraud=True 时必填
    files: dict[DocType, str]      # 单据类型 -> PDF 相对路径
    oracle: dict                   # 结构化真值（要素级，供抽取准确率评测）
    injected_adversarial: bool = False  # 是否嵌入对抗性注入（护栏评测用）
```

---

## 4. Pipeline 定义

### 4.1 实现形态

- **主实现为纯 Python 函数链**（`src/pipeline.py`）：顺序调用各环节函数，仅依赖标准库 + 本仓库代码，**不依赖 LangGraph**。
- `src/pipeline_graph.py` 为**可选等价实现**（LangGraph 编排）：仅当 `import langgraph` 成功时可用；节点与边一一对应 4.3 的函数，输入输出完全一致。未安装 langgraph 时该模块不得被 import（惰性导入），且不影响任何测试与评测。

### 4.2 PipelineState

```python
from pydantic import BaseModel

class PipelineState(BaseModel):
    """环节间传递的完整状态。各环节只写自己负责的字段。"""
    case_id: str
    run_mode: Literal["mock", "live"]
    files: dict[DocType, str]                       # 输入单据路径

    contract: ContractEssentials | None = None
    invoice: InvoiceEssentials | None = None
    lease_items: LeaseItemEssentials | None = None
    evidences: list[FieldEvidence] = []

    verification: VerificationResult | None = None
    rule_hits: list[RuleHit] = []
    validation_flags: list[ValidationFlag] = []     # v0.8 新增：字段级交叉校验标记
    stress: ResidualStressResult | None = None
    alerts: list[UtilizationAlert] = []
    risk_score: RiskScore | None = None

    utilization_series: list[float] = []            # M1 附带的合成遥测
    report_path: str | None = None
    errors: list[str] = []                          # 结构化异常的降级记录
```

### 4.3 各环节函数签名（冻结）

```python
# src/pipeline.py

def stage_guardrail_in(state: PipelineState) -> PipelineState:
    """入口护栏：敏感数据检测 + 对抗注入拦截。命中则记录 errors 并中止后续环节。"""

def stage_parse(state: PipelineState) -> PipelineState:
    """M2：填充 contract/invoice/lease_items/evidences。"""

def stage_validate(state: PipelineState) -> PipelineState:
    """v0.8 新增：字段级交叉校验（解析层之后、核验之前），填充 validation_flags。
    review 级标记 = 字段置信度置 0 转人审；info 级仅记录。不改变 M2 抽取接口。"""

def stage_verify(state: PipelineState) -> PipelineState:
    """M3：填充 verification。"""

def stage_rules(state: PipelineState) -> PipelineState:
    """M4：填充 rule_hits。"""

def stage_stress(state: PipelineState) -> PipelineState:
    """M5：填充 stress。非 GPU 租赁物跳过（stress 保持 None 并记审计）。"""

def stage_alerts(state: PipelineState) -> PipelineState:
    """M6：填充 alerts。无利用率序列时为空列表。"""

def stage_score(state: PipelineState) -> PipelineState:
    """M7：填充 risk_score。依赖 verification 与 rule_hits 存在。"""

def stage_report(state: PipelineState) -> PipelineState:
    """M8：填充 report_path。"""

def stage_guardrail_out(state: PipelineState, text: str) -> str:
    """出口护栏：返回净化后文本（附合规声明、剔除决策性措辞）。"""

def run_pipeline(case_id: str, files: dict[DocType, str], run_mode: str = "mock") -> PipelineState:
    """顺序执行全部环节；每个环节进出写审计日志（M9）；任一环节结构化异常不中断主链，记入 state.errors 并按 5.2 回退。"""
```

---

## 5. 错误处理约定

### 5.1 结构化异常（`src/errors.py`）

```python
class JinDunError(Exception):
    """基类：携带 code 与 context，message 面向日志。"""

class ParseError(JinDunError): ...        # code="PARSE_*"：单据无法解析/要素缺失
class VerificationError(JinDunError): ... # code="VERIFY_*"
class LLMError(JinDunError): ...          # code="LLM_*"：超时/限流/非法 JSON
class GuardrailViolation(JinDunError): ...# code="GUARD_*"：护栏命中，终止处理
class AuditChainError(JinDunError): ...   # code="AUDIT_*"：哈希链校验失败
```

约定：所有异常带 `code: str` 与 `context: dict`；不向调用方抛裸异常；pipeline 捕获后写入 `state.errors`（`f"{code}: {message}"`）。

### 5.2 mock 模式回退

- 无 `LLM_API_KEY` 或 LLM 调用抛 `LLMError` → 自动降级为规则/模板路径（mock），并在审计日志记录 `run_mode` 与实际降级事件。
- mock 与 live 共用同一套 schema、指标口径与验收阈值；评测报告必须标注运行模式。
- 任何环节降级不得静默：必须留下审计记录与 `state.errors` 条目。

---

## 6. 验收标准（评测口径统一，mock 与 live 同口径）

| # | 指标 | 阈值 | 说明 |
|---|------|------|------|
| 1 | 要素抽取准确率 | ≥ 95% | 字段级 exact-match 对 oracle；mock 同口径 |
| 2 | 三单核验 F1 | ≥ 0.90 | 以"不一致项检出"为正类 |
| 3 | 欺诈召回 / 误报 | 召回 ≥ 90%，误报 ≤ 10% | 以 EvalLabel.is_fraud 为真值，风险分判定阈值固定于 eval 代码 |
| 4 | 规则命中率 | 100% | 所有预埋应命中的规则无一遗漏（以标签标注的规则清单核对） |
| 5 | 证据链覆盖率 | ≥ 98% | 有字段级证据回链的结论数 / 总结论数 |
| 6 | 对抗拦截率 | 100% | injected_adversarial=True 样本全部被护栏拦截 |
| 7 | 单案端到端耗时 | ≤ 3 分钟 | 全 pipeline 单案例墙钟时间 |
| 8 | token 成本 | ≤ 0.5 元/案 | 仅 live（有 Key）模式评估；mock 为 0 |
| 9 | vs 纯 LLM 消融基线 | 欺诈检出率提升 ≥ 15pp | 基线为"纯 LLM 直接判欺诈"，其提示词与判定规则固定硬编码在 eval 代码中，不随实现演进修改 |

---

## 7. 仓库结构

```
suanlian-jindun/
├── requirements.txt            # 核心依赖
├── requirements-optional.txt   # 可选依赖（langgraph / paddleocr，注释说明）
├── .env.example                # LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
├── SPEC.md                     # 本文档
├── config/                     # 配置：settings.py、rules_77.yaml（后续阶段）
├── src/                        # 核心 pipeline 与 12 模块的实现代码
├── app/                        # Streamlit Demo
├── eval/                       # 评测脚本与消融基线
├── tests/                      # pytest 单测
└── data/                       # 合成数据与评测集产物（不入库）
```

## 8. 本阶段验收命令

```bash
pip install -r requirements.txt
python -c "import src"
```
