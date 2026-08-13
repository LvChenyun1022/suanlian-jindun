【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0041

> 生成时间：2026-08-13T07:48:54.806280+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：94.0 / 100 → **建议拒绝**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 1.00 | 40.0 |
| rules | 0.35 | 1.00 | 35.0 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.60 | 9.0 |

**路由理由**：风险分超过 90，建议拒绝；三单核验 2 项未通过；规则命中 2 条（最重 R77-005/block）；压力测试突破阈值情景: stress/extreme；利用率预警 1 条（最高 orange）

## 三单核验（通过 7 / 未通过 2）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「群英传媒有限公司」 vs 发票销售方「群英传媒有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「精芯科技有限公司」 vs 发票购买方「精芯科技有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 5,526,720.42 vs 发票价税合计 5,526,720.42（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 5,526,720.42 vs 清单总价值 5,526,720.42（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 4,890,903.03 + 税额 635,817.39 vs 价税合计 5,526,720.42 |
| account_period.consistency | ✅ 通过 | 账期 90 天；开票距签订 15 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0041」 vs 合同编号「HT-2025-0041」 |
| cross_case.item_id_duplicate | ❌ 未通过 | 租赁物编号重复登记: {'ZL-POOL-004': ['case_0087']} |
| cross_case.serial_no_duplicate | ❌ 未通过 | 序列号重复登记: {'SN8CC278CT': ['case_0087']} |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 2 项核验未通过: [cross_case.item_id_duplicate] 租赁物编号重复登记: {'ZL-POOL-004': ['case_0087']}；[cross_case.serial_no_duplicate] 序列号重复登记: {'SN8CC278CT': ['case_0087']} |
| R77-005 | 77号文 第十八条 第(一)项 | block | 租赁物（1）编号 ZL-POOL-004 已登记于 case_0087；序列号 SN8CC278CT 已登记于 case_0087 |

## 残值与现金流压力测试（NVIDIA A100 80GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.16 | 0.90 | 1.11 | 否 | 正常回收；月租金 153,520 元，回本 32.4 个月 |
| stress | 0.14 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.72 | 1.24 | 0.75 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 利用率预警

| 类型 | 级别 | 窗口 | 指标 | 说明 |
|---|---|---|---|---|
| rent_divergence | orange | external | 100.00% | 外部负面信号（模拟接口）: 精芯科技有限公司: 【模拟】动产抵押登记异常提示（虚构样本） |

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0041 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-08-19 |
| vendor.name | contract | 1 | (152,715,248,727) | 卖方（出卖人）：群英传媒有限公司 |
| vendor.credit_code | contract | 1 | (188,697,279,709) | 卖方统一社会信用代码：91************0FIJ |
| lessee.name | contract | 1 | (152,643,248,655) | 买方（买受人）：精芯科技有限公司 |
| lessee.credit_code | contract | 1 | (188,625,290,637) | 买方统一社会信用代码：91************AR3U |
| subject | contract | 1 | (96,571,518,581) | 标的物：NVIDIA A100 80GB PCIe x 29 台；NVIDIA A800 80GB PCIe x ... |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：5,526,720.42 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：90 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：25801864 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-09-03 |
| seller.name | invoice | 1 | (128,715,224,727) | 销售方名称：群英传媒有限公司 |
| buyer.name | invoice | 1 | (128,697,224,709) | 购买方名称：精芯科技有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：93 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：52,590.36 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：4,890,903.03 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：635,817.39 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：5,526,720.42 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0041 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0041 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-10-17 |
| total_value.amount | lease_items | 1 | (128,373,201,385) | 清单总价值：5,526,720.42 元 |
| items.0.item_id | lease_items | 1 | (178,715,248,727) | 租赁物编号（1）：ZL-POOL-004 |
| items.0.model | lease_items | 1 | (166,697,291,709) | GPU型号（1）：NVIDIA A100 80GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,223,691) | 序列号（1）：SN8CC278CT |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：29 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：16,090.34 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,206,637) | 总价（1）：466,619.86 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0041-B |
| items.1.model | lease_items | 1 | (166,589,291,601) | GPU型号（2）：NVIDIA A800 80GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,227,583) | 序列号（2）：SNG2ZOTNSF |
| items.1.quantity | lease_items | 1 | (142,625,153,637) | 数量（2）：46 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：75,513.20 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,214,529) | 总价（2）：3,473,607.20 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0041-C |
| items.2.model | lease_items | 1 | (166,697,291,709) | GPU型号（3）：NVIDIA A100 80GB PCIe |
| items.2.serial_no | lease_items | 1 | (154,463,229,475) | 序列号（3）：SNTVZZNXC0 |
| items.2.quantity | lease_items | 1 | (142,445,153,457) | 数量（3）：18 |
| items.2.unit_price | lease_items | 1 | (142,427,201,439) | 单价（3）：88,138.52 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,214,421) | 总价（3）：1,586,493.36 元 |
