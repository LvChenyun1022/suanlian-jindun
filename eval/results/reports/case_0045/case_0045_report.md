【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0045

> 生成时间：2026-08-13T08:35:17.453183+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：91.0 / 100 → **建议拒绝**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 1.00 | 40.0 |
| rules | 0.35 | 1.00 | 35.0 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.00 | 0.0 |

**路由理由**：风险分超过 90，建议拒绝；三单核验 2 项未通过；规则命中 2 条（最重 R77-005/block）；压力测试突破阈值情景: stress/extreme

## 三单核验（通过 7 / 未通过 2）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「时空盒数字科技有限公司」 vs 发票销售方「时空盒数字科技有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「济南亿次元网络有限公司」 vs 发票购买方「济南亿次元网络有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 10,004,931.44 vs 发票价税合计 10,004,931.44（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 10,004,931.44 vs 清单总价值 10,004,931.44（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 8,853,921.63 + 税额 1,151,009.81 vs 价税合计 10,004,931.44 |
| account_period.consistency | ✅ 通过 | 账期 180 天；开票距签订 22 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0045」 vs 合同编号「HT-2025-0045」 |
| cross_case.item_id_duplicate | ❌ 未通过 | 租赁物编号重复登记: {'ZL-POOL-005': ['case_0094']} |
| cross_case.serial_no_duplicate | ❌ 未通过 | 序列号重复登记: {'SNCI14PMUN': ['case_0094']} |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 2 项核验未通过: [cross_case.item_id_duplicate] 租赁物编号重复登记: {'ZL-POOL-005': ['case_0094']}；[cross_case.serial_no_duplicate] 序列号重复登记: {'SNCI14PMUN': ['case_0094']} |
| R77-005 | 77号文 第十八条 第(一)项 | block | 租赁物（1）编号 ZL-POOL-005 已登记于 case_0094；序列号 SNCI14PMUN 已登记于 case_0094 |

## 残值与现金流压力测试（NVIDIA H800 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.23 | 0.90 | 1.11 | 否 | 正常回收；月租金 277,915 元，回本 32.4 个月 |
| stress | 0.21 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.79 | 1.14 | 0.80 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0045 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-10-02 |
| vendor.name | contract | 1 | (152,715,284,727) | 卖方（出卖人）：时空盒数字科技有限公司 |
| vendor.credit_code | contract | 1 | (188,697,290,709) | 卖方统一社会信用代码：91************YYZK |
| lessee.name | contract | 1 | (152,643,284,655) | 买方（买受人）：济南亿次元网络有限公司 |
| lessee.credit_code | contract | 1 | (188,625,289,637) | 买方统一社会信用代码：91************NOPJ |
| subject | contract | 1 | (96,571,514,581) | 标的物：NVIDIA H800 80GB SXM x 45 台；NVIDIA L40S 48GB PCIe x 7... |
| total_amount.amount | contract | 1 | (176,553,254,565) | 合同总金额（含税）：10,004,931.44 元 |
| account_days | contract | 1 | (92,535,123,547) | 账期：180 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：58257446 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-10-24 |
| seller.name | invoice | 1 | (128,715,260,727) | 销售方名称：时空盒数字科技有限公司 |
| buyer.name | invoice | 1 | (128,697,260,709) | 购买方名称：济南亿次元网络有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：68 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：130,204.73 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：8,853,921.63 |
| tax_amount.amount | invoice | 1 | (92,589,150,601) | 税额：1,151,009.81 |
| amount_incl_tax.amount | invoice | 1 | (164,571,242,583) | 价税合计（含税）：10,004,931.44 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0045 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0045 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-10-18 |
| total_value.amount | lease_items | 1 | (128,373,206,385) | 清单总价值：10,004,931.44 元 |
| items.0.item_id | lease_items | 1 | (178,715,248,727) | 租赁物编号（1）：ZL-POOL-005 |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H800 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,227,691) | 序列号（1）：SNCI14PMUN |
| items.0.quantity | lease_items | 1 | (150,751,161,763) | 数量（1）：45 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：181,549.64 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：8,169,733.80 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0045-B |
| items.1.model | lease_items | 1 | (166,589,289,601) | GPU型号（2）：NVIDIA L40S 48GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,222,583) | 序列号（2）：SN5PBVAB55 |
| items.1.quantity | lease_items | 1 | (169,625,175,637) | 数量（2）：7 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：60,652.60 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,206,529) | 总价（2）：424,568.20 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0045-C |
| items.2.model | lease_items | 1 | (166,481,291,493) | GPU型号（3）：NVIDIA A100 80GB PCIe |
| items.2.serial_no | lease_items | 1 | (154,463,235,475) | 序列号（3）：SNRHNSUMEV |
| items.2.quantity | lease_items | 1 | (150,625,161,637) | 数量（3）：16 |
| items.2.unit_price | lease_items | 1 | (142,427,201,439) | 单价（3）：88,164.34 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,214,421) | 总价（3）：1,410,629.44 元 |
