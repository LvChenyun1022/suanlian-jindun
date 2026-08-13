【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0084

> 生成时间：2026-08-13T04:08:58.827318+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「宏晟科技（通辽）有限公司」 vs 发票销售方「宏晟科技（通辽）有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「宏晟贸易（通辽）有限公司」 vs 发票购买方「宏晟贸易（通辽）有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 2,934,423.60 vs 发票价税合计 2,934,423.60（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 2,934,423.60 vs 清单总价值 2,934,423.60（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 2,596,835.04 + 税额 337,588.56 vs 价税合计 2,934,423.60 |
| account_period.consistency | ❌ 未通过 | 账期 0 天；开票距签订 4 天（账期为 0 或开票超账期，交易节奏异常） |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0084」 vs 合同编号「HT-2025-0084」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 1 项核验未通过: [account_period.consistency] 账期 0 天；开票距签订 4 天（账期为 0 或开票超账期，交易节奏异常） |

## 残值与现金流压力测试（NVIDIA A100 80GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.16 | 0.90 | 1.11 | 否 | 正常回收；月租金 81,512 元，回本 32.4 个月 |
| stress | 0.14 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.72 | 1.24 | 0.75 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0084 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-09-29 |
| vendor.name | contract | 1 | (152,715,296,727) | 卖方（出卖人）：宏晟科技（通辽）有限公司 |
| vendor.credit_code | contract | 1 | (188,697,287,709) | 卖方统一社会信用代码：91************LR8R |
| lessee.name | contract | 1 | (152,643,296,655) | 买方（买受人）：宏晟贸易（通辽）有限公司 |
| lessee.credit_code | contract | 1 | (188,625,287,637) | 买方统一社会信用代码：91************JOLT |
| subject | contract | 1 | (104,571,434,583) | 标的物：NVIDIA A100 80GB PCIe x 29 台；NVIDIA RTX 4090 24GB x 22 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：2,934,423.60 元 |
| account_days | contract | 1 | (92,535,112,547) | 账期：0 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：25401328 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-10-03 |
| seller.name | invoice | 1 | (128,715,272,727) | 销售方名称：宏晟科技（通辽）有限公司 |
| buyer.name | invoice | 1 | (128,697,272,709) | 购买方名称：宏晟贸易（通辽）有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：51 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：50,918.33 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：2,596,835.04 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：337,588.56 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：2,934,423.60 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0084 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0084 |
| items.delivery_date | lease_items | 1 | (116,499,169,511) | 交付日期：2025-10-18 |
| total_value.amount | lease_items | 1 | (128,481,201,493) | 清单总价值：2,934,423.60 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0084-A |
| items.0.model | lease_items | 1 | (166,697,291,709) | GPU型号（1）：NVIDIA A100 80GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,217,691) | 序列号（1）：SNNPB7BEJI |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：29 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：89,217.64 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：2,587,311.56 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0084-B |
| items.1.model | lease_items | 1 | (166,589,287,601) | GPU型号（2）：NVIDIA RTX 4090 24GB |
| items.1.serial_no | lease_items | 1 | (154,571,226,583) | 序列号（2）：SNNU29KXFB |
| items.1.quantity | lease_items | 1 | (142,553,153,565) | 数量（2）：22 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：15,777.82 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,206,529) | 总价（2）：347,112.04 元 |
