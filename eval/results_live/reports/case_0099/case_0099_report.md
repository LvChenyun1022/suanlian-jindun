【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0099

> 生成时间：2026-08-11T08:10:25.696172+00:00 ｜ 运行模式：live
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：68.8 / 100 → **待人工复核（强制）**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.50 | 20.0 |
| rules | 0.35 | 0.85 | 29.8 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.60 | 9.0 |

**路由理由**：风险分进入 60–90 区间，强制待人工复核；三单核验 1 项未通过；规则命中 1 条（最重 R77-003/high）；压力测试突破阈值情景: stress/extreme；利用率预警 3 条（最高 orange）

## 三单核验（通过 8 / 未通过 1）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「华鼎科技（宁德）有限公司」 vs 发票销售方「华鼎科技（宁德）有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「华鼎贸易（宁德）有限公司」 vs 发票购买方「华鼎贸易（宁德）有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 12,555,514.22 vs 发票价税合计 12,555,514.22（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 12,555,514.22 vs 清单总价值 12,555,514.22（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 11,111,074.53 + 税额 1,444,439.69 vs 价税合计 12,555,514.22 |
| account_period.consistency | ❌ 未通过 | 账期 0 天；开票距签订 9 天（账期为 0 或开票超账期，交易节奏异常） |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0099」 vs 合同编号「HT-2025-0099」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

| 规则编号 | 条款引用 | 严重度 | 说明 |
|---|---|---|---|
| R77-003 | 77号文 第十二条 第(二)项 | high | 1 项核验未通过: [account_period.consistency] 账期 0 天；开票距签订 9 天（账期为 0 或开票超账期，交易节奏异常） |

## 残值与现金流压力测试（NVIDIA L40S 48GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.20 | 0.90 | 1.11 | 否 | 正常回收；月租金 348,764 元，回本 32.4 个月 |
| stress | 0.18 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.75 | 1.20 | 0.77 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 利用率预警

| 类型 | 级别 | 窗口 | 指标 | 说明 |
|---|---|---|---|---|
| long_idle | yellow | D63-D179 | 14.87% | 连续 117 天利用率低于 30%（T-1 天预警） |
| sudden_drop | orange | D57-D70 | 12.27% | 周均利用率 70% → 12%，环比骤降超 50%（T-27 天预警） |
| rent_divergence | orange | external | 200.00% | 外部负面信号（模拟接口）: 华鼎贸易（宁德）有限公司: 【模拟】被执行人信息：涉及买卖合同纠纷（虚构样本）；华鼎科技（宁德）有限公司: 【模拟】被执行人信息：涉及买卖合同纠纷（虚构样本） |

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0099 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-07-02 |
| vendor.name | contract | 1 | (152,715,296,727) | 卖方（出卖人）：华鼎科技（宁德）有限公司 |
| vendor.credit_code | contract | 1 | (188,697,289,709) | 卖方统一社会信用代码：91************IANX |
| lessee.name | contract | 1 | (152,643,296,655) | 买方（买受人）：华鼎贸易（宁德）有限公司 |
| lessee.credit_code | contract | 1 | (188,625,286,637) | 买方统一社会信用代码：91************51ZK |
| subject | contract | 1 | (96,571,514,581) | 标的物：NVIDIA L40S 48GB PCIe x 7 台；NVIDIA H100 80GB SXM x 40... |
| total_amount.amount | contract | 1 | (176,553,254,565) | 合同总金额（含税）：12,555,514.22 元 |
| account_days | contract | 1 | (92,535,112,547) | 账期：0 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：48446268 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-07-11 |
| seller.name | invoice | 1 | (128,715,272,727) | 销售方名称：华鼎科技（宁德）有限公司 |
| buyer.name | invoice | 1 | (128,697,272,709) | 购买方名称：华鼎贸易（宁德）有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：91 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：122,099.72 |
| amount_excl_tax.amount | invoice | 1 | (152,625,216,637) | 金额（不含税）：11,111,074.53 |
| tax_amount.amount | invoice | 1 | (92,589,150,601) | 税额：1,444,439.69 |
| amount_incl_tax.amount | invoice | 1 | (164,571,242,583) | 价税合计（含税）：12,555,514.22 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0099 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0099 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-07-27 |
| total_value.amount | lease_items | 1 | (128,373,206,385) | 清单总价值：12,555,514.22 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0099-A |
| items.0.model | lease_items | 1 | (166,697,289,709) | GPU型号（1）：NVIDIA L40S 48GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,225,691) | 序列号（1）：SN5VFUJNG6 |
| items.0.quantity | lease_items | 1 | (142,661,147,673) | 数量（1）：7 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：59,693.06 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,206,637) | 总价（1）：417,851.42 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0099-B |
| items.1.model | lease_items | 1 | (166,589,292,601) | GPU型号（2）：NVIDIA H100 80GB SXM |
| items.1.serial_no | lease_items | 1 | (154,571,228,583) | 序列号（2）：SNWMX1DI27 |
| items.1.quantity | lease_items | 1 | (217,697,228,709) | 数量（2）：40 |
| items.1.unit_price | lease_items | 1 | (142,535,206,547) | 单价（2）：221,115.37 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,214,529) | 总价（2）：8,844,614.80 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0099-C |
| items.2.model | lease_items | 1 | (166,481,291,493) | GPU型号（3）：NVIDIA A800 80GB PCIe |
| items.2.serial_no | lease_items | 1 | (154,463,220,475) | 序列号（3）：SND927BRLF |
| items.2.quantity | lease_items | 1 | (155,517,167,529) | 数量（3）：44 |
| items.2.unit_price | lease_items | 1 | (142,427,201,439) | 单价（3）：74,842.00 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,214,421) | 总价（3）：3,293,048.00 元 |
