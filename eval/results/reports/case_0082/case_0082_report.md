【AI 生成内容 · 合成演示数据，不构成任何授信/投资建议】
# 证据链报告 — case_0082

> 生成时间：2026-08-11T08:09:40.904142+00:00 ｜ 运行模式：mock
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
| contract_vs_invoice.seller_name | ✅ 通过 | 合同卖方「晖来计算机网络有限公司」 vs 发票销售方「晖来计算机网络有限公司」 |
| contract_vs_invoice.buyer_name | ✅ 通过 | 合同买方「恩悌信息有限公司」 vs 发票购买方「恩悌信息有限公司」 |
| amount.contract_vs_invoice | ✅ 通过 | 合同 3,590,213.58 vs 发票价税合计 3,590,213.58（容差 1.0） |
| amount.contract_vs_lease | ✅ 通过 | 合同 3,590,213.58 vs 清单总价值 3,590,213.58（容差 1.0） |
| invoice.tax_reconciliation | ✅ 通过 | 不含税 3,177,180.16 + 税额 413,033.42 vs 价税合计 3,590,213.58 |
| account_period.consistency | ✅ 通过 | 账期 30 天；开票距签订 9 天 |
| lease.contract_no_link | ✅ 通过 | 清单关联合同号「HT-2025-0082」 vs 合同编号「HT-2025-0082」 |
| cross_case.item_id_duplicate | ✅ 通过 | 无跨案件重复租赁物编号 |
| cross_case.serial_no_duplicate | ✅ 通过 | 无跨案件重复序列号 |

## 规则命中

无。

## 残值与现金流压力测试（NVIDIA A100 80GB PCIe）

| 情景 | 残值率 | LTV | DSCR | 突破阈值 | 说明 |
|---|---|---|---|---|---|
| base | 0.16 | 0.90 | 1.11 | 否 | 正常回收；月租金 99,728 元，回本 32.4 个月 |
| stress | 0.14 | 0.99 | 0.89 | 是 | 利用率 -20%，租金回收率同步 -20% |
| extreme | 0.72 | 1.24 | 0.75 | 是 | 单一客户违约（集中度 100%），第 6 个月违约、处置折扣 30% |

回本周期：32.4 个月。

## 证据链明细（字段级）

| 字段 | 单据 | 页码 | 坐标 (pt, 左下原点) | 原文片段 |
|---|---|---|---|---|
| contract_no | contract | 1 | (116,751,186,763) | 合同编号：HT-2025-0082 |
| sign_date | contract | 1 | (116,733,169,745) | 签订日期：2025-04-06 |
| vendor.name | contract | 1 | (152,715,284,727) | 卖方（出卖人）：晖来计算机网络有限公司 |
| vendor.credit_code | contract | 1 | (188,697,287,709) | 卖方统一社会信用代码：91************XX64 |
| lessee.name | contract | 1 | (152,643,248,655) | 买方（买受人）：恩悌信息有限公司 |
| lessee.credit_code | contract | 1 | (188,625,296,637) | 买方统一社会信用代码：91************FWMX |
| subject | contract | 1 | (100,571,553,582) | 标的物：NVIDIA A100 80GB PCIe x 6 台；NVIDIA A800 80GB PCIe x 5... |
| total_amount.amount | contract | 1 | (176,553,249,565) | 合同总金额（含税）：3,590,213.58 元 |
| account_days | contract | 1 | (92,535,118,547) | 账期：30 天 |
| invoice_no | invoice | 1 | (116,751,160,763) | 发票号码：35329711 |
| invoice_date | invoice | 1 | (116,733,169,745) | 开票日期：2025-04-15 |
| seller.name | invoice | 1 | (128,715,260,727) | 销售方名称：晖来计算机网络有限公司 |
| buyer.name | invoice | 1 | (128,697,224,709) | 购买方名称：恩悌信息有限公司 |
| item_name | invoice | 1 | (212,679,330,691) | 货物或应税劳务、服务名称：*电子设备*GPU加速卡 |
| quantity | invoice | 1 | (92,661,103,673) | 数量：55 |
| unit_price | invoice | 1 | (152,643,197,655) | 单价（不含税）：57,766.91 |
| amount_excl_tax.amount | invoice | 1 | (152,625,210,637) | 金额（不含税）：3,177,180.16 |
| tax_amount.amount | invoice | 1 | (92,589,142,601) | 税额：413,033.42 |
| amount_incl_tax.amount | invoice | 1 | (164,571,237,583) | 价税合计（含税）：3,590,213.58 元 |
| list_no | lease_items | 1 | (116,751,161,763) | 清单编号：QD-0082 |
| contract_no | lease_items | 1 | (140,733,210,745) | 关联合同编号：HT-2025-0082 |
| items.delivery_date | lease_items | 1 | (116,391,169,403) | 交付日期：2025-05-07 |
| total_value.amount | lease_items | 1 | (128,373,201,385) | 清单总价值：3,590,213.58 元 |
| items.0.item_id | lease_items | 1 | (178,715,231,727) | 租赁物编号（1）：ZL-0082-A |
| items.0.model | lease_items | 1 | (166,697,291,709) | GPU型号（1）：NVIDIA A100 80GB PCIe |
| items.0.serial_no | lease_items | 1 | (154,679,223,691) | 序列号（1）：SNH5R2TYL0 |
| items.0.quantity | lease_items | 1 | (142,661,147,673) | 数量（1）：6 |
| items.0.unit_price | lease_items | 1 | (142,643,201,655) | 单价（1）：84,569.77 元 |
| items.0.purchase_price.amount | lease_items | 1 | (142,625,206,637) | 总价（1）：507,418.62 元 |
| items.1.item_id | lease_items | 1 | (178,607,229,619) | 租赁物编号（2）：ZL-0082-B |
| items.1.model | lease_items | 1 | (166,589,291,601) | GPU型号（2）：NVIDIA A800 80GB PCIe |
| items.1.serial_no | lease_items | 1 | (154,571,218,583) | 序列号（2）：SNE1I18RLU |
| items.1.quantity | lease_items | 1 | (178,733,183,745) | 数量（2）：5 |
| items.1.unit_price | lease_items | 1 | (142,535,201,547) | 单价（2）：78,020.20 元 |
| items.1.purchase_price.amount | lease_items | 1 | (142,517,206,529) | 总价（2）：390,101.00 元 |
| items.2.item_id | lease_items | 1 | (178,499,231,511) | 租赁物编号（3）：ZL-0082-C |
| items.2.model | lease_items | 1 | (166,481,289,493) | GPU型号（3）：NVIDIA L40S 48GB PCIe |
| items.2.serial_no | lease_items | 1 | (154,463,227,475) | 序列号（3）：SNJXFYM86W |
| items.2.quantity | lease_items | 1 | (142,445,153,457) | 数量（3）：44 |
| items.2.unit_price | lease_items | 1 | (142,427,201,439) | 单价（3）：61,197.59 元 |
| items.2.purchase_price.amount | lease_items | 1 | (142,409,214,421) | 总价（3）：2,692,693.96 元 |
