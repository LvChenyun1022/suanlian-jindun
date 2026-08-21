"""LangGraph 等价编排（可选实现，SPEC 4.1）。

仅在安装了 langgraph 时可用；未安装时本模块可安全导入（run_pipeline_graph 抛 ImportError），
不影响纯 Python pipeline（src/pipeline.py）与任何测试。节点与 src/pipeline._STAGES 一一对应。
"""
from __future__ import annotations

import importlib.util

LANGGRAPH_AVAILABLE = importlib.util.find_spec("langgraph") is not None


def run_pipeline_graph(case_id: str, files: dict, run_mode: str = "mock", **kwargs):
    """与 src.pipeline.run_pipeline 行为等价的 LangGraph 编排。"""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph 未安装；请使用 src.pipeline.run_pipeline（纯 Python 实现）")

    from langgraph.graph import END, StateGraph

    from .pipeline import _STAGES, PipelineRuntime, build_default_registry, load_dataset_context
    from .audit.sqlite_store import SqliteAuditStore
    from .guardrails import ToolRegistry  # noqa: F401  （经 build_default_registry 注册）
    from .schemas import PipelineState

    # 与 run_pipeline 共享运行时构建逻辑
    from pathlib import Path

    from config.settings import load_settings

    base = Path(kwargs.get("base_dir", "."))
    audit = SqliteAuditStore(kwargs.get("audit_path") or (base / "audit.db"), run_mode)
    rt = PipelineRuntime(settings=load_settings(), run_mode=run_mode, base_dir=base,
                         audit=audit, tools=build_default_registry(audit))
    _lp = kwargs.get("labels_path")
    if _lp:
        rt.item_index, rt.serial_index, rt.all_cases = load_dataset_context(Path(_lp))

    graph = StateGraph(PipelineState)
    for name, stage in _STAGES:
        graph.add_node(name, lambda state, _s=stage: _s(state, rt))
    for i in range(len(_STAGES) - 1):
        graph.add_edge(_STAGES[i][0], _STAGES[i + 1][0])
    graph.set_entry_point(_STAGES[0][0])
    graph.add_edge(_STAGES[-1][0], END)
    app = graph.compile()
    return app.invoke(PipelineState(case_id=case_id, run_mode=run_mode, files=files))

