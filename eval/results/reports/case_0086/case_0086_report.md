【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0086

> 生成时间：2026-08-11T08:09:41.816408+00:00 ｜ 运行模式：mock
> 本系统为合成数据演示，全部主体/单据均为虚构，不构成授信/投资建议。

## 风险评分：19.0 / 100 → **建议通过**

| 分项 | 权重 | 原始值 | 贡献 |
|---|---|---|---|
| verification | 0.40 | 0.00 | 0.0 |
| rules | 0.35 | 0.00 | 0.0 |
| stress | 0.10 | 1.00 | 10.0 |
| utilization | 0.15 | 0.60 | 9.0 |

**路由理由**：压力测试突破阈值情景: stress/extreme；利用率预警 2 条（最高 orange）

## 三单核验（通过 9 / 未通过 0）

| 核验项 | 结论 | 说明 |
|---|---|---|
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「易动力网络有限公司」 vs 发票销售方「易动力网络有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「联软网络有限公司」 vs 发票购买方「联软网络有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 2,886,699.30 vs 发票价税合计 2,886,699.30（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 2,886,699.30 vs 清单总价值 2,886,699.30（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 2,554,601.15 + 税额 332,098.15 vs 价税合计 2,886,699.30 |
| account_period.consistency | ✅ 通过 | 账期 90 天；开票距签订 26 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0086」 vs 合同编号「HT-2025-0086」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

无。

## 残值与现金流压力测试（NVIDIA A800 80GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.14 | 0.90 | 1.11 | 否 | 正常回收；月租金 80,186 元，回本 32.4 个月 |
| stress | 0.13 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.71 | 1.27 | 0.74 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 利用率预警

| 类型 | 级别 | 窗口 | 指标 | 说明 |
|---|---|---|---|---|
| long_idle | yellow | D62-D179 | 14.49% | 连续 118 天利用率低于 30%（T-1 天预警） |
| sudden_drop | orange | D57-D70 | 14.18% | 周均利用率 66% → 14%，环比骤降超 50%（T-27 天预警） |

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0086 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-02-14 |
| vendor.name | contract | 1 | (152,715,260,727) | 卖方（出卖人）：易动力网络有限公司 |
| vendor.credit_code | contract | 1 | (188,697,292,709) | 卖方统一社会信用代码：91************MSRC |
| lessee.name | contract | 1 | (152,643,248,655) | 买方（买受人）：联软网络有限公司 |
| lessee.credit_code | contract | 1 | (188,625,292,637) | 买方统一社会信用代码：91************1COU |
| subject | contract | 1 | (104,571,265,583) | 标的物：NVIDIA A800 80GB PCIe x 37 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：2,886,699.30 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：90 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：69146787 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-03-12 |
| seller.name | invoice | 1 | (128,715,236,727) | 销售方名称：易动力网络有限公司 |
| buyer.name | invoice | 1 | (128,697,224,709) | 购买方名称：联软网络有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：37 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：69,043.27 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：2,554,601.15 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：332,098.15 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：2,886,699.30 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0086 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0086 |
| items.delivery_date | lease_items | 1 | (116,607,169,619) | 交付日期：2025-03-01 |
| total_value.amount | lease_items | 1 | (142,625,214,637) | 清单总价值：2,886,699.30 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0086-A |
| items.0.model | lease_items | 1 | (166,697,291,709) | GPU型号（1）：NVIDIA A800 80GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,223,691) | 序列号（1）：SNA7DRWJI2 |
| items.0.quantity | lease_items | 1 | (142,661,153,673) | 数量（1）：37 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：78,018.90 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：2,886,699.30 元 |
