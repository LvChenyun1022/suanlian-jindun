"""live 字段补抽演示案的可复现性与审计测试。"""
from __future__ import annotations

import json
import re
import sys
from types import SimpleNamespace

import pymupdf

from config.settings import LLMSettings
from scripts.make_live_demo_case import CASE_ID, generate_live_demo_case
from src.audit.sqlite_store import SqliteAuditStore
from src.parsing import parse_document
from src.schemas import DocType


def test_live_demo_case_backfill_and_llm_audit(tmp_path, monkeypatch) -> None:
    files = generate_live_demo_case(tmp_path)
    case_dir = tmp_path / CASE_ID

    assert set(files) == {"contract", "invoice", "lease_items"}
    assert not (tmp_path / "labels.jsonl").exists()
    assert all((tmp_path / rel).is_file() for rel in files.values())

    contract_path = case_dir / "contract.pdf"
    with pymupdf.open(contract_path) as document:
        text = "".join(page.get_text() for page in document)
    assert "签署日期" in text
    assert "签订日期" not in text
    sign_date = re.search(r"签署日期[^0-9]*(\d{4}-\d{2}-\d{2})", text).group(1)

    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"sign_date": sign_date})))],
        usage=SimpleNamespace(prompt_tokens=123, completion_tokens=7),
    )

    class FakeCompletions:
        @staticmethod
        def create(**_kwargs):
            return response

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    audit = SqliteAuditStore(tmp_path / "audit.db", "live")
    settings = LLMSettings(api_key="test-key", base_url="https://example.invalid/v1", model="test-model")
    contract, evidences = parse_document(
        contract_path,
        DocType.CONTRACT,
        settings=settings,
        audit=audit,
        source_file=files["contract"],
        case_id=CASE_ID,
    )

    assert contract.sign_date.isoformat() == sign_date
    evidence = next(ev for ev in evidences if ev.field_name == "sign_date")
    assert evidence.bbox is not None
    assert sign_date in evidence.excerpt

    llm_events = [event for event in audit.list_case_events(CASE_ID) if event["event_type"] == "llm_call"]
    audit.close()
    assert len(llm_events) == 1
    assert llm_events[0]["stage"] == "parsing.llm_fill"
    assert llm_events[0]["tokens_prompt"] == 123
    assert llm_events[0]["tokens_completion"] == 7
