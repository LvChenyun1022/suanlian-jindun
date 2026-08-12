【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0040

> 生成时间：2026-08-12T17:31:36.468728+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：25.0 / 100 → **建议通过**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.00 | 0.0 |
| rules | 0.35 | 0.00 | 0.0 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 1.00 | 15.0 |

**路由理由**：压力测试突破阈值情景: stress/extreme；利用率预警 1 条（最高 red）

## 三单核验（通过 9 / 未通过 0）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「银嘉信息有限公司」 vs 发票销售方「银嘉信息有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「联通时科传媒有限公司」 vs 发票购买方「联通时科传媒有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 3,409,399.55 vs 发票价税合计 3,409,399.55（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 3,409,399.55 vs 清单总价值 3,409,399.55（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 3,017,167.74 + 税额 392,231.81 vs 价税合计 3,409,399.55 |
| account_period.consistency | ✅ 通过 | 账期 180 天；开票距签订 18 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0040」 vs 合同编号「HT-2025-0040」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

无。

## 残值与现金流压力测试（NVIDIA H800 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.23 | 0.90 | 1.11 | 否 | 正常回收；月租金 94,706 元，回本 32.4 个月 |
| stress | 0.21 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.79 | 1.14 | 0.80 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 利用率预警

| 类型 | 级别 | 窗口 | 指标 | 说明 |
|---|---|---|---|---|
| long_idle | red | D14-D40 | 2.44% | 连续 27 天利用率低于 10%（T-20 天预警） |

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0040 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-06-17 |
| vendor.name | contract | 1 | (152,715,248,727) | 卖方（出卖人）：银嘉信息有限公司 |
| vendor.credit_code | contract | 1 | (188,697,292,709) | 卖方统一社会信用代码：91************YXYO |
| lessee.name | contract | 1 | (152,643,272,655) | 买方（买受人）：联通时科传媒有限公司 |
| lessee.credit_code | contract | 1 | (188,625,291,637) | 买方统一社会信用代码：91************ROVF |
| subject | contract | 1 | (104,571,432,583) | 标的物：NVIDIA H800 80GB SXM x 17 台；NVIDIA L40S 48GB PCIe x 4 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：3,409,399.55 元 |
| account_days | contract | 1 | (92,535,123,547) | 账期：180 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：96354162 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-07-05 |
| seller.name | invoice | 1 | (128,715,224,727) | 销售方名称：银嘉信息有限公司 |
| buyer.name | invoice | 1 | (128,697,248,709) | 购买方名称：联通时科传媒有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：21 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：143,674.65 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：3,017,167.74 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：392,231.81 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：3,409,399.55 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0040 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0040 |
| items.delivery_date | lease_items | 1 | (116,499,169,511) | 交付日期：2025-07-05 |
| total_value.amount | lease_items | 1 | (128,481,201,493) | 清单总价值：3,409,399.55 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0040-A |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H800 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,222,691) | 序列号（1）：SNUVBLSP65 |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：17 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：186,220.95 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：3,165,756.15 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0040-B |
| items.1.model | lease_items | 1 | (166,589,289,601) | GPU型号（2）：NVIDIA L40S 48GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,226,583) | 序列号（2）：SNQQRJ5W45 |
| items.1.quantity | lease_items | 1 | (150,751,155,763) | 数量（2）：4 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：60,910.85 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,206,529) | 总价（2）：243,643.40 元 |
