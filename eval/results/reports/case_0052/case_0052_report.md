【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0052

> 生成时间：2026-08-12T17:31:38.815051+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：74.8 / 100 → **待人工复核（强制）**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.50 | 20.0 |
| rules | 0.35 | 0.85 | 29.8 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 1.00 | 15.0 |

**路由理由**：风险分进入 60–90 区间，强制待人工复核；三单核验 1 项未通过；规则命中 1 条（最重 R77-003/high）；压力测试突破阈值情景: stress/extreme；利用率预警 1 条（最高 red）

## 三单核验（通过 8 / 未通过 1）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「戴硕电子科技有限公司」 vs 发票销售方「戴硕电子科技有限公司」 |
| contract_vs_invoice.buyer_name | ❌ 未通过 | 合同买方「迪摩信息有限公司」 vs 发票购买方「华兴远洋供应链集团有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 5,455,537.85 vs 发票价税合计 5,455,537.85（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 5,455,537.85 vs 清单总价值 5,455,537.85（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 4,827,909.60 + 税额 627,628.25 vs 价税合计 5,455,537.85 |
| account_period.consistency | ✅ 通过 | 账期 30 天；开票距签订 24 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0052」 vs 合同编号「HT-2025-0052」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 1 项核验未通过: [contract_vs_invoice.buyer_name] 合同买方「迪摩信息有限公司」 vs 发票购买方「华兴远洋供应链集团有限公司」 |

## 残值与现金流压力测试（NVIDIA RTX 4090 24GB）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.24 | 0.90 | 1.11 | 否 | 正常回收；月租金 151,543 元，回本 32.4 个月 |
| stress | 0.22 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.78 | 1.16 | 0.79 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 利用率预警

| 类型 | 级别 | 窗口 | 指标 | 说明 |
|---|---|---|---|---|
| long_idle | red | D21-D101 | 2.29% | 连续 81 天利用率低于 10%（T-19 天预警） |

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0052 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-07-14 |
| vendor.name | contract | 1 | (152,715,272,727) | 卖方（出卖人）：戴硕电子科技有限公司 |
| vendor.credit_code | contract | 1 | (188,697,289,709) | 卖方统一社会信用代码：91************00DG |
| lessee.name | contract | 1 | (152,643,248,655) | 买方（买受人）：迪摩信息有限公司 |
| lessee.credit_code | contract | 1 | (188,625,287,637) | 买方统一社会信用代码：91************PFKP |
| subject | contract | 1 | (96,571,515,581) | 标的物：NVIDIA RTX 4090 24GB x 41 台；NVIDIA L40S 48GB PCIe x 2... |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：5,455,537.85 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：30 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：61174112 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-08-07 |
| seller.name | invoice | 1 | (128,715,248,727) | 销售方名称：戴硕电子科技有限公司 |
| buyer.name | invoice | 1 | (128,697,284,709) | 购买方名称：华兴远洋供应链集团有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：85 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：56,798.94 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：4,827,909.60 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：627,628.25 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：5,455,537.85 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0052 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0052 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-08-01 |
| total_value.amount | lease_items | 1 | (128,373,201,385) | 清单总价值：5,455,537.85 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0052-A |
| items.0.model | lease_items | 1 | (166,697,287,709) | GPU型号（1）：NVIDIA RTX 4090 24GB |
| items.0.serial_no | lease_items | 1 | (154,679,218,691) | 序列号（1）：SN1KPT6BLI |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：41 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：16,645.57 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,206,637) | 总价（1）：682,468.37 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0052-B |
| items.1.model | lease_items | 1 | (166,589,289,601) | GPU型号（2）：NVIDIA L40S 48GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,228,583) | 序列号（2）：SNGXLHN1T4 |
| items.1.quantity | lease_items | 1 | (142,553,153,565) | 数量（2）：28 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：60,584.87 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,214,529) | 总价（2）：1,696,376.36 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0052-C |
| items.2.model | lease_items | 1 | (166,481,292,493) | GPU型号（3）：NVIDIA H800 80GB SXM |
| items.2.serial_no | lease_items | 1 | (154,463,221,475) | 序列号（3）：SN923GTE5Y |
| items.2.quantity | lease_items | 1 | (142,643,153,655) | 数量（3）：16 |
| items.2.unit_price | lease_items | 1 | (142,427,206,439) | 单价（3）：192,293.32 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,214,421) | 总价（3）：3,076,693.12 元 |
