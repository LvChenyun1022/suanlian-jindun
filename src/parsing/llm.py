"""LLM 补充抽取：仅在正则缺字段时触发；无 Key 或调用失败回退（SPEC 5.2）。"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from config.settings import LLMSettings, load_settings

from ..errors import LLMError

if TYPE_CHECKING:
    from ..audit import AuditLogger
    from ..audit.sqlite_store import SqliteAuditStore

_SYSTEM = "你是单据要素抽取器。只输出 JSON，不要输出任何其他文字。"

_PROMPT = """从以下{doc_type}文本中抽取缺失字段，输出 JSON：{{字段名: 值字符串}}。
缺失字段：{missing}
要求：值必须是原文片段（原样截取，不改写）；找不到的字段不要出现在 JSON 中。

文本：
{text}"""


def llm_fill(
    doc_type: str,
    text: str,
    missing_fields: list[str],
    settings: LLMSettings | None = None,
    *,
    audit: AuditLogger | SqliteAuditStore | None = None,
    case_id: str | None = None,
    source_file: str | None = None,
) -> dict[str, str]:
    """调用 OpenAI-compatible API 补抽缺失字段。

    Raises:
        LLMError: 无 Key（mock 模式不应调用本函数）、超时、非法 JSON 等。
    """
    s = settings or load_settings()
    if s.mock_mode:
        raise LLMError("未配置 LLM_API_KEY，无法 LLM 补抽", code="LLM_NO_KEY")
    input_payload = {
        "doc_type": doc_type,
        "missing_fields": missing_fields,
        "source_file": source_file,
        "text_chars": min(len(text), 6000),
        "model": s.model,
    }
    response = None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=s.api_key, base_url=s.base_url, timeout=60)
        response = client.chat.completions.create(
            model=s.model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": _PROMPT.format(
                        doc_type=doc_type, missing="、".join(missing_fields), text=text[:6000]
                    ),
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
    except LLMError:
        raise
    except json.JSONDecodeError as e:
        _log_llm_call(
            audit,
            input_payload,
            {"status": "invalid_json"},
            case_id=case_id,
            response=response,
            detail="字段补抽返回非法 JSON",
        )
        raise LLMError(f"LLM 返回非法 JSON: {e}", code="LLM_BAD_JSON") from e
    except Exception as e:  # 超时/限流/网络等
        _log_llm_call(
            audit,
            input_payload,
            {"status": "failed", "error_type": type(e).__name__},
            case_id=case_id,
            response=response,
            detail=f"字段补抽调用失败: {type(e).__name__}",
        )
        raise LLMError(f"LLM 调用失败: {type(e).__name__}: {e}", code="LLM_CALL_FAILED") from e
    if not isinstance(data, dict):
        _log_llm_call(
            audit,
            input_payload,
            {"status": "invalid_payload"},
            case_id=case_id,
            response=response,
            detail="字段补抽返回非对象 JSON",
        )
        raise LLMError("LLM 返回非对象 JSON", code="LLM_BAD_JSON")
    values = {str(k): str(v) for k, v in data.items() if k in missing_fields}
    _log_llm_call(
        audit,
        input_payload,
        {"status": "ok", "returned_fields": sorted(values)},
        case_id=case_id,
        response=response,
        detail=f"字段补抽完成: {','.join(sorted(values)) or '无返回字段'}",
    )
    return values


def _log_llm_call(
    audit: AuditLogger | SqliteAuditStore | None,
    input_payload: dict,
    output_payload: dict,
    *,
    case_id: str | None,
    response: object | None,
    detail: str,
) -> None:
    """兼容 SQLite 运行时审计与旧 JSONL 审计，且不落原始单据或模型原文。"""
    if audit is None:
        return
    usage = getattr(response, "usage", None)
    tokens_prompt = getattr(usage, "prompt_tokens", None)
    tokens_completion = getattr(usage, "completion_tokens", None)

    from ..audit.sqlite_store import SqliteAuditStore

    if isinstance(audit, SqliteAuditStore):
        audit.log(
            "parsing.llm_fill",
            input_payload,
            output_payload,
            case_id=case_id,
            event_type="llm_call",
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            detail=detail,
        )
    else:
        audit.log("parsing.llm_fill", input_payload, output_payload)
