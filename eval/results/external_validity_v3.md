# 外部效度测试报告 v3（OCR + 字段级交叉校验）

- 生成时间：2026-08-13T04:07:44.148246+00:00
- 样本目录：data/external/（不入库、不上传、不再分发）
- OCR：OCR（paddleocr 3.7 + paddlepaddle 3.2.2，250DPI，仅关键页）已启用；低置信字段转人工路由（ocr_low_confidence）；字段级交叉校验（金额大写/小写、期限边界/一致性）已启用，review 级标记转人审。
- 合规：输出不含银行账号/电话/身份证类敏感字段原文；样本以来源类型+渠道+日期描述。

## 样本与文本层检测

| 样本 | 页数 | 文本层 | 文本页占比 | 疑似扫描件 |
|---|---|---|---|---|
| 售后回租合同特别条款（真实公章+手写签名扫描版式）（港交所披露易，2026-06） | 4 | 无 | 0% | 是 |
| 售后回租合同（专用条款大表式版式，含骑缝章与横排清单）（港交所披露易，2025-09） | 56 | 无 | 0% | 是 |
| 售后回租合同（全文对角水印+骑缝章，发票号级租赁物清单）（上市公司公告附件（东方财富 PDF 库），2022-05） | 35 | 无 | 0% | 是 |
| 数电发票样式（官方票样，25 类票样为嵌入图片）（国家税务总局 2024 年第 11 号公告附件（由 doc 附件经 Word 转 PDF），2024-11） | 16 | 有 | 94% | 否 |
| 官方买卖合同示范文本（GF-2000-0101 工业品买卖合同）+模拟填写（市场监管总局合同示范文本库（Word 版模拟填写后转 PDF），2026-08） | 4 | 有 | 100% | 否 |
| 官方数据委托处理服务合同示范文本（GF-2025-2616）+模拟填写（国家数据局/市场监管总局（Word 版模拟填写后转 PDF），2026-08） | 19 | 有 | 100% | 否 |

## 逐样本字段抽取结果

| 样本 | 抽取成功率 | OCR 页数/耗时 | 优雅降级行为 |
|---|---|---|---|
| 售后回租合同特别条款（真实公章+手写签名扫描版式）（港交所披露易，2026-06） | 5/5（100%） | 4 页 / 293s（73s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（专用条款大表式版式，含骑缝章与横排清单）（港交所披露易，2025-09） | 4/6（67%） | 5 页 / 391s（78s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（全文对角水印+骑缝章，发票号级租赁物清单）（上市公司公告附件（东方财富 PDF 库），2022-05） | 4/6（67%） | 6 页 / 571s（95s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 数电发票样式（官方票样，25 类票样为嵌入图片）（国家税务总局 2024 年第 11 号公告附件（由 doc 附件经 Word 转 PDF），2024-11） | 0/6（0%） | 4 页 / 284s（71s/页，仅关键页） | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方买卖合同示范文本（GF-2000-0101 工业品买卖合同）+模拟填写（市场监管总局合同示范文本库（Word 版模拟填写后转 PDF），2026-08） | 5/6（83%） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方数据委托处理服务合同示范文本（GF-2025-2616）+模拟填写（国家数据局/市场监管总局（Word 版模拟填写后转 PDF），2026-08） | 5/5（100%） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |

### 逐字段明细

| 样本 | 字段 | 真值存在 | 抽到值 | 命中 | 失败模式/状态 |
|---|---|---|---|---|---|
| contract_A | contract_no | 是 | 是 | ✅ |  |
| contract_A | lessor | 是 | 是 | ✅ |  |
| contract_A | lessee | 是 | 是 | ✅ |  |
| contract_A | amount | 是 | 是 | ✅ |  |
| contract_A | term_months | 是 | 是 | ✅ |  |
| contract_A | lease_list_rows | 否(预期不可抽取) | 否 | — | 字段缺失 |
| contract_B | contract_no | 是 | 是 | ✅ |  |
| contract_B | lessor | 是 | 是 | ✅ |  |
| contract_B | lessee | 是 | 是 | ✅ |  |
| contract_B | amount | 是 | 是 | ✅ |  |
| contract_B | term_months | 是 | 是 | 🛑转人审 | term_out_of_bounds |
| contract_B | lease_list_rows | 是 | 是 | ❌ | 跨页表格断裂 |
| contract_C | contract_no | 是 | 是 | ✅ |  |
| contract_C | lessor | 是 | 是 | ✅ |  |
| contract_C | lessee | 是 | 是 | ✅ |  |
| contract_C | amount | 是 | 是 | ✅ |  |
| contract_C | term_months | 是 | 是 | 🛑转人审 | term_inconsistent |
| contract_C | lease_list_rows | 是 | 是 | ❌ | 跨页表格断裂 |
| invoice_style | invoice_no | 是 | 否 | ❌ | 字段缺失 |
| invoice_style | invoice_date | 是 | 否 | ❌ | 字段缺失 |
| invoice_style | seller | 是 | 否 | ❌ | 字段缺失 |
| invoice_style | buyer | 是 | 否 | ❌ | 字段缺失 |
| invoice_style | amount_incl_tax | 是 | 否 | ❌ | 字段缺失 |
| invoice_style | tax_amount | 是 | 否 | ❌ | 字段缺失 |
| template_sale_filled | contract_no | 是 | 是 | ✅ |  |
| template_sale_filled | seller | 是 | 是 | ✅ |  |
| template_sale_filled | buyer | 是 | 是 | ✅ |  |
| template_sale_filled | amount | 是 | 是 | ✅ |  |
| template_sale_filled | term_days | 是 | 是 | ✅ |  |
| template_sale_filled | item_name | 是 | 是 | ❌ | 表格结构差异 |
| template_data_service_filled | contract_no | 否(预期不可抽取) | 否 | — | 字段缺失 |
| template_data_service_filled | party_a | 是 | 是 | ✅ |  |
| template_data_service_filled | party_b | 是 | 是 | ✅ |  |
| template_data_service_filled | amount | 是 | 是 | ✅ |  |
| template_data_service_filled | term_end | 是 | 是 | ✅ |  |
| template_data_service_filled | item_name | 是 | 是 | ✅ |  |

### 字段级交叉校验标记（v3 新增）

| 样本 | 字段 | 原因码 | 级别 | 说明 |
|---|---|---|---|---|
| contract_A | contract.租赁物转让价款 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（74600000） |
| contract_A | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_A | contract.租赁本金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_A | contract.保证金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_A | contract.保证金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.概算租赁本金 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（380000000） |
| contract_B | contract.租赁本金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁物转让价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁本金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.租赁本金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_B | contract.lease_term_months | term_out_of_bounds | 🛑review | 期限 180 个月越出有效区间 [1, 120]（融资租赁业务常见 1 个月–10 年），转人审 |
| contract_C | contract.租金总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.租赁成本 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.租赁物价款 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（435000000） |
| contract_C | contract.租赁物价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.租赁物价款 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.租赁物价款 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（100） |
| contract_C | contract.租赁物价款 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（0） |
| contract_C | contract.保证金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.租赁本金 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| contract_C | contract.lease_term_months | term_inconsistent | 🛑review | 期限多值冲突 [44, 144]（月），不静默采信，转人审 |
| invoice_style | invoice.价税合计 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |

## 失败模式分类汇总

| 失败模式 | 字段数 | 说明 |
|---|---|---|
| 跨页表格断裂 | 2 | |
| 字段缺失 | 6 | |
| 表格结构差异 | 1 | |

**总体抽取率：23/34（68%）；OCR 低置信转人工：0；交叉校验转人审：2；优雅降级全部正常：是**

## v2 → v3 字段级状态变化（交叉校验拦截记录）

| 样本 | 字段 | v2 状态 | v3 状态 |
|---|---|---|---|
| contract_B | term_months | ok/ | validation_review/term_out_of_bounds |
| contract_C | term_months | fail/ocr 误识别（字形混淆） | validation_review/term_inconsistent |

## 与 v1（纯文本层口径）对比

| 样本 | v1 命中 | v3 命中 |
|---|---|---|
| contract_A | 0/5 | 5/5 |
| contract_B | 0/6 | 4/6 |
| contract_C | 0/6 | 4/6 |
| invoice_style | 0/6 | 0/6 |
| template_sale_filled | 5/6 | 5/6 |
| template_data_service_filled | 5/5 | 5/5 |

## 交叉校验命中的人工核对记录（真阳/假阳，2026-08-13）

| 样本 | 字段 | 原因码 | 核对结论 | 说明 |
|---|---|---|---|---|
| contract_C | term_months | term_inconsistent | **真阳（预期拦截）** | v2 中 OCR 将"144 个月"误识为"44 个月"且静默采信错值；v3 多值冲突 [44, 144] 触发，字段置信度置 0 转人审，不再静默通过——本阶段核心目标达成 |
| contract_B | term_months | term_out_of_bounds | **假阳（规则边界）** | 真值 180 个月（风电项目 15 年租期）真实正确，超出默认有效区间 [1,120]；属设计内的软拦截——人审可见完整证据后可放行，机制未静默改值 |
| contract_A/B/C | amount | amount_crosscheck_match | 校验通过（info） | 74600000 / 380000000 / 435000000 大写与小写一致，交叉校验正面证实抽取值 |
| 其余 | — | amount_crosscheck_unavailable | 记录（info） | 仅一种写法，无法交叉，不惩罚 |

注：初版实现曾出现 2 例假阳（C 金额大写碎片"零捌拾元贰角"误配、"仟伍佰万元整"前缀截断误判），
已通过**通用修复**消除：大写碎片负向断言（`(?<![零壹…万亿】])`）、多候选就近配对
（同一金额大写通常紧随其小写）、回溯窗口在句号/分号处截断；非任何样本特例。

## 无回归证明（v3 改动后重跑，2026-08-13）

| 检查项 | 结果 |
|---|---|
| `pytest -q tests/` | 116 passed（v2 时 53 → 新增 63 项：chinese_amount 46 + field_validation 15 + pipeline 集成 2） |
| `python -m eval.run_eval --cases data/cases --mock` | 9/9 指标全达标且数字不变（合成 100 案 0 误伤：validation 仅产生 info 记录） |
| v1 口径外部复跑（`--truth eval/external_truth_v1.jsonl`） | 4 份样本 23 字段与 HEAD 提交结果逐字段完全一致 |
| v2→v3 字段级状态变化 | 仅 2 处：contract_C term_months（fail/ocr 误识别 → validation_review，真阳）、contract_B term_months（ok → validation_review/term_out_of_bounds，假阳边界），见上表 |
