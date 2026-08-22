# 算链金盾（suanlian-jindun）

算力（GPU）融资租赁智能风控**合成数据演示系统**：对"购销合同 + 增值税发票 + 租赁物清单"三单做
字段级证据抽取、三单一致性核验、贸易真实性与账期规则、GPU 残值与现金流压力测试、利用率预警与
0–100 风险评分，输出可追溯到单据坐标的证据链报告与防篡改审计包。

## ⚠️ 合规红线声明（系统边界，不可逾越）

- **本系统输出为 AI 辅助意见，不构成授信或投资建议**，所有 AI 生成内容带显式标识；
- 不接任何真实交易系统，不做授信/投资决定；
- 全部演示数据为程序合成的虚构数据，不使用真实个人敏感数据（单据内证件号/银行账号均为掩码形式）；
- 仅本地 localhost 运行，不公网部署；
- 所有外部接口（LLM、外部负面信号、动产登记查询）均为模拟/可替换接口。

系统边界详见 [SPEC.md](SPEC.md) 第 1 节；监管条款到产品功能的对照见 [docs/compliance.md](docs/compliance.md)。

## 参赛主体与责任边界

本项目按赛事补充规则，以**一人公司（OPC）**形式单独参赛。项目负责人独立承担需求定义、
合规边界、算法与工程实现、测试复核、材料提交及路演答辩；开源组件、LLM API 和 AI 编程助手
仅作为开发工具，不作为团队成员或成果责任主体。所有最终决策、指标披露与交付责任均由负责人承担。

## 快速开始（逐条可复制）

```bash
pip install -r requirements.txt
cp .env.example .env          # 填入真实 LLM_API_KEY/BASE_URL/MODEL；保持占位符时用 --mock 运行
python -c "import src"        # 初始化自检：无输出即通过
python -m src.datagen.generate --n 100 --out data/cases --seed 42   # 生成合成评测集（可复现）
python -m src.pipeline --case data/cases/case_0001 --mock           # 单案端到端（mock）
streamlit run app/streamlit_app.py                                  # 本地 Demo（仅 localhost）
python -X utf8 -m eval.run_eval --cases data/cases --mock           # 全量评测（mock，无需 Key）
python -X utf8 -m eval.run_eval --cases data/cases                  # 全量评测（live，需 Key）
python -X utf8 -m eval.run_eval --cases data/cases --rerun-baseline-only  # 只重跑消融基线（缓存续跑）
python -m pytest -q tests/                                          # 115 passed, 1 skipped
```

Windows 控制台建议评测命令保留 `-X utf8`，避免结果表中的 Unicode 状态符在 GBK 环境下
触发编码错误。

可选依赖（`requirements-optional.txt`，不安装不影响运行）：`langgraph`（等价编排，
`src/pipeline_langgraph.py` 惰性导入）、`paddleocr`（扫描件 OCR 预留）。

## 评测结果（修正口径重跑，2026-08-22；100 案 = 70 正常 + 30 欺诈[a/b/c 各 10]，seed 42）

> **评测口径修正声明（2026-08-22）**：旧评测默认把全量 `labels.jsonl` 的租赁物真值加载为
> 跨案件登记历史，使前案能够“看到”未来案件，构成 EVAL-01 前视泄漏。现改为按标签顺序滚动构建
> 上下文，且只写入已完成前案的系统抽取输出，不读取未来案件或标签 oracle，与生产登记库只包含
> 历史已登记案件的条件一致。修正后召回为 83.33%：`b_multi_pledge` 每对案件的首次出现因无外部
> 完整登记历史而结构性不可检（该模式召回 50%），a/c 两类仍为 100%。本次未改 pipeline 检测逻辑、
> 评分权重、标签或数据集，只修正评测方法。

### mock 模式（[eval/results/eval_results.md](eval/results/eval_results.md)）

| 指标 | 结果 | 目标 | 达标 |
|---|---|---|---|
| 要素抽取准确率 | 100.00%（3260/3260 字段） | ≥95% | ✅ |
| 三单核验 F1 | 0.9091 | ≥0.90 | ✅ |
| 欺诈检出召回 / 误报率 | 83.33% / 0.00% | ≥90% / ≤10% | ❌ / ✅ |
| 规则命中准确率 | 95.00% | 100% | ❌ |
| 证据链覆盖率 | 100.00%（928/928 条结论） | ≥98% | ✅ |
| 对抗拦截率 | 100.00%（22/22） | 100% | ✅ |
| 单案端到端时耗 | 均值 0.205s / 最大 0.38s | ≤3 分钟 | ✅ |
| LLM token 成本 | 0 元/案（mock） | ≤0.5 元/案 | ✅ |
| 消融：检出率提升 | **+50.0pp**（系统 83.33% vs mock 关键词基线 33.33%） | ≥15pp | ✅ |

### live 模式（真实 LLM 消融基线，[eval/results_live/eval_results_after_baseline_fix.md](eval/results_live/eval_results_after_baseline_fix.md)）

主系统采用上述修正后口径（正则优先设计，pipeline 全程 0 LLM 调用、0 token、成本 0 元/案）。
真实 LLM 直判基线（`eval/baseline.py` v2-fixed-2026-08-11，temperature=0，严格 JSON 输出，
100 次调用、92,791 tokens、0 invalid）：

| 方案 | 召回 | 误报率 | 精确率 | F1 | Balanced Acc | MCC |
|---|---|---|---|---|---|---|
| 本系统 | 83.33% | 0.00% | 100.00% | 0.9091 | 0.9167 | 0.8819 |
| 纯 LLM 直判基线 | 36.67% | 1.43% | 91.67% | 0.5238 | 0.6762 | 0.4969 |
| **检出率（召回）提升** | **+46.7pp** | | | | 目标 ≥15pp | ✅ |

分造假模式基线召回：a 承兴系 100%、b 一单多押 10%、c 空转贸易 0%——纯 LLM 只能看出单案内
主体不一致，无法发现跨案件租赁物重复质押与实控人关联空转，这正是结构化 pipeline 的增量价值。

**基线有效性复核（如实记录）**：首轮 live 基线（v1）曾退化为"逢案必报"（召回 100%/误报 100%，
提升 +0.0pp）。复核发现 v1 存在子串解析脆弱、异常默认映射、低门槛诱导措辞等 6 项实现 bug
（详见 `eval/results_live/eval_results_after_baseline_fix.md` 与
[eval/results/baseline_audit.jsonl](eval/results/baseline_audit.jsonl) 逐案审计）；仅修复
eval/baseline* 的客观错误后重跑（主系统代码/权重/标签/评测集零改动），得到上表有效结果。
修复前原始结果保留于 `eval/results_live/eval_results_before_baseline_fix.{json,md}`。

### 未达标项（如实披露）

- `fraud_recall`：83.33%，低于 ≥90% 目标。根因是 `b_multi_pledge` 每对案件的首次出现没有前案
  登记历史，在不接入完整外部登记库时结构性不可检测；其后出现的同物案件可检出，a/c 模式均保持 100%。
- `rule_accuracy`：95.00%，低于 100% 目标。对应同一结构性原因：5 个首次出现的
  `b_multi_pledge` 案件无法命中依赖历史冲突的 R77-005。

## 技术架构

```
三单 PDF ──► 护栏（注入检测/敏感数据拒绝/工具白名单）
        ──► 解析（PyMuPDF 提取，正则优先、LLM 补充，字段级证据：页码/原文/坐标）
        ──► 三单核验（主体规范化/金额勾稽/账期/跨案件租赁物查重）
        ──► 贸易真实性与账期规则库（含银发〔2025〕77号场景化规则，R77-001~005）
        ──► GPU 残值与压力测试（分代折旧 + 利用率 -20%/单客户违约情景）
        ──► 利用率预警（绿/黄/红，"T-N 天预警"）
        ──► 风险评分 0–100（显式权重 + 分项贡献 + 红线兜底）
        ──► 人审路由（<60 建议通过 / 60–90 强制人工复核 / >90 建议拒绝）
        ──► 证据链报告（Markdown/HTML）+ 审计包 zip + SQLite 哈希链审计日志
```

- **纯 Python 顺序 pipeline 为主**（`src/pipeline.py`，state 为 SPEC 定义的 Pydantic 模型）；
  LangGraph 仅为可选等价实现，未安装不影响运行与测试；
- **正则优先、LLM 补充**：无 API Key 自动回退 mock 模式，全链路（含评测）可跑、成本为 0；
- PaddleOCR 为扫描件预留可选组件，本演示数据为数字文本 PDF，非必需；
- 评测口径与消融基线固定在 `eval/` 代码中（`BASELINE_VERSION` 冻结），不随主系统调参变动。

## 仓库结构

```
config/    配置（规则集 rules_77.yaml、评分权重、残值/预警/核验参数）
src/       datagen · parsing · verification · rules · asset · monitoring
           scoring · report · audit(SQLite 哈希链) · guardrails · pipeline
app/       Streamlit Demo（localhost）
eval/      run_eval（全指标）· baseline（消融基线）· rerun_baseline · adversarial · results*
docs/      compliance（监管对照）· demo_script（路演脚本）· plan_draft（项目书骨架）· screenshots
tests/     pytest（50 项）
data/      合成评测集与运行产物（不入库）
```

## 已知局限

- **合成数据外部效度**：评测集为模板生成的数字文本 PDF，版式与噪声分布不同于真实扫描件；
  指标反映的是受控环境下的能力上限，不能直接外推到生产数据；
- 三类造假模式为已知模式的程序化注入，对未知欺诈手法的泛化未验证；
- 残值/折旧/租金参数为公开案例校准的假设值（`config/asset.yaml` 有注释），非市场报价；
- 利用率时序、外部负面信号、动产登记查询均为本地 mock（代码中标注"模拟接口"）；
- 主体规范化比对的缩写匹配规则在 mock 模式存在理论误报面，live 口径未暴露；
- 消融基线的 prompt 设计空间很大，本基线仅是"纯 LLM 直判"的一个固定代表。

## 外部效度初步验证（mini-test，2026-08-13）

为回应"出题人即考生"质疑，用 4 份**网上公开的真实版式单据**（非自制）检验解析层在
非合成版式上的鲁棒性。样本为公开披露文件，仅存于 `data/external/`（gitignore 覆盖，
不入库、不上传、不再分发）；真值经人工阅读原文标注于
[eval/external_truth.jsonl](eval/external_truth.jsonl)（敏感字段不照录）。
完整结果：[eval/results/external_validity.md](eval/results/external_validity.md)
（可复跑：`python -m eval.run_external`）。

| 样本（来源类型+渠道+日期） | 页数 | 文本层 | 字段抽取成功率 | 优雅降级 |
|---|---|---|---|---|
| 售后回租合同特别条款（真实公章+手写签名扫描版式，港交所披露易，2026-06） | 4 | 无 | 0/5（0%） | ✅ PARSE_NO_TEXT_LAYER |
| 售后回租合同（专用条款大表式+横排跨页清单，港交所披露易，2025-09） | 56 | 无 | 0/6（0%） | ✅ PARSE_NO_TEXT_LAYER |
| 售后回租合同（全文对角水印+发票号级清单，上市公司公告附件，2022-05） | 35 | 无 | 0/6（0%） | ✅ PARSE_NO_TEXT_LAYER |
| 数电发票样式（国家税务总局 2024 年第 11 号公告附件，票样为嵌入图片） | 16 | 仅分节标题 | 0/6（0%） | ✅ PARSE_FIELD_MISSING |

**总体抽取率 0/23（0%）**——如实记录，这正是本次测试最有价值的材料：

- **失败模式分类**：扫描页无文本层 17 字段；票面要素为图片（文本层仅标题）6 字段；
  水印干扰与跨页表格断裂两种失败面**未被触及**（无文本层在更上游拦截）；
- **差距根因**：合成评测集 100% 抽取率的前提是数字文本 PDF；而真实披露渠道的
  售后回租合同**全部是整本扫描件**（4/4 样本），官方发票票样也是图片。瓶颈不在
  版式适配，而在文档获取形态——文本优先的解析层对扫描件天然无效；
- **本阶段的通用改进**（非样本特例）：`PdfTextReader` 新增无文本层检测
  （`has_text_layer`/`is_likely_scanned`），解析入口对扫描件抛出显式结构化错误
  `PARSE_NO_TEXT_LAYER` 而非静默空抽取；4/4 样本降级行为全部优雅（无未捕获异常）；
- **OCR 复测见下文 v2**（2026-08-13/14）：v1 时 OCR 为预留能力未启用，v2 已启用并复测；
- **结论**：合成数据指标反映的是"数字文本单据"能力上限；真实生产接入扫描件必须
  经过 OCR 前置，本系统已具备对该边界的显式识别与降级能力。

## 外部效度 v2（OCR 增强复测 + 原生电子版补测，2026-08-13/14）

在 v1 基础上做两件事：(A) 启用 PaddleOCR 可选路径复测 4 份扫描样本，触及 v1 未触及的
水印干扰与跨页表格断裂两个失败面；(B) 补充 2 份**官方示范文本+模拟填写**的原生电子版
样本（市场监管总局合同示范文本库 GF-2000-0101 工业品买卖合同、国家数据局/市场监管总局
GF-2025-2616 数据委托处理服务合同，空白条款全部填入合成"示例"系数据，非真实合同），
首次测出字段级外部泛化准确率。完整结果：
[eval/results/external_validity_v2.md](eval/results/external_validity_v2.md)
（可复跑：`python -m eval.run_external --ocr`，OCR 默认关闭，仅 `--ocr` 或
`ENABLE_OCR=1` 时启用，未安装 paddleocr 不影响任何既有结果）。

**v1 → v2 对比（逐样本字段抽取成功率）**

| 样本 | v1（纯文本层） | v2（+OCR 兜底） |
|---|---|---|
| 售后回租合同特别条款（港交所披露易，2026-06） | 0/5 | **5/5（100%）** |
| 售后回租合同大表式版式（港交所披露易，2025-09） | 0/6 | **5/6（83%）** |
| 售后回租合同对角水印版式（上市公司公告附件，2022-05） | 0/6 | **4/6（67%）** |
| 数电发票样式（国家税务总局公告附件，空白票样） | 0/6 | 0/6（空白票样无数值，预期不可抽取） |
| 买卖合同示范文本+模拟填写（GF-2000-0101，原生电子版） | —（v2 新增） | **5/6（83%）** |
| 数据委托处理服务合同示范文本+模拟填写（GF-2025-2616，原生电子版） | —（v2 新增） | **5/5（100%）** |
| **总体** | **0/23（0%）** | **24/34（71%）** |

**原生电子版首次字段级泛化准确率**：v1 抽取器直跑仅 1/11（9%，融资租赁专用标签不覆盖
买卖/服务合同命名）；经**通用同义标签扩充**（出卖人/买受人/委托方/受托方/费用总额/
有效期至等，非样本特例）后达 **10/11（91%）**，唯一失败为买卖合同标的表格窄列换行断裂
（表格结构差异）。

**OCR 新增失败模式分布**：ocr 误识别 1 字段（合同 C 租赁期限"144 个月"被识别为
"44 个月"，形近漏字）；跨页表格断裂 2 字段（合同 B 横排 90° 清单 OCR 行序错乱、
合同 C 跨页清单行数不可复原）；字段缺失 6 字段（官方空白票样无数值，预期行为）。
低置信转人工（ocr_low_confidence）0 字段。OCR 成本：250DPI 平均约 81s/页
（CPU，paddlepaddle 3.2.2 + paddleocr 3.7.0），仅跑含目标字段的关键页共 19 页。

**v2 通用改进（非样本特例）**：文本层抽取失败字段自动降级 OCR 兜底（两遍抽取，保留文本层
命中）；合同填写值【】括号容忍；通用同义标签表；金额取文中最大货币候选值策略；OCR 逐页
缓存与字段级置信度路由（<0.80 转人工）。

**历史无回归记录**：v2 全部改动后 `pytest -q tests/` 53 绿；当时评测实现记录为
`run_eval --mock` 9/9，且 v1 口径复跑与原结果逐字段一致（证明附于 v2 报告末节）。该 9/9
因后续发现 EVAL-01 前视泄漏已不再作为当前成绩；当前成绩统一以本页 2026-08-22 修正主表的
7/9 达标为准。

### v2 后续改进：字段级交叉校验（v3，2026-08-13）

v2 暴露出"OCR 自信误识别静默通过"的风险（contract_C 期限 144→44，低置信路由未触发），
v3 为金额与期限两个高风险字段增加"自我证伪"能力
（[eval/results/external_validity_v3.md](eval/results/external_validity_v3.md)，
复跑：`python -m eval.run_external --ocr`）：

- **金额大写/小写交叉校验**（`src/parsing/chinese_amount.py` + `src/validation/`）：
  中文大写金额解析（零壹贰…万亿/角分/整正）、阿拉伯金额归一化（¥/￥/RMB/万元/亿元）；
  两种写法不一致 → `amount_mismatch_daxie`，字段置信度置 0 转人审；只有一种写法 →
  记录 `amount_crosscheck_unavailable` 不惩罚；A/B/C 三份合同的大写/小写均交叉证实
  （7460 万/3.8 亿/4.35 亿 ✓）；
- **期限边界与一致性**：期限解析增强（阿拉伯/中文数字、年×12、【】括号）、有效区间
  [1,120] 个月可配置（`config/settings.py`，依据：融资租赁常见 1 个月–10 年）、
  多值冲突与起止日期一致性检查 → `term_out_of_bounds` / `term_inconsistent` 转人审；
- **触发实例**：contract_C `term_months` 被 `term_inconsistent`（44 vs 144 冲突）拦截
  转人审（真阳，v2 的静默错值被根除）；contract_B 180 个月租期被 `term_out_of_bounds`
  拦截（假阳·规则边界，风电 15 年租期真实存在，人审可放行）；
- **集成**：validation 阶段挂在解析层之后（`stage_validate`），标记进入 pipeline state、
  SQLite 审计日志（原始值掩码）与 Streamlit 人审路由面板（显示原因码）；
- **历史无回归记录**：该阶段共收集 116 项 pytest（当前环境实跑 115 passed、1 skipped），
  v1 口径复跑逐字段一致；v2→v3 仅 2 处字段状态变化（即上述两例）。当时记录的 mock 9/9
  已被 EVAL-01 修正口径取代，当前成绩为 7/9。

### 数电票票样归因修正 + 发票版式首次有效测量（v4，2026-08-13）

经官方附件原件逐图人工核验确认：国家税务总局 2024 年第 11 号公告附件《数电发票样式》
25 类票样**全部是空白模板**——票面只有字段标签，所有值栏均为空（依据：公告第三条，
票样仅展示票面基本内容要素之版式）。因此 v1–v3 中 invoice_style 样本 6 字段
"真值存在=是"系**真值标注错误**，系统返回 PARSE_FIELD_MISSING、抽取 0/6 是对空白
模板的**正确行为**，非抽取能力缺口。v4 修正
（[eval/results/external_validity_v4.md](eval/results/external_validity_v4.md)，
复跑：`python -m eval.run_external --ocr --stem external_validity_v4 --preamble-file eval/v4_correction_note.md`）：

- **标注修正**：invoice_style 6 字段真值改为"字段值不存在（官方空白模板）"，
  剔除出抽取率分母，不再计入失败模式"字段缺失"；v1–v3 原报告保留不动；
- **替代样本**：以官方空白票样为底版叠加全合成数据生成填写版数电票
  （`eval/make_filled_invoice.py` → `data/external/invoice_filled_synthetic.pdf`，
  不入库）：20 位模拟发票号码（公告第四条口径）、合成购销双方、金额 884,955.75 /
  税率 13% / 税额 115,044.25 / 价税合计壹佰万元整（大小写一致）；
- **发票版式首次有效外部测量：6/6（100%）**——发票号码/开票日期/销售方/购买方/
  价税合计/税额全部命中，且金额大写/小写交叉校验**正确触发 match 路径**
  （`amount_crosscheck_match`，壹佰万元整 = 1,000,000.00 ✓）；
- **修正后总体抽取率**：既有样本 23/28（82.1%，分母剔除空白模板 6 字段）；
  含替代样本 29/34（85.3%）；既有 5 样本逐字段结果与 v3 完全一致（无回归）；
- **通用改进**（非样本特例）：税额抽取新增"发票合计行双数值取第二值"通用回退模式；
  run_external 支持 `--stem/--title/--preamble-file`（归因修正报告可复跑）；
- **无回归**：共收集 116 项 pytest（当前环境实跑 115 passed、1 skipped），既有 5 个外部样本逐字段结果与 v3 一致；该阶段曾记录的 mock
  9/9 属 EVAL-01 修正前口径，当前统一以 v5 修正后的 7/9 为准。

## 文档与脚本

### v5 变更记录（2026-08-22）

- EVAL-01：取消隐式加载全量标签，评测按时间序仅用前案系统输出构建登记上下文；修正后召回
  83.33%、规则准确率 95.00%、mock/live-basis 提升分别为 +50.0pp/+46.7pp。
- VAL-01：`severity=review` 的字段级交叉校验标记进入评分路由，风险分只抬升下限、不压低真实拒绝案。
- AMT-01：支持 `【100】万元`、`【1.5】亿元` 与方括号包裹的阿拉伯金额。
- REG-01：按银发〔2025〕77号第十至十三条修正规则引用，R77-004 明确为内部演示阈值。

- [SPEC.md](SPEC.md) — 系统边界、12 模块、schema、指标口径（唯一规格依据）
- [docs/compliance.md](docs/compliance.md) — 监管条款 → 产品功能对照表
- [docs/demo_script.md](docs/demo_script.md) — 3 分钟路演 Demo 脚本
- [docs/plan_draft.md](docs/plan_draft.md) — 参赛项目书骨架
- [docs/screenshots/](docs/screenshots/) — Demo 页面截图

## 测试

```bash
python -m pytest -q tests/    # 115 passed, 1 skipped
```

