# 正式 live 评测运行说明（2026-08-23）

本目录记录修正生产时序口径后的 100 案全量 live 评测。评测集为 seed 42 生成的
70 个正常案与 30 个欺诈案；跨案件上下文只含此前已完成案件的系统输出，不读取未来标签。

## 运行配置

- 运行环境：Windows，Python 3.13.7（本机解释器 `D:\Python\python.exe`）
- 运行模式：live
- 第三方 OpenAI-compatible 网关：`https://yuanyuaicloud.cn/v1`
- 模型：`deepseek-v4-pro`
- 基线版本：`v2-fixed-2026-08-11`
- API Key：运行时存在，但未写入任何结果或本文档
- 价格参数：`price_per_1k_tokens=0`（未配置实际单价，因此不报告基线人民币费用）

## 结果摘要

- 主系统：召回 83.33%，FPR 0，精确率 100%，F1 0.9091；0 LLM tokens
- 纯 LLM 单案直判：召回 33.33%，FPR 2.86%，精确率 83.33%，F1 0.4762
- 基线补充指标：Balanced Accuracy 0.6524，MCC 0.4298
- 消融召回差值：+50.0pp（valid，目标 ≥15pp）
- 基线调用：306,201 tokens，0 invalid，0 baseline errors
- 分已知注入模式基线召回：a 虚构应收 100%，b 跨案重复资产 0%，c 关联方闭环 0%
- 主系统时耗：均值 0.157s/案，最大 0.267s/案

`eval_results.json` 是逐案与汇总机器可读记录，`eval_results.md` 是人类可读汇总。
`reports/`、`audit_eval.db` 和滚动上下文是本地可再生成产物，默认不提交 Git。
