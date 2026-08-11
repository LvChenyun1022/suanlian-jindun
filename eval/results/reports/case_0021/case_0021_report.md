【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0021

> 生成时间：2026-08-11T08:09:27.400270+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「济南亿次元网络有限公司」 vs 发票销售方「济南亿次元网络有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「易动力传媒有限公司」 vs 发票购买方「易动力传媒有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 2,711,254.00 vs 发票价税合计 2,711,254.00（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 2,711,254.00 vs 清单总价值 2,711,254.00（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 2,399,339.82 + 税额 311,914.18 vs 价税合计 2,711,254.00 |
| account_period.consistency | ✅ 通过 | 账期 180 天；开票距签订 24 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0021」 vs 合同编号「HT-2025-0021」 |
| cross_case.item_id_duplicate | ❌ 未通过 | 租赁物编号重复登记: {'ZL-POOL-001': ['case_0058']} |
| cross_case.serial_no_duplicate | ❌ 未通过 | 序列号重复登记: {'SNR949A134': ['case_0058']} |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 2 项核验未通过: [cross_case.item_id_duplicate] 租赁物编号重复登记: {'ZL-POOL-001': ['case_0058']}；[cross_case.serial_no_duplicate] 序列号重复登记: {'SNR949A134': ['case_0058']} |
| R77-005 | 77号文 第十八条 第(一)项 | block | 租赁物（1）编号 ZL-POOL-001 已登记于 case_0058；序列号 SNR949A134 已登记于 case_0058 |

## 残值与现金流压力测试（NVIDIA A800 80GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.14 | 0.90 | 1.11 | 否 | 正常回收；月租金 75,313 元，回本 32.4 个月 |
| stress | 0.13 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.71 | 1.27 | 0.74 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0021 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-02-20 |
| vendor.name | contract | 1 | (152,715,284,727) | 卖方（出卖人）：济南亿次元网络有限公司 |
| vendor.credit_code | contract | 1 | (188,697,292,709) | 卖方统一社会信用代码：91************WK2B |
| lessee.name | contract | 1 | (152,643,260,655) | 买方（买受人）：易动力传媒有限公司 |
| lessee.credit_code | contract | 1 | (188,625,288,637) | 买方统一社会信用代码：91************YBK7 |
| subject | contract | 1 | (104,571,265,583) | 标的物：NVIDIA A800 80GB PCIe x 35 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：2,711,254.00 元 |
| account_days | contract | 1 | (92,535,123,547) | 账期：180 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：37167272 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-03-16 |
| seller.name | invoice | 1 | (128,715,260,727) | 销售方名称：济南亿次元网络有限公司 |
| buyer.name | invoice | 1 | (128,697,236,709) | 购买方名称：易动力传媒有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：35 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：68,552.57 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：2,399,339.82 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：311,914.18 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：2,711,254.00 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0021 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0021 |
| items.delivery_date | lease_items | 1 | (116,607,169,619) | 交付日期：2025-04-19 |
| total_value.amount | lease_items | 1 | (142,625,214,637) | 清单总价值：2,711,254.00 元 |
| items.0.item_id | lease_items | 1 | (178,715,248,727) | 租赁物编号（1）：ZL-POOL-001 |
| items.0.model | lease_items | 1 | (166,697,291,709) | GPU型号（1）：NVIDIA A800 80GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,217,691) | 序列号（1）：SNR949A134 |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：35 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：77,464.40 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：2,711,254.00 元 |
