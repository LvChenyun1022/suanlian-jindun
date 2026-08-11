【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0024

> 生成时间：2026-08-11T08:10:08.912738+00:00 ｜ 运行模式：live
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：10.0 / 100 → **建议通过**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.00 | 0.0 |
| rules | 0.35 | 0.00 | 0.0 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.00 | 0.0 |

**路由理由**：压力测试突破阈值情景: stress/extreme

## 三单核验（通过 9 / 未通过 0）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「黄石金承传媒有限公司」 vs 发票销售方「黄石金承传媒有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「新宇龙信息网络有限公司」 vs 发票购买方「新宇龙信息网络有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 6,454,897.70 vs 发票价税合计 6,454,897.70（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 6,454,897.70 vs 清单总价值 6,454,897.70（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 5,712,298.85 + 税额 742,598.85 vs 价税合计 6,454,897.70 |
| account_period.consistency | ✅ 通过 | 账期 180 天；开票距签订 18 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0024」 vs 合同编号「HT-2025-0024」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

无。

## 残值与现金流压力测试（NVIDIA H800 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.23 | 0.90 | 1.11 | 否 | 正常回收；月租金 179,303 元，回本 32.4 个月 |
| stress | 0.21 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.79 | 1.14 | 0.80 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0024 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-07-07 |
| vendor.name | contract | 1 | (152,715,272,727) | 卖方（出卖人）：黄石金承传媒有限公司 |
| vendor.credit_code | contract | 1 | (188,697,286,709) | 卖方统一社会信用代码：91************P8PT |
| lessee.name | contract | 1 | (152,643,284,655) | 买方（买受人）：新宇龙信息网络有限公司 |
| lessee.credit_code | contract | 1 | (188,625,287,637) | 买方统一社会信用代码：91************4P2H |
| subject | contract | 1 | (104,571,438,583) | 标的物：NVIDIA H800 80GB SXM x 25 台；NVIDIA L40S 48GB PCIe x 29 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：6,454,897.70 元 |
| account_days | contract | 1 | (92,535,123,547) | 账期：180 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：60841114 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-07-25 |
| seller.name | invoice | 1 | (128,715,248,727) | 销售方名称：黄石金承传媒有限公司 |
| buyer.name | invoice | 1 | (128,697,260,709) | 购买方名称：新宇龙信息网络有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：54 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：105,783.31 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：5,712,298.85 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：742,598.85 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：6,454,897.70 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0024 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0024 |
| items.delivery_date | lease_items | 1 | (116,499,169,511) | 交付日期：2025-08-19 |
| total_value.amount | lease_items | 1 | (128,481,201,493) | 清单总价值：6,454,897.70 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0024-A |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H800 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,223,691) | 序列号（1）：SNVLF80M7B |
| items.0.quantity | lease_items | 1 | (172,733,183,745) | 数量（1）：25 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：183,068.45 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：4,576,711.25 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0024-B |
| items.1.model | lease_items | 1 | (166,589,289,601) | GPU型号（2）：NVIDIA L40S 48GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,230,583) | 序列号（2）：SNQBYJTHQA |
| items.1.quantity | lease_items | 1 | (142,553,153,565) | 数量（2）：29 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：64,765.05 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,214,529) | 总价（2）：1,878,186.45 元 |
