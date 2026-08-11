"""LLM 补充抽取：仅在正则缺字段时触发；无 Key 或调用失败回退（SPEC 5.2）。"""
from __future__ import annotations

import json

from config.settings import LLMSettings, load_settings

from ..errors import LLMError

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
) -> dict[str, str]:
    """调用 OpenAI-compatible API 补抽缺失字段。

    Raises:
        LLMError: 无 Key（mock 模式不应调用本函数）、超时、非法 JSON 等。
    """
    s = settings or load_settings()
    if s.mock_mode:
        raise LLMError("未配置 LLM_API_KEY，无法 LLM 补抽", code="LLM_NO_KEY")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=s.api_key, base_url=s.base_url, timeout=60)
        resp = client.chat.completions.create(
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
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
    except LLMError:
        raise
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM 返回非法 JSON: {e}", code="LLM_BAD_JSON") from e
    except Exception as e:  # 超时/限流/网络等
        raise LLMError(f"LLM 调用失败: {type(e).__name__}: {e}", code="LLM_CALL_FAILED") from e
    if not isinstance(data, dict):
        raise LLMError("LLM 返回非对象 JSON", code="LLM_BAD_JSON")
    return {str(k): str(v) for k, v in data.items() if k in missing_fields}
