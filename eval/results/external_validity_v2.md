# 外部效度测试报告 v2（OCR 增强复测）

- 生成时间：2026-08-12T18:58:38.723367+00:00
- 样本目录：data/external/（不入库、不上传、不再分发）
- OCR：OCR（paddleocr 3.7 + paddlepaddle 3.2.2，250DPI，仅关键页）已启用；低置信字段转人工路由（ocr_low_confidence）。
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
| 售后回租合同（专用条款大表式版式，含骑缝章与横排清单）（港交所披露易，2025-09） | 5/6（83%） | 5 页 / 391s（78s/页，仅关键页） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
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
| contract_B | term_months | 是 | 是 | ✅ |  |
| contract_B | lease_list_rows | 是 | 是 | ❌ | 跨页表格断裂 |
| contract_C | contract_no | 是 | 是 | ✅ |  |
| contract_C | lessor | 是 | 是 | ✅ |  |
| contract_C | lessee | 是 | 是 | ✅ |  |
| contract_C | amount | 是 | 是 | ✅ |  |
| contract_C | term_months | 是 | 是 | ❌ | ocr 误识别（字形混淆） |
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

## 失败模式分类汇总

| 失败模式 | 字段数 | 说明 |
|---|---|---|
| 跨页表格断裂 | 2 | |
| ocr 误识别（字形混淆） | 1 | |
| 字段缺失 | 6 | |
| 表格结构差异 | 1 | |

**总体抽取率：24/34（71%）；OCR 低置信转人工字段数：0；优雅降级全部正常：是**

## 与 v1（纯文本层口径）对比

| 样本 | v1 命中 | v2 命中 |
|---|---|---|
| contract_A | 0/5 | 5/5 |
| contract_B | 0/6 | 5/6 |
| contract_C | 0/6 | 4/6 |
| invoice_style | 0/6 | 0/6 |
| template_sale_filled | 5/6 | 5/6 |
| template_data_service_filled | 5/5 | 5/5 |

## 无回归证明（v2 改动后重跑，2026-08-13）

| 检查项 | 结果 |
|---|---|
| `pytest -q tests/` | 53 passed（与改动前一致） |
| `python -m eval.run_eval --cases data/cases --mock` | 9/9 指标全达标（抽取准确率/核验 F1/欺诈召回/误报/规则命中/证据链覆盖/对抗拦截/时耗/成本），详见 eval_results.{json,md} |
| v1 口径复跑（`--truth eval/external_truth_v1.jsonl`，对比 HEAD 提交结果） | 4 份样本 23 字段 extracted/matched/status/failure_mode 逐字段完全一致 |
| 消融对比（mock 关键词基线，固定于 eval 代码） | 本系统召回 100% vs 基线 33.33%（+66.7pp ≥15pp ✅） |

备注：手写签名/手写日期不属于本测试目标字段（真值未含），未触及"手写字不可识读"模式；
OCR 全程仅跑关键页（共 19 页，平均约 81s/页，累计约 26 分钟），逐页缓存可复跑。
