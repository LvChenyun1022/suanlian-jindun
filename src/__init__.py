"""suanlian-jindun 核心包：算力融资租赁风控演示系统。

子模块规划（见 SPEC.md）：
- schemas      全部数据 schema 的 Pydantic 模型
- datagen      合成数据生成
- parsing      单据解析（PDF -> 要素 + 字段级证据）
- verification 三单核验
- rules        77号文规则引擎
- stress       GPU 残值与现金流压力测试
- alerts       利用率预警
- scoring      风险评分
- report       证据链报告
- audit        审计日志（哈希链）
- guardrails   合规护栏
- pipeline     纯 Python pipeline 编排（LangGraph 为可选等价实现）
"""
