【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0047

> 生成时间：2026-08-11T08:09:33.037381+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「昂歌信息科技有限公司」 vs 发票销售方「昂歌信息科技有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「浙大万朋传媒有限公司」 vs 发票购买方「浙大万朋传媒有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 8,736,724.16 vs 发票价税合计 8,736,724.16（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 8,736,724.16 vs 清单总价值 8,736,724.16（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 7,731,614.30 + 税额 1,005,109.86 vs 价税合计 8,736,724.16 |
| account_period.consistency | ✅ 通过 | 账期 180 天；开票距签订 11 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0047」 vs 合同编号「HT-2025-0047」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

无。

## 残值与现金流压力测试（NVIDIA H100 80GB SXM）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.26 | 0.90 | 1.11 | 否 | 正常回收；月租金 242,687 元，回本 32.4 个月 |
| stress | 0.23 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.81 | 1.11 | 0.82 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0047 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-03-11 |
| vendor.name | contract | 1 | (152,715,272,727) | 卖方（出卖人）：昂歌信息科技有限公司 |
| vendor.credit_code | contract | 1 | (188,697,295,709) | 卖方统一社会信用代码：91************MWEL |
| lessee.name | contract | 1 | (152,643,272,655) | 买方（买受人）：浙大万朋传媒有限公司 |
| lessee.credit_code | contract | 1 | (188,625,291,637) | 买方统一社会信用代码：91************RM2T |
| subject | contract | 1 | (104,571,267,583) | 标的物：NVIDIA H100 80GB SXM x 37 台 |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：8,736,724.16 元 |
| account_days | contract | 1 | (92,535,123,547) | 账期：180 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：93940890 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-03-22 |
| seller.name | invoice | 1 | (128,715,248,727) | 销售方名称：昂歌信息科技有限公司 |
| buyer.name | invoice | 1 | (128,697,248,709) | 购买方名称：浙大万朋传媒有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：37 |
| unit_price | invoice | 1 | (152,643,202,655) | 单价（不含税）：208,962.55 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：7,731,614.30 |
| tax_amount.amount | invoice | 1 | (92,589,150,601) | 税额：1,005,109.86 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：8,736,724.16 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0047 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0047 |
| items.delivery_date | lease_items | 1 | (116,607,169,619) | 交付日期：2025-04-23 |
| total_value.amount | lease_items | 1 | (142,625,214,637) | 清单总价值：8,736,724.16 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0047-A |
| items.0.model | lease_items | 1 | (166,697,292,709) | GPU型号（1）：NVIDIA H100 80GB SXM |
| items.0.serial_no | lease_items | 1 | (154,679,226,691) | 序列号（1）：SNPYN37HA1 |
| items.0.quantity | lease_items | 1 | (191,679,202,691) | 数量（1）：37 |
| items.0.unit_price | lease_items | 1 | (142,643,206,655) | 单价（1）：236,127.68 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,214,637) | 总价（1）：8,736,724.16 元 |
