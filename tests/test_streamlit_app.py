"""Streamlit Demo 测试（AppTest 无头运行）：渲染、跑案、强制人审留痕。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


@pytest.fixture(scope="module")
def app_ds(tmp_path_factory) -> Path:
    """独立小数据集（20 案），避免污染 data/cases 的审计库。"""
    from src.datagen.generate import generate_dataset

    out = tmp_path_factory.mktemp("appds") / "cases"
    generate_dataset(20, out, 77)
    return out


def _new_at(app_ds: Path) -> AppTest:
    os.environ["JINDUN_CASES_ROOT"] = str(app_ds)
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    return at


def test_app_loads_without_error(app_ds: Path) -> None:
    at = _new_at(app_ds)
    assert not at.exception
    assert at.caption[0].value.startswith("【AI 生成内容")
    # 页脚固定声明
    assert "不构成授信或投资建议" in at.caption[-1].value
    # mock 开关默认开
    assert at.toggle(key="mock_toggle").value is True


def test_app_run_pipeline_and_panels(app_ds: Path) -> None:
    at = _new_at(app_ds)
    at.button(key="run_btn").click().run()
    assert not at.exception
    # 环节耗时表与核验/规则/压力/预警面板均渲染
    assert len(at.dataframe) >= 4
    captions = " ".join(c.value for c in at.caption)
    assert "不构成授信或投资建议" in captions
    # 评分 metric 存在
    assert any("风险评分" in m.label for m in at.metric)


def test_app_forced_review_writes_audit(app_ds: Path) -> None:
    """60–90 分案件：强制人审按钮可用，点击写入审计日志（manual_op）。"""
    import json

    labels = [json.loads(l) for l in (app_ds / "labels.jsonl").read_text(encoding="utf-8").splitlines()]
    fraud = next(r["case_id"] for r in labels if r["is_fraud"])

    at = _new_at(app_ds)
    at.selectbox(key="case_select").set_value(fraud).run()
    at.button(key="run_btn").click().run()
    assert not at.exception
    # 欺诈案应进入人审/拒绝区间
    assert at.session_state["state"].risk_score.grade in ("review", "reject")
    at.button(key="review_approve").click().run()
    assert not at.exception
    assert at.session_state["manual_decision"] == "通过"

    from src.audit.sqlite_store import SqliteAuditStore

    store = SqliteAuditStore(app_ds / "audit.db", "mock")
    events = [e for e in store.list_case_events(fraud) if e["event_type"] == "manual_op"]
    assert store.verify_chain() is True
    store.close()
    assert events and "通过" in events[-1]["detail"]
