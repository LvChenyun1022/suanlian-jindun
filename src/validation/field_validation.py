"""字段级交叉校验（v3）：金额大写/小写交叉 + 期限边界/一致性。

设计原则（与 SPEC 一致）：通用实现，0 token，正则优先；标记 → 字段置信度置 0
转人审路由，绝不静默替换值；只有一种写法/无法解析时不惩罚、如实记录。
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from config.settings import (
    TERM_CONSISTENCY_TOLERANCE_MONTHS,
    TERM_MONTHS_MAX,
    TERM_MONTHS_MIN,
)
from src.parsing.chinese_amount import (
    crosscheck_amount,
    parse_arabic_amount,
    parse_chinese_amount,
    parse_chinese_int,
)
from src.schemas import ValidationFlag

# ---------------------------------------------------------------- 通用模式

_AMOUNT_LABELS = (
    "合同总金额|合同金额|租金总额|保证金|价税合计|费用总额|"
    "租赁物转让价款|转让价款|租赁本金|租赁成本|租赁物价款|概算租赁本金"
)
_DAXIE_RE = re.compile(
    r"(?<![零壹贰叁肆伍陆柒捌玖拾佰仟万亿】])"  # 防止截取上一子句大写的尾部碎片（如"零捌拾元贰角"）
    r"(?:【?(?:人民币)?[零壹贰叁肆伍陆柒捌玖拾佰仟万亿]+】?[元圆][零壹贰叁肆伍陆柒捌玖角分]*(?:整|正)?"
    r"|【?[零壹贰叁肆伍陆柒捌玖]+[角分])")
_ARABIC_RE = re.compile(r"[¥￥]?\s*【?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*】?\s*(?:万元|亿元|万|亿|元)?")

_TERM_LABEL_RE = re.compile(r"(?:租赁期限|合同期限|借款期限|期限)")
_TERM_CAND_RES = [
    # 标签后 N 字符内的期限值（含【】括号容忍、年/月、中文数字）
    re.compile(
        r"(?:租赁期限|合同期限|借款期限|期限)[^0-9零壹贰叁肆伍陆柒捌玖一二三四五六七八九十]{0,20}"
        r"【?([0-9]{1,3})】?\s*个?月"),
    re.compile(
        r"(?:租赁期限|合同期限|借款期限|期限)[^0-9零壹贰叁肆伍陆柒捌玖一二三四五六七八九十]{0,20}"
        r"【?([0-9]{1,2})】?\s*个?年"),
    re.compile(
        r"(?:租赁期限|合同期限|借款期限|期限)[^。]{0,20}?"
        r"([零壹贰叁肆伍陆柒捌玖拾佰仟一二三四五六七八九十百]{2,8})个?月"),
    # 大表式版式：值在标签前行（如 "【180】月，含宽限期【12】月。租赁期限自起租日起算"）
    re.compile(r"【?([0-9]{1,3})】?\s*个?月(?=[^\n]{0,25}租赁期限)"),
    # 相对到期表述："起租日后第144个月对应日"（融资租赁通用条款）
    re.compile(r"起租日后第【?([0-9]{1,3})】?个月"),
    re.compile(r"(?:租赁期限|合同期限)[^。]{0,20}?【?([0-9]{1,2})】?\s*个?年"),
]

_DATE = r"([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})"
_START_DATE_RE = re.compile(r"(?:起租日|生效日|签订日期|起始日)[^0-9]{0,12}" + _DATE)
_END_DATE_RE = re.compile(r"(?:到期日|届满日|终止日|有效期至)[^0-9]{0,12}" + _DATE)


def mask_value(text: str) -> str:
    """原始值掩码：数字段保留首 2 位，其余用 * 代替（审计留痕用）。"""
    return re.sub(r"\d{3,}", lambda m: m.group(0)[:2] + "*" * (len(m.group(0)) - 2), text)


def _parse_date(text: str) -> date | None:
    """通用日期解析：YYYY年M月D日 / YYYY-MM-DD / YYYY/M/D。"""
    m = re.match(r"([0-9]{4})\s*(?:年|[-/])\s*([0-9]{1,2})\s*(?:月|[-/])\s*([0-9]{1,2})\s*日?", text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _months_between(d1: date, d2: date) -> float:
    return (d2 - d1).days / 30.4375


# ---------------------------------------------------------------- 金额大写/小写交叉校验


def extract_amount_pairs(text: str) -> list[dict]:
    """在单据文本中按金额标签定位子句，抽取同一子句内的大写/阿拉伯两种写法。

    Returns: [{label, daxie, arabic, excerpt}]，daxie/arabic 为原文片段（可为 None）。
    """
    pairs: list[dict] = []
    for m in re.finditer(_AMOUNT_LABELS, text):
        label = m.group(0)
        # 通用版式容忍：大写常出现在标签前一行，窗口向前回溯 50 字符、向后 90 字符；
        # 回溯部分在最后一个句号/分号处截断，避免串入上一子句的大写
        back = text[max(0, m.start() - 50): m.start()]
        bstop = re.search(r"[。；;][^。；;]*$", back)
        if bstop:
            back = back[bstop.start() + 1:]
        fwd = text[m.start(): m.start() + 90]
        fstop = re.search(r"[。；;]", fwd)
        if fstop:
            fwd = fwd[: fstop.start()]
        window = back + fwd
        daxies = list(_DAXIE_RE.finditer(window))
        arabics = list(_ARABIC_RE.finditer(window))
        arabic_m = None
        if len(arabics) == 1:
            arabic_m = arabics[0]
        elif len(arabics) > 1:
            # 多个阿拉伯候选：优先带 ¥/￥/【 前缀或紧邻"小写"的（通用启发式）
            pref = [a for a in arabics
                    if "¥" in a.group(0) or "￥" in a.group(0) or "【" in a.group(0)
                    or "小写" in window[max(0, a.start() - 4): a.start()]]
            if len(pref) == 1:
                arabic_m = pref[0]
        daxie_m = None
        if len(daxies) == 1:
            daxie_m = daxies[0]
        elif len(daxies) > 1:
            # 多个大写候选：同一金额的大写通常紧随其小写，取与小写最近的；
            # 无小写时取与标签最近的（通用就近原则，防止跨子句误配）
            anchor = arabic_m.end() if arabic_m else len(back)
            daxie_m = min(daxies, key=lambda d: abs(d.start() - anchor))
        pairs.append({
            "label": label,
            "daxie": daxie_m.group(0) if daxie_m else None,
            "arabic": arabic_m.group(0) if arabic_m else None,
            "excerpt": window.strip()[:80],
        })
    return pairs


def crosscheck_amount_fields(
    text: str,
    field_prefix: str,
    parsed_values: dict[str, float] | None = None,
) -> list[ValidationFlag]:
    """对单据文本做金额大写/小写交叉校验，输出 ValidationFlag 列表。

    parsed_values: {label: 已解析金额}（可选）——交叉通过后若与解析值冲突，同样标记。
    """
    flags: list[ValidationFlag] = []
    seen: set[tuple[str, str, str]] = set()
    for pair in extract_amount_pairs(text):
        key = (pair["label"], pair["daxie"] or "", pair["arabic"] or "")
        if key in seen:
            continue
        seen.add(key)
        fname = f"{field_prefix}.{pair['label']}"
        status, d, a = crosscheck_amount(pair["daxie"], pair["arabic"])
        raw = mask_value(f"大写={pair['daxie'] or '无'} 小写={pair['arabic'] or '无'}")
        if status == "mismatch":
            flags.append(ValidationFlag(
                field_name=fname, reason_code="amount_mismatch_daxie",
                severity="review",
                detail=f"大写金额 {d} 与小写金额 {a} 不一致，字段置信度置 0 转人审",
                raw_masked=raw))
        elif status == "parse_failed":
            flags.append(ValidationFlag(
                field_name=fname, reason_code="amount_parse_failed",
                severity="review",
                detail="金额写法存在但解析失败（疑似 OCR 误识别），转人审",
                raw_masked=raw))
        elif status == "match":
            if parsed_values and pair["label"] in parsed_values:
                pv = Decimal(str(parsed_values[pair["label"]]))
                if abs(d - pv) > Decimal("0.01"):  # type: ignore[arg-type]
                    flags.append(ValidationFlag(
                        field_name=fname, reason_code="amount_mismatch_daxie",
                        severity="review",
                        detail=f"票面大写/小写一致（{d}），但与抽取值 {pv} 冲突，转人审",
                        raw_masked=raw))
                    continue
            flags.append(ValidationFlag(
                field_name=fname, reason_code="amount_crosscheck_match",
                severity="info",
                detail=f"大写/小写交叉校验通过（{d}）",
                raw_masked=raw))
        else:  # unavailable：只有一种写法，无法交叉，不惩罚
            flags.append(ValidationFlag(
                field_name=fname, reason_code="amount_crosscheck_unavailable",
                severity="info",
                detail="仅一种金额写法，无法交叉校验（不惩罚）",
                raw_masked=raw))
    return flags


# ---------------------------------------------------------------- 期限解析 / 边界 / 一致性


def extract_term_candidates(text: str) -> list[dict]:
    """抽取文本中全部期限候选值（统一换算为月）。无法解析的候选同样保留（记 raw）。"""
    cands: list[dict] = []
    for rx in _TERM_CAND_RES:
        for m in rx.finditer(text):
            raw = m.group(0)
            token = m.group(1)
            # 通用排除：宽限期/免租期等其他期限类型不作为租赁期限候选
            ctx_before = text[max(0, m.start() - 6): m.start()]
            if re.search(r"宽限|免租|缓征", ctx_before):
                continue
            months: int | None = None
            is_year = bool(re.search(re.escape(token) + r"】?\s*个?年", raw))
            if re.fullmatch(r"[0-9]{1,3}", token):
                months = int(token) * (12 if is_year else 1)
            else:
                cn = parse_chinese_int(token)
                if cn is not None:
                    months = cn * (12 if is_year else 1)
            cands.append({"raw": raw.strip()[:40], "token": token, "months": months})
    # 去重（同一 raw 文本同一位置可能被多条模式命中）
    uniq: list[dict] = []
    seen: set[tuple[str, int | None]] = set()
    for c in cands:
        k = (c["raw"], c["months"])
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq


def check_term(
    text: str,
    field_name: str = "contract.lease_term_months",
    lo: int = TERM_MONTHS_MIN,
    hi: int = TERM_MONTHS_MAX,
) -> tuple[int | None, list[ValidationFlag]]:
    """期限解析增强 + 边界检查 + 一致性检查。

    Returns: (采信的期限月数或 None, ValidationFlag 列表)。
    多值冲突/越界/与起止日期矛盾 → 不采信任何值，置信度置 0 转人审。
    """
    flags: list[ValidationFlag] = []
    cands = extract_term_candidates(text)
    if not cands:
        return None, flags
    valid = [c for c in cands if c["months"] is not None]
    if not valid:
        flags.append(ValidationFlag(
            field_name=field_name, reason_code="term_parse_failed",
            severity="review",
            detail="期限文本存在但无法解析为有效数字（疑似 OCR 误识别），转人审",
            raw_masked=mask_value(cands[0]["raw"])))
        return None, flags
    distinct = sorted({c["months"] for c in valid})
    if len(distinct) > 1:
        # 主标签值 vs 相对到期值不一致（如 "44 个月" vs "第 144 个月对应日"）
        raws = "；".join(c["raw"] for c in valid[:4])
        flags.append(ValidationFlag(
            field_name=field_name, reason_code="term_inconsistent",
            severity="review",
            detail=f"期限多值冲突 {distinct}（月），不静默采信，转人审",
            raw_masked=mask_value(raws)))
        return None, flags
    months = distinct[0]
    if not (lo <= months <= hi):
        flags.append(ValidationFlag(
            field_name=field_name, reason_code="term_out_of_bounds",
            severity="review",
            detail=f"期限 {months} 个月越出有效区间 [{lo}, {hi}]（融资租赁业务常见 1 个月–10 年），转人审",
            raw_masked=mask_value(valid[0]["raw"])))
        return None, flags
    # 一致性：起止日期与期限
    sm, em = _START_DATE_RE.search(text), _END_DATE_RE.search(text)
    if sm and em:
        d1, d2 = _parse_date(sm.group(1)), _parse_date(em.group(1))
        if d1 and d2:
            span = _months_between(d1, d2)
            if abs(span - months) > TERM_CONSISTENCY_TOLERANCE_MONTHS:
                flags.append(ValidationFlag(
                    field_name=field_name, reason_code="term_inconsistent",
                    severity="review",
                    detail=f"起止日期跨度 {span:.1f} 个月与期限 {months} 个月偏差 >1 个月，转人审",
                    raw_masked=mask_value(f"{sm.group(1)} ~ {em.group(1)}")))
                return None, flags
    return months, flags


# ---------------------------------------------------------------- 单据级入口


def validate_document(
    text: str,
    doc_kind: str,
    amount_labels_parsed: dict[str, float] | None = None,
) -> list[ValidationFlag]:
    """单文档统一 validation：金额交叉 + 期限检查（解析层之后调用，不改抽取接口）。

    doc_kind: "contract" | "invoice"（清单无金额大写/期限字段，跳过）。
    """
    flags: list[ValidationFlag] = []
    if doc_kind in ("contract", "invoice"):
        flags += crosscheck_amount_fields(text, doc_kind, amount_labels_parsed)
    if doc_kind == "contract":
        _, term_flags = check_term(text)
        flags += term_flags
    return flags

