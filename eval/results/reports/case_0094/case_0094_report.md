【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0094

> 生成时间：2026-08-12T17:31:47.100023+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「巨奥传媒有限公司」 vs 发票销售方「巨奥传媒有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「艾提科信科技有限公司」 vs 发票购买方「艾提科信科技有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 1,497,669.81 vs 发票价税合计 1,497,669.81（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 1,497,669.81 vs 清单总价值 1,497,669.81（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 1,325,371.51 + 税额 172,298.30 vs 价税合计 1,497,669.81 |
| account_period.consistency | ✅ 通过 | 账期 30 天；开票距签订 27 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0094」 vs 合同编号「HT-2025-0094」 |
| cross_case.item_id_duplicate | ❌ 未通过 | 租赁物编号重复登记: {'ZL-POOL-005': ['case_0045']} |
| cross_case.serial_no_duplicate | ❌ 未通过 | 序列号重复登记: {'SNCI14PMUN': ['case_0045']} |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 2 项核验未通过: [cross_case.item_id_duplicate] 租赁物编号重复登记: {'ZL-POOL-005': ['case_0045']}；[cross_case.serial_no_duplicate] 序列号重复登记: {'SNCI14PMUN': ['case_0045']} |
| R77-005 | 77号文 第十八条 第(一)项 | block | 租赁物（1）编号 ZL-POOL-005 已登记于 case_0045；序列号 SNCI14PMUN 已登记于 case_0045 |

## 残值与现金流压力测试（NVIDIA H800 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.23 | 0.90 | 1.11 | 否 | 正常回收；月租金 41,602 元，回本 32.4 个月 |
| stress | 0.21 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.79 | 1.14 | 0.80 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0094 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-08-17 |
| vendor.name | contract | 1 | (152,715,248,727) | 卖方（出卖人）：巨奥传媒有限公司 |
| vendor.credit_code | contract | 1 | (188,697,292,709) | 卖方统一社会信用代码：91************NNLY |
| lessee.name | contract | 1 | (152,643,272,655) | 买方（买受人）：艾提科信科技有限公司 |
| lessee.credit_code | contract | 1 | (188,625,291,637) | 买方统一社会信用代码：91************DYXE |
| subject | contract | 1 | (104,571,436,583) | 标的物：NVIDIA H800 80GB SXM x 11 台；NVIDIA RTX 4090 24GB x 39 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：1,497,669.81 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：30 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：46396320 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-09-13 |
| seller.name | invoice | 1 | (128,715,224,727) | 销售方名称：巨奥传媒有限公司 |
| buyer.name | invoice | 1 | (128,697,248,709) | 购买方名称：艾提科信科技有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：50 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：26,507.43 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：1,325,371.51 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：172,298.30 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：1,497,669.81 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0094 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0094 |
| items.delivery_date | lease_items | 1 | (116,499,169,511) | 交付日期：2025-10-16 |
| total_value.amount | lease_items | 1 | (128,481,201,493) | 清单总价值：1,497,669.81 元 |
| items.0.item_id | lease_items | 1 | (178,715,248,727) | 租赁物编号（1）：ZL-POOL-005 |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H800 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,227,691) | 序列号（1）：SNCI14PMUN |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：11 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：78,144.69 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,206,637) | 总价（1）：859,591.59 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0094-B |
| items.1.model | lease_items | 1 | (166,589,287,601) | GPU型号（2）：NVIDIA RTX 4090 24GB |
| items.1.serial_no | lease_items | 1 | (154,571,222,583) | 序列号（2）：SN8CQ56T8B |
| items.1.quantity | lease_items | 1 | (142,553,153,565) | 数量（2）：39 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：16,360.98 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,206,529) | 总价（2）：638,078.22 元 |
