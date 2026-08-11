# 算链金盾（suanlian-jindun）

算力（GPU）融资租赁智能风控**合成数据演示系统**：对"购销合同 + 增值税发票 + 租赁物清单"三单做
字段级证据抽取、三单一致性核验、77 号文规则引擎、GPU 残值与现金流压力测试、利用率预警与
0–100 风险评分，输出可追溯到单据坐标的证据链报告与防篡改审计包。

## ⚠️ 合规红线声明（系统边界，不可逾越）

- **本系统输出为 AI 辅助意见，不构成授信或投资建议**，所有 AI 生成内容带显式标识；
- 不接任何真实交易系统，不做授信/投资决定；
- 全部演示数据为程序合成的虚构数据，不使用真实个人敏感数据（单据内证件号/银行账号均为掩码形式）；
- 仅本地 localhost 运行，不公网部署；
- 所有外部接口（LLM、外部负面信号、动产登记查询）均为模拟/可替换接口。

系统边界详见 [SPEC.md](SPEC.md) 第 1 节；监管条款到产品功能的对照见 [docs/compliance.md](docs/compliance.md)。

## 快速开始（逐条可复制）

```bash
pip install -r requirements.txt
cp .env.example .env          # 填入真实 LLM_API_KEY/BASE_URL/MODEL；保持占位符时用 --mock 运行
python -c "import src"        # 初始化自检：无输出即通过
python -m src.datagen.generate --n 100 --out data/cases --seed 42   # 生成合成评测集（可复现）
python -m src.pipeline --case data/cases/case_0001 --mock           # 单案端到端（mock）
streamlit run app/streamlit_app.py                                  # 本地 Demo（仅 localhost）
python -m eval.run_eval --cases data/cases --mock                   # 全量评测（mock，无需 Key）
python -m eval.run_eval --cases data/cases                          # 全量评测（live，需 Key）
python -m eval.run_eval --cases data/cases --rerun-baseline-only    # 只重跑消融基线（缓存续跑）
python -m pytest -q tests/                                          # 50 passed
```

可选依赖（`requirements-optional.txt`，不安装不影响运行）：`langgraph`（等价编排，
`src/pipeline_langgraph.py` 惰性导入）、`paddleocr`（扫描件 OCR 预留）。

## 评测结果（真实运行，2026-08-11；100 案 = 70 正常 + 30 欺诈[a/b/c 各 10]，seed 42）

### mock 模式（[eval/results/eval_results.md](eval/results/eval_results.md)）

| 指标 | 结果 | 目标 | 达标 |
|---|---|---|---|
| 要素抽取准确率 | 100.00%（3260/3260 字段） | ≥95% | ✅ |
| 三单核验 F1 | 1.0000 | ≥0.90 | ✅ |
| 欺诈检出召回 / 误报率 | 100.00% / 0.00% | ≥90% / ≤10% | ✅ |
| 规则命中准确率 | 100.00% | 100% | ✅ |
| 证据链覆盖率 | 100.00%（940/940 条结论） | ≥98% | ✅ |
| 对抗拦截率 | 100.00%（22/22） | 100% | ✅ |
| 单案端到端时耗 | 均值 0.214s / 最大 0.28s | ≤3 分钟 | ✅ |
| LLM token 成本 | 0 元/案（mock） | ≤0.5 元/案 | ✅ |
| 消融：检出率提升 | **+66.7pp**（系统 100% vs mock 关键词基线 33.3%） | ≥15pp | ✅ |

### live 模式（真实 LLM 消融基线，[eval/results_live/eval_results_after_baseline_fix.md](eval/results_live/eval_results_after_baseline_fix.md)）

主系统指标与 mock 完全一致（正则优先设计，pipeline 全程 0 LLM 调用、0 token、成本 0 元/案）。
真实 LLM 直判基线（`eval/baseline.py` v2-fixed-2026-08-11，temperature=0，严格 JSON 输出，
100 次调用、92,791 tokens、0 invalid）：

| 方案 | 召回 | 误报率 | 精确率 | F1 | Balanced Acc | MCC |
|---|---|---|---|---|---|---|
| 本系统 | 100.00% | 0.00% | 100.00% | 1.0000 | 1.0000 | 1.0000 |
| 纯 LLM 直判基线 | 36.67% | 1.43% | 91.67% | 0.5238 | 0.6762 | 0.4969 |
| **检出率（召回）提升** | **+63.3pp** | | | | 目标 ≥15pp | ✅ |

分造假模式基线召回：a 承兴系 100%、b 一单多押 10%、c 空转贸易 0%——纯 LLM 只能看出单案内
主体不一致，无法发现跨案件租赁物重复质押与实控人关联空转，这正是结构化 pipeline 的增量价值。

**基线有效性复核（如实记录）**：首轮 live 基线（v1）曾退化为"逢案必报"（召回 100%/误报 100%，
提升 +0.0pp）。复核发现 v1 存在子串解析脆弱、异常默认映射、低门槛诱导措辞等 6 项实现 bug
（详见 `eval/results_live/eval_results_after_baseline_fix.md` 与
[eval/results/baseline_audit.jsonl](eval/results/baseline_audit.jsonl) 逐案审计）；仅修复
eval/baseline* 的客观错误后重跑（主系统代码/权重/标签/评测集零改动），得到上表有效结果。
修复前原始结果保留于 `eval/results_live/eval_results_before_baseline_fix.{json,md}`。

**未达标项**：当前 9 项指标在 mock 与 live 口径下全部达标，无未达标项。

## 技术架构

```
三单 PDF ──► 护栏（注入检测/敏感数据拒绝/工具白名单）
        ──► 解析（PyMuPDF 提取，正则优先、LLM 补充，字段级证据：页码/原文/坐标）
        ──► 三单核验（主体规范化/金额勾稽/账期/跨案件租赁物查重）
        ──► 77 号文规则引擎（config/rules_77.yaml，R77-001~005）
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

## 文档与脚本

- [SPEC.md](SPEC.md) — 系统边界、12 模块、schema、指标口径（唯一规格依据）
- [docs/compliance.md](docs/compliance.md) — 监管条款 → 产品功能对照表
- [docs/demo_script.md](docs/demo_script.md) — 3 分钟路演 Demo 脚本
- [docs/plan_draft.md](docs/plan_draft.md) — 参赛项目书骨架
- [docs/screenshots/](docs/screenshots/) — Demo 页面截图

## 测试

```bash
python -m pytest -q tests/    # 50 passed
```
