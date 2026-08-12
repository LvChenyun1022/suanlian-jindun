【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0060

> 生成时间：2026-08-12T18:59:53.134206+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：60.0 / 100 → **待人工复核（强制）**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.50 | 20.0 |
| rules | 0.35 | 0.85 | 29.8 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.00 | 0.0 |

**路由理由**：风险分进入 60–90 区间，强制待人工复核；三单核验 1 项未通过；规则命中 1 条（最重 R77-003/high）；压力测试突破阈值情景: stress/extreme

## 三单核验（通过 8 / 未通过 1）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「新宇龙信息网络有限公司」 vs 发票销售方「新宇龙信息网络有限公司」 |
| contract_vs_invoice.buyer_name | ❌ 未通过 | 合同买方「飞海科技网络有限公司」 vs 发票购买方「中晟安泰重工股份有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 12,413,598.26 vs 发票价税合计 12,413,598.26（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 12,413,598.26 vs 清单总价值 12,413,598.26（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 10,985,485.19 + 税额 1,428,113.07 vs 价税合计 12,413,598.26 |
| account_period.consistency | ✅ 通过 | 账期 90 天；开票距签订 26 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0060」 vs 合同编号「HT-2025-0060」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 1 项核验未通过: [contract_vs_invoice.buyer_name] 合同买方「飞海科技网络有限公司」 vs 发票购买方「中晟安泰重工股份有限公司」 |

## 残值与现金流压力测试（NVIDIA H100 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.26 | 0.90 | 1.11 | 否 | 正常回收；月租金 344,822 元，回本 32.4 个月 |
| stress | 0.23 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.81 | 1.11 | 0.82 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0060 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-05-13 |
| vendor.name | contract | 1 | (152,715,284,727) | 卖方（出卖人）：新宇龙信息网络有限公司 |
| vendor.credit_code | contract | 1 | (188,697,292,709) | 卖方统一社会信用代码：91************GRAX |
| lessee.name | contract | 1 | (152,643,272,655) | 买方（买受人）：飞海科技网络有限公司 |
| lessee.credit_code | contract | 1 | (188,625,293,637) | 买方统一社会信用代码：91************MLDR |
| subject | contract | 1 | (96,571,515,581) | 标的物：NVIDIA H100 80GB SXM x 16 台；NVIDIA H800 80GB SXM x 45... |
| total_amount.amount | contract | 1 | (176,553,254,565) | 合同总金额（含税）：12,413,598.26 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：90 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：00181964 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-06-08 |
| seller.name | invoice | 1 | (128,715,260,727) | 销售方名称：新宇龙信息网络有限公司 |
| buyer.name | invoice | 1 | (128,697,272,709) | 购买方名称：中晟安泰重工股份有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：66 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：166,446.75 |
| amount_excl_tax.amount | invoice | 1 | (152,625,216,637) | 金额（不含税）：10,985,485.19 |
| tax_amount.amount | invoice | 1 | (92,589,150,601) | 税额：1,428,113.07 |
| amount_incl_tax.amount | invoice | 1 | (164,571,242,583) | 价税合计（含税）：12,413,598.26 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0060 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0060 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-06-29 |
| total_value.amount | lease_items | 1 | (128,373,206,385) | 清单总价值：12,413,598.26 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0060-A |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H100 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,224,691) | 序列号（1）：SNB76HSHBB |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：16 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：235,148.36 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：3,762,373.76 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0060-B |
| items.1.model | lease_items | 1 | (166,589,292,601) | GPU型号（2）：NVIDIA H800 80GB SXM |
| items.1.serial_no | lease_items | 1 | (154,571,224,583) | 序列号（2）：SNGM38669U |
| items.1.quantity | lease_items | 1 | (142,553,153,565) | 数量（2）：45 |
| items.1.unit_price | lease_items | 1 | (142,535,206,547) | 单价（2）：185,308.72 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,214,529) | 总价（2）：8,338,892.40 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0060-C |
| items.2.model | lease_items | 1 | (166,481,289,493) | GPU型号（3）：NVIDIA L40S 48GB PCIe |
| items.2.serial_no | lease_items | 1 | (154,463,228,475) | 序列号（3）：SNCBUHFAKJ |
| items.2.quantity | lease_items | 1 | (178,733,183,745) | 数量（3）：5 |
| items.2.unit_price | lease_items | 1 | (142,427,201,439) | 单价（3）：62,466.42 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,206,421) | 总价（3）：312,332.10 元 |
