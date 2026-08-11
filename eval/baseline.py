"""消融基线："纯 LLM 直判"（SPEC 第 6 节指标 9）。

⚠️ 本模块常量固定（BASELINE_VERSION），作为对照组不得随主系统调参而变动。
- live：把三单据文本直接发给 LLM，让其直判欺诈（固定提示词，temperature=0，
  严格 JSON 输出，response_format=json_object）；
- mock：用简单关键词规则代替（固定关键词表），不调用 LLM。

v2-fixed-2026-08-11 修复（消融基线有效性复核）：
1. v1 用子串 `"FRAUD" in answer` 解析，空响应/截断/非预期文本会被静默误分类；
   v2 要求严格 JSON 并按 schema 校验，解析失败/字段缺失/空响应/重试后仍失败
   一律标记 label="invalid"，绝不默认映射为 fraud 或 normal。
2. v1 提示词"判断是否存在欺诈嫌疑"门槛过低且只要求回答 FRAUD/NORMAL；
   v2 要求"仅依据客观事实证据判断，无充分证据必须判正常"，无任何从严诱导措辞。
3. v1 max_tokens=8 有截断风险；v2 max_tokens=300 且开启 json_object 模式。
4. v2 返回完整逐案记录（raw response / finish_reason / HTTP 状态 / token / 重试次数），
   供 eval/results/baseline_audit.jsonl 审计留痕。
"""
from __future__ import annotations

import json
import random
import re
import time
from typing import Any

from config.settings import LLMSettings

BASELINE_VERSION = "v2-fixed-2026-08-11"

# mock 基线关键词表（固定）：仅看"账期：0 天"这一类表面异常
MOCK_KEYWORDS = ["账期：0 天"]

# live 基线提示词（固定）：不做任何结构化解析/核验/规则，仅直判。
# 要求严格 JSON 输出；明确"无充分客观证据时必须判正常"；不含任何诱导性措辞。
BASELINE_PROMPT = """你是融资租赁风控审核员。以下是一份案件的购销合同、增值税发票和租赁物清单全文。
请仅依据单据中的客观事实，判断该案件是否存在欺诈（例如：合同与发票主体名称不一致、金额勾稽明显不符、租赁物信息异常、贸易背景明显矛盾等）。
如果没有充分的客观证据表明存在欺诈，必须判定为正常（is_fraud=false，evidence 为空数组）。

严格输出如下 JSON，不要输出任何其他内容：
{{"is_fraud": true 或 false, "confidence": 0 到 1 之间的数字, "evidence": ["支撑判断的客观证据片段"]}}

【购销合同】
{contract}

【增值税发票】
{invoice}

【租赁物清单】
{lease_items}"""

# 429/5xx 退避表（秒），jitter 由固定种子随机数产生；最多重试 3 次
BACKOFF_SECONDS = [2, 4, 8, 16]
MAX_RETRIES = 3
MAX_TOKENS = 300
DOC_CHAR_LIMIT = 2500


def predict_baseline_mock(texts: dict[str, str]) -> bool:
    """mock 关键词直判：任一单据含固定关键词即判欺诈。"""
    return any(kw in text for kw in MOCK_KEYWORDS for text in texts.values())


def build_baseline_prompt(texts: dict[str, str]) -> str:
    """构造基线 prompt（截断长度固定，逐案审计需留存完整 prompt）。"""
    return BASELINE_PROMPT.format(
        contract=texts["contract"][:DOC_CHAR_LIMIT],
        invoice=texts["invoice"][:DOC_CHAR_LIMIT],
        lease_items=texts["lease_items"][:DOC_CHAR_LIMIT],
    )


def parse_baseline_response(raw: str | None) -> tuple[str, str | None, dict[str, Any] | None]:
    """解析基线 raw response。

    Returns:
        (label, invalid_reason, payload)
        label ∈ {"fraud", "normal", "invalid"}；payload 为解析出的 JSON（成功时）。
        空响应 / JSON 解析失败 / is_fraud 字段缺失或类型不符 → invalid。
    """
    if raw is None or not raw.strip():
        return "invalid", "empty_response", None
    text = raw.strip()
    # 容忍 markdown 代码围栏，提取首个 { 到末个 } 之间的内容
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if m:
            text = m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return "invalid", "json_parse_error", None
    try:
        payload = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return "invalid", "json_parse_error", None
    if not isinstance(payload, dict) or "is_fraud" not in payload:
        return "invalid", "schema_missing_is_fraud", payload if isinstance(payload, dict) else None
    val = payload["is_fraud"]
    if isinstance(val, bool):
        return ("fraud" if val else "normal"), None, payload
    if isinstance(val, str) and val.strip().lower() in ("true", "false"):
        # 字符串形式真值： coerce 并在记录中标注（不改变 invalid 口径的严格性，仅容错）
        payload["is_fraud_coerced_from_string"] = True
        return ("fraud" if val.strip().lower() == "true" else "normal"), None, payload
    return "invalid", "schema_bad_is_fraud_type", payload


def _record_base(prompt: str, settings: LLMSettings) -> dict[str, Any]:
    return {
        "baseline_version": BASELINE_VERSION,
        "model": settings.model,
        "prompt": prompt,
        "label": "invalid",
        "invalid_reason": None,
        "raw_response": None,
        "finish_reason": None,
        "http_status": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "retry_count": 0,
        "error": None,
        "saw_429": False,
    }


def predict_baseline_live(
    texts: dict[str, str],
    settings: LLMSettings,
    *,
    seed: int | str = 0,
) -> dict[str, Any]:
    """纯 LLM 直判（v2）。返回完整逐案记录 dict；label="invalid" 表示无法有效判定。

    - temperature=0，response_format=json_object；
    - 429/5xx/超时/连接错误：指数退避 + jitter（2/4/8/16s），最多重试 3 次；
    - seed 固定 jitter 随机序列（按案件传入，保证可复现）。
    """
    from openai import OpenAI
    from openai import APIStatusError

    prompt = build_baseline_prompt(texts)
    rec = _record_base(prompt, settings)
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, timeout=90)

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            base = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
            jitter = random.Random(f"{seed}:{attempt}").uniform(0, base * 0.5)
            time.sleep(base + jitter)
        try:
            raw_resp = client.chat.completions.with_raw_response.create(
                model=settings.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            rec["http_status"] = raw_resp.http_response.status_code
            resp = raw_resp.parse()
            choice = resp.choices[0] if resp.choices else None
            rec["finish_reason"] = choice.finish_reason if choice else None
            rec["raw_response"] = (choice.message.content if choice else None) or ""
            usage = resp.usage
            rec["prompt_tokens"] = usage.prompt_tokens if usage else 0
            rec["completion_tokens"] = usage.completion_tokens if usage else 0
            rec["retry_count"] = attempt
            label, reason, _payload = parse_baseline_response(rec["raw_response"])
            rec["label"] = label
            rec["invalid_reason"] = reason
            if label == "invalid" and reason == "empty_response" and attempt < MAX_RETRIES:
                continue  # 空响应按可重试处理
            return rec
        except APIStatusError as e:
            rec["http_status"] = e.status_code
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            rec["retry_count"] = attempt
            if e.status_code == 429:
                rec["saw_429"] = True
            # 429 与 5xx 可重试；其他 4xx（如 400）重试无意义，直接判 invalid
            if e.status_code == 429 or e.status_code >= 500:
                if attempt < MAX_RETRIES:
                    continue
            rec["label"] = "invalid"
            rec["invalid_reason"] = "api_error"
            return rec
        except Exception as e:  # 超时/连接错误等
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            rec["retry_count"] = attempt
            if attempt < MAX_RETRIES:
                continue
            rec["label"] = "invalid"
            rec["invalid_reason"] = "request_error"
            return rec
    # 理论不可达
    rec["invalid_reason"] = rec["invalid_reason"] or "exhausted"
    return rec
