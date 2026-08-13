# v4 修正说明：数电发票票样归因修正（2026-08-13）

## 归因结论

国家税务总局 2024 年第 11 号公告附件 1《数电发票样式》中的 25 类票样**全部是空白模板**：票面只有字段标签（发票号码：、开票日期：、名称：、价税合计(大写)等），**所有值栏均为空**，无任何可抽取的字段值。依据：公告第三条——"数电发票的票面基本内容包括：发票名称、发票号码、开票日期、购买方信息、销售方信息、项目名称、规格型号、单位、数量、单价、金额、税率/征收率、税额、合计、价税合计、备注、开票人等"——附件票样仅展示上述要素之版式，不承载数值；该结论经官方附件原件逐图人工核验确认。

## 修正内容

1. **v1–v3 报告中 invoice_style 样本 6 个字段"真值存在=是"系真值标注错误**。系统返回 PARSE_FIELD_MISSING、抽取 0/6 是对空白模板的**正确行为**，不是抽取能力缺口，也不是 OCR 问题。
2. eval/external_truth.jsonl 中该样本 6 字段真值已改为"字段值不存在（官方空白模板）"，**自 v4 起剔除出外部效度抽取率分母**，不再计入失败模式"字段缺失"。v1–v3 原报告保留不动，本说明即修正记录。
3. **替代样本**：以官方空白票样（电子发票（增值税专用发票）票样）为底版，叠加全合成数据生成填写版数电票 PDF（invoice_filled_synthetic.pdf，eval/make_filled_invoice.py 生成）：20 位模拟发票号码（公告第四条：号码为 20 位）、模拟开票日期、合成购销双方名称与模拟统一社会信用代码、模拟金额/税率/税额/价税合计（大写与小写一致，触发金额交叉校验 match 路径）。底版图像不改版式，仅填入值；同样不入库、不上传、不再分发。
4. 替代样本测量为**发票版式的首次有效外部测量**（文本层路径）。

## 修正后的口径

- invoice_style：标注"空白模板/不计入分母"，逐字段状态为 expected_absent（预期不可抽取）；
- 总体抽取率分母剔除该样本 6 字段；替代样本字段级结果单列于下表。

---

# 外部效度测试报告 v4（数电票票样归因修正 + 发票版式首次有效测量）

- 生成时间：2026-08-13T08:34:53.421161+00:00
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
| 数电发票填写版（官方空白票样底版+全合成填写，电子发票（增值税专用发票）版式）（底版：国家税务总局 2024 年第 11 号公告附件票样；填写：eval/make_filled_invoice.py，2026-08） | 1 | 有 | 100% | 否 |

## 逐样本字段抽取结果

| 样本 | 抽取成功率 | OCR 页数/耗时 | 优雅降级行为 |
|---|---|---|---|
| 售后回租合同特别条款（真实公章+手写签名扫描版式）（港交所披露易，2026-06） | 5/5（100%） | 4 页 / 293s（73s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（专用条款大表式版式，含骑缝章与横排清单）（港交所披露易，2025-09） | 4/6（67%） | 5 页 / 391s（78s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（全文对角水印+骑缝章，发票号级租赁物清单）（上市公司公告附件（东方财富 PDF 库），2022-05） | 4/6（67%） | 6 页 / 571s（95s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 数电发票样式（官方票样，25 类票样为嵌入图片）（国家税务总局 2024 年第 11 号公告附件（由 doc 附件经 Word 转 PDF），2024-11） | 0/0（N/A） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方买卖合同示范文本（GF-2000-0101 工业品买卖合同）+模拟填写（市场监管总局合同示范文本库（Word 版模拟填写后转 PDF），2026-08） | 5/6（83%） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方数据委托处理服务合同示范文本（GF-2025-2616）+模拟填写（国家数据局/市场监管总局（Word 版模拟填写后转 PDF），2026-08） | 5/5（100%） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 数电发票填写版（官方空白票样底版+全合成填写，电子发票（增值税专用发票）版式）（底版：国家税务总局 2024 年第 11 号公告附件票样；填写：eval/make_filled_invoice.py，2026-08） | 6/6（100%） | — | ✅ structured_parse_error PARSE_FIELD_MISSING |

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
| invoice_style | invoice_no | 否(预期不可抽取) | 否 | — | 字段缺失 |
| invoice_style | invoice_date | 否(预期不可抽取) | 否 | — | 字段缺失 |
| invoice_style | seller | 否(预期不可抽取) | 否 | — | 字段缺失 |
| invoice_style | buyer | 否(预期不可抽取) | 否 | — | 字段缺失 |
| invoice_style | amount_incl_tax | 否(预期不可抽取) | 否 | — | 字段缺失 |
| invoice_style | tax_amount | 否(预期不可抽取) | 否 | — | 字段缺失 |
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
| invoice_filled_synthetic | invoice_no | 是 | 是 | ✅ |  |
| invoice_filled_synthetic | invoice_date | 是 | 是 | ✅ |  |
| invoice_filled_synthetic | seller | 是 | 是 | ✅ |  |
| invoice_filled_synthetic | buyer | 是 | 是 | ✅ |  |
| invoice_filled_synthetic | amount_incl_tax | 是 | 是 | ✅ |  |
| invoice_filled_synthetic | tax_amount | 是 | 是 | ✅ |  |

### 字段级交叉校验标记（v4）

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
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| template_data_service_filled | contract.费用总额 | amount_crosscheck_unavailable | ℹ️info | 仅一种金额写法，无法交叉校验（不惩罚） |
| invoice_filled_synthetic | invoice.价税合计 | amount_crosscheck_match | ℹ️info | 大写/小写交叉校验通过（1000000） |

## 失败模式分类汇总

| 失败模式 | 字段数 | 说明 |
|---|---|---|
| 跨页表格断裂 | 2 | |
| 表格结构差异 | 1 | |

**总体抽取率：29/34（85%）；OCR 低置信转人工：0；交叉校验转人审：2；优雅降级全部正常：是**

## v2 → 本轮（external_validity_v4）字段级状态变化（交叉校验拦截记录）

| 样本 | 字段 | v2 状态 | 本轮状态 |
|---|---|---|---|
| contract_B | term_months | ok/ | validation_review/term_out_of_bounds |
| contract_C | term_months | fail/ocr 误识别（字形混淆） | validation_review/term_inconsistent |
| invoice_style | invoice_no | fail/字段缺失 | expected_absent/字段缺失 |
| invoice_style | invoice_date | fail/字段缺失 | expected_absent/字段缺失 |
| invoice_style | seller | fail/字段缺失 | expected_absent/字段缺失 |
| invoice_style | buyer | fail/字段缺失 | expected_absent/字段缺失 |
| invoice_style | amount_incl_tax | fail/字段缺失 | expected_absent/字段缺失 |
| invoice_style | tax_amount | fail/字段缺失 | expected_absent/字段缺失 |

## 与 v1（纯文本层口径）对比

| 样本 | v1 命中 | 本轮（external_validity_v4）命中 |
|---|---|---|
| contract_A | 0/5 | 5/5 |
| contract_B | 0/6 | 4/6 |
| contract_C | 0/6 | 4/6 |
| invoice_style | 0/6 | 0/0 |
| template_sale_filled | 5/6 | 5/6 |
| template_data_service_filled | 5/5 | 5/5 |
| invoice_filled_synthetic | —（v3 新增样本） | 6/6 |

## 无回归证明（2026-08-13T08:35:29.378021+00:00 实际补跑）

| 命令 | 退出码 | 末行输出 |
|---|---|---|
| `-m pytest -q tests/` | 0 | 116 passed in 13.32s |
| `-m eval.run_eval --cases data/cases --mock` | 0 | 结果已落盘: eval\results\eval_results.json / eval\results\eval_results.md |

**结论：两项全部通过 ✓**

<details><summary><code>-m pytest -q tests/</code> 末尾输出</summary>

```
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 13.32s
```

</details>

<details><summary><code>-m eval.run_eval --cases data/cases --mock</code> 末尾输出</summary>

```
| a_chengxing | 10 | 100.00% | 0.00% |
| b_multi_pledge | 10 | 100.00% | 0.00% |
| c_circular_trade | 10 | 100.00% | 100.00% |
### 未达标项
无。
结果已落盘: eval\results\eval_results.json / eval\results\eval_results.md
```

</details>
