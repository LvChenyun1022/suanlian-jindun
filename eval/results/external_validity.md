# 外部效度 mini-test 报告

- 生成时间：2026-08-12T18:59:21.696748+00:00
- 样本目录：data/external/（不入库、不上传、不再分发）
- OCR：OCR 未启用（--ocr 或 ENABLE_OCR=1 可开启）；扫描件无文本层属预期行为边界。
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

| 样本 | 抽取成功率 | 优雅降级行为 |
|---|---|---|
| 售后回租合同特别条款（真实公章+手写签名扫描版式）（港交所披露易，2026-06） | 0/5（0%） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（专用条款大表式版式，含骑缝章与横排清单）（港交所披露易，2025-09） | 0/6（0%） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 售后回租合同（全文对角水印+骑缝章，发票号级租赁物清单）（上市公司公告附件（东方财富 PDF 库），2022-05） | 0/6（0%） | ✅ structured_parse_error PARSE_NO_TEXT_LAYER |
| 数电发票样式（官方票样，25 类票样为嵌入图片）（国家税务总局 2024 年第 11 号公告附件（由 doc 附件经 Word 转 PDF），2024-11） | 0/6（0%） | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方买卖合同示范文本（GF-2000-0101 工业品买卖合同）+模拟填写（市场监管总局合同示范文本库（Word 版模拟填写后转 PDF），2026-08） | 5/6（83%） | ✅ structured_parse_error PARSE_FIELD_MISSING |
| 官方数据委托处理服务合同示范文本（GF-2025-2616）+模拟填写（国家数据局/市场监管总局（Word 版模拟填写后转 PDF），2026-08） | 5/5（100%） | ✅ structured_parse_error PARSE_FIELD_MISSING |

### 逐字段明细

| 样本 | 字段 | 真值存在 | 抽到值 | 命中 | 失败模式/状态 |
|---|---|---|---|---|---|
| contract_A | contract_no | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_A | lessor | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_A | lessee | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_A | amount | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_A | term_months | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_A | lease_list_rows | 否(预期不可抽取) | 否 | — | 字段缺失 |
| contract_B | contract_no | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_B | lessor | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_B | lessee | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_B | amount | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_B | term_months | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_B | lease_list_rows | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | contract_no | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | lessor | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | lessee | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | amount | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | term_months | 是 | 否 | ❌ | 扫描页无文本层 |
| contract_C | lease_list_rows | 是 | 否 | ❌ | 扫描页无文本层 |
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
| 扫描页无文本层 | 17 | |
| 字段缺失 | 6 | |
| 表格结构差异 | 1 | |
| 水印干扰 | 0 | 合同 C 全文对角水印，但因无文本层未触及该失败面（--ocr 复测触及） |
| 跨页表格断裂 | 0 | 合同 B/C 清单均为跨页表格，但因无文本层未触及该失败面（--ocr 复测触及） |

**总体抽取率：10/34（29%）；OCR 低置信转人工字段数：0；优雅降级全部正常：是**
