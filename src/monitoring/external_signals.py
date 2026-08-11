"""模拟外部负面信号接口（本地 mock 数据）。

注意：本模块为模拟接口。真实系统中应对接工商/司法/舆情等外部数据源；
本演示仅返回内置虚构样本，用于演示预警合并逻辑。
"""
from __future__ import annotations

# 模拟接口数据：主体名称（片段）-> 虚构负面信号
_MOCK_SIGNALS: dict[str, list[str]] = {
    "华鼎": ["【模拟】被执行人信息：涉及买卖合同纠纷（虚构样本）"],
    "瑞联": ["【模拟】经营异常名录记录（虚构样本）"],
    "精芯": ["【模拟】动产抵押登记异常提示（虚构样本）"],
}


def fetch_external_signals(party_names: list[str]) -> list[str]:
    """模拟接口：按主体名称检索外部负面信号（本地 mock，无网络访问）。"""
    signals: list[str] = []
    for name in party_names:
        for key, items in _MOCK_SIGNALS.items():
            if key in name:
                signals.extend(f"{name}: {s}" for s in items)
    return signals
