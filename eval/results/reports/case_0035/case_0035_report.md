【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0035

> 生成时间：2026-08-12T17:31:35.509742+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「方正科技传媒有限公司」 vs 发票销售方「方正科技传媒有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「银嘉信息有限公司」 vs 发票购买方「银嘉信息有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 4,418,052.98 vs 发票价税合计 4,418,052.98（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 4,418,052.98 vs 清单总价值 4,418,052.98（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 3,909,781.40 + 税额 508,271.58 vs 价税合计 4,418,052.98 |
| account_period.consistency | ✅ 通过 | 账期 90 天；开票距签订 22 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0035」 vs 合同编号「HT-2025-0035」 |
| cross_case.item_id_duplicate | ❌ 未通过 | 租赁物编号重复登记: {'ZL-POOL-002': ['case_0076']} |
| cross_case.serial_no_duplicate | ❌ 未通过 | 序列号重复登记: {'SNMT9OPRM3': ['case_0076']} |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 2 项核验未通过: [cross_case.item_id_duplicate] 租赁物编号重复登记: {'ZL-POOL-002': ['case_0076']}；[cross_case.serial_no_duplicate] 序列号重复登记: {'SNMT9OPRM3': ['case_0076']} |
| R77-005 | 77号文 第十八条 第(一)项 | block | 租赁物（1）编号 ZL-POOL-002 已登记于 case_0076；序列号 SNMT9OPRM3 已登记于 case_0076 |

## 残值与现金流压力测试（NVIDIA RTX 4090 24GB）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.24 | 0.90 | 1.11 | 否 | 正常回收；月租金 122,724 元，回本 32.4 个月 |
| stress | 0.22 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.78 | 1.16 | 0.79 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0035 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-09-06 |
| vendor.name | contract | 1 | (152,715,272,727) | 卖方（出卖人）：方正科技传媒有限公司 |
| vendor.credit_code | contract | 1 | (188,697,289,709) | 卖方统一社会信用代码：91************N89U |
| lessee.name | contract | 1 | (152,643,248,655) | 买方（买受人）：银嘉信息有限公司 |
| lessee.credit_code | contract | 1 | (188,625,293,637) | 买方统一社会信用代码：91************QW8F |
| subject | contract | 1 | (104,571,261,583) | 标的物：NVIDIA RTX 4090 24GB x 23 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：4,418,052.98 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：90 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：03291855 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-09-28 |
| seller.name | invoice | 1 | (128,715,248,727) | 销售方名称：方正科技传媒有限公司 |
| buyer.name | invoice | 1 | (128,697,224,709) | 购买方名称：银嘉信息有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：23 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：169,990.50 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：3,909,781.40 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：508,271.58 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：4,418,052.98 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0035 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0035 |
| items.delivery_date | lease_items | 1 | (116,607,169,619) | 交付日期：2025-09-29 |
| total_value.amount | lease_items | 1 | (142,625,214,637) | 清单总价值：4,418,052.98 元 |
| items.0.item_id | lease_items | 1 | (178,715,248,727) | 租赁物编号（1）：ZL-POOL-002 |
| items.0.model | lease_items | 1 | (166,697,287,709) | GPU型号（1）：NVIDIA RTX 4090 24GB |
| items.0.serial_no | lease_items | 1 | (154,679,231,691) | 序列号（1）：SNMT9OPRM3 |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：23 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：192,089.26 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：4,418,052.98 元 |
