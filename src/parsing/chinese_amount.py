"""中文大写金额与阿拉伯金额的通用解析（0 token，纯正则/查表）。

用途：金额大写/小写交叉校验（amount cross-check）的底层解析器。
- parse_chinese_amount：中文大写金额 → Decimal（支持 零壹贰叁肆伍陆柒捌玖、
  拾佰仟万亿、元/圆、角、分、整/正，处理"零"的省略与补位）；
- parse_arabic_amount：¥/￥/RMB/人民币 前缀、千分位逗号、万元/亿元后缀 → Decimal（元）；
- parse_chinese_int：中文数字（含小写 一二三… 与大写 壹贰叁…）→ int，
  供期限解析（叁拾陆个月 / 十二个月）复用。
非法输入一律返回 None（视为解析失败，不采信、不猜测）。
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_DIGITS = {
    "零": 0, "壹": 1, "贰": 2, "叁": 3, "肆": 4,
    "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9,
}
_DIGITS_LOWER = {
    "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "〇": 0,
}
_SMALL_UNITS = {"拾": 10, "佰": 100, "仟": 1000}
_SMALL_UNITS_LOWER = {"十": 10, "百": 100, "千": 1000}
_BIG_UNITS = {"万": 10_000, "亿": 100_000_000}

_PREFIX_RE = re.compile(r"^(?:人民币|RMB|￥|¥)\s*")
_SUFFIX_RE = re.compile(r"[（(]?大写[）)]?|[（(]?\s*￥?\s*[）)]?$")


def _parse_section(text: str, digits: dict, small_units: dict) -> int | None:
    """解析不含万/亿的段（0–9999），如 叁佰零伍 / 十二 / 壹拾。"""
    if not text:
        return None
    section = 0
    num: int | None = None
    for i, ch in enumerate(text):
        if ch in digits:
            num = digits[ch]
        elif ch in small_units:
            unit = small_units[ch]
            if num is None:
                # 仅段首的"拾/十"允许隐含 1（拾万=10 万、十五=15）；
                # 佰/仟前必须有数字，"壹佰拾"这类写法视为非法输入
                if unit != 10 or section > 0 or i > 0:
                    return None
                num = 1
            elif num >= unit:  # 非法：如 拾佰
                return None
            section += num * unit
            num = None
        else:
            return None
    if num is not None:
        section += num
    return section


def parse_chinese_int(text: str, strict_daxie: bool = False) -> int | None:
    """中文整数 → int（支持 万/亿 分段与嵌套，如 壹万亿）；非法返回 None。

    strict_daxie=True 时只接受大写数字（零壹贰…），用于正式大写金额；
    默认同时接受小写中文数字（一二三…），供期限等场景使用。
    """
    s = _PREFIX_RE.sub("", text.strip())
    s = s.replace(" ", "")
    if not s:
        return None
    digits = dict(_DIGITS) if strict_daxie else {**_DIGITS, **_DIGITS_LOWER}
    small = dict(_SMALL_UNITS) if strict_daxie else {**_SMALL_UNITS, **_SMALL_UNITS_LOWER}

    def parse_wan(part: str) -> int | None:
        if not part:
            return None
        if "万" in part:
            head, _, rest = part.partition("万")
            sec = _parse_section(head, digits, small)
            if sec is None or sec == 0:
                return None
            tail = _parse_section(rest, digits, small) if rest else 0
            if tail is None:
                return None
            return sec * _BIG_UNITS["万"] + tail
        return _parse_section(part, digits, small)

    if "亿" in s:
        head, _, rest = s.partition("亿")
        hi = parse_wan(head)
        if hi is None or hi == 0:
            return None
        if not rest:
            return hi * _BIG_UNITS["亿"]
        lo = parse_wan(rest)
        return None if lo is None else hi * _BIG_UNITS["亿"] + lo
    return parse_wan(s)


def parse_chinese_amount(text: str) -> Decimal | None:
    """中文大写金额 → Decimal（元）。非法/无法解析返回 None。

    支持：壹佰零伍元整=105.00、壹拾万元整=100000.00、
    贰亿零叁佰万元整=203000000.00、伍角=0.50、壹元贰角叁分=1.23。
    """
    s = _PREFIX_RE.sub("", text.strip())
    s = re.sub(r"[【】\[\]\s]", "", s)
    s = re.sub(r"(整|正)$", "", s)
    if not s:
        return None
    int_part, frac_part = s, ""
    for sep in ("元", "圆"):
        if sep in s:
            int_part, _, frac_part = s.partition(sep)
            break
    else:
        # 无"元"：仅接受纯角分写法（如 伍角），否则要求有元单位防止误判
        if "角" not in s and "分" not in s:
            return None
        int_part, frac_part = "", s
    yuan = 0
    if int_part:
        parsed = parse_chinese_int(int_part, strict_daxie=True)
        if parsed is None:
            return None
        yuan = parsed
    jiao = fen = 0
    if frac_part:
        m = re.match(
            r"^(?:([零壹贰叁肆伍陆柒捌玖])角)?(?:零)?(?:([零壹贰叁肆伍陆柒捌玖])分)?$",
            frac_part)
        if not m or (m.group(1) is None and m.group(2) is None):
            return None
        if m.group(1):
            jiao = _DIGITS[m.group(1)]
        if m.group(2):
            fen = _DIGITS[m.group(2)]
    return Decimal(yuan) + Decimal(jiao) / 10 + Decimal(fen) / 100


_ARABIC_RE = re.compile(
    r"(?:人民币|RMB|￥|¥)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(亿元|万元|亿|万)?")


def parse_arabic_amount(text: str) -> Decimal | None:
    """阿拉伯金额 → Decimal（元）。支持 ¥/￥/RMB/人民币 前缀、千分位、万/亿后缀。"""
    m = _ARABIC_RE.search(text.strip())
    if not m:
        return None
    try:
        v = Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None
    suffix = m.group(2)
    if suffix in ("万", "万元"):
        v *= 10_000
    elif suffix in ("亿", "亿元"):
        v *= 100_000_000
    return v


def crosscheck_amount(
    daxie_text: str | None,
    arabic_text: str | None,
    tolerance: Decimal = Decimal("0.01"),
) -> tuple[str, Decimal | None, Decimal | None]:
    """大写/小写交叉校验。

    Returns:
        (status, daxie_value, arabic_value)
        status ∈ {"match", "mismatch", "unavailable", "parse_failed"}
        - 两种写法都存在且相等（±tolerance）→ match
        - 都存在但不相等 → mismatch（调用方转人审，不得静默替换值）
        - 只有一种写法 → unavailable（无法交叉，不惩罚）
        - 写法存在但解析失败 → parse_failed（同样转人审）
    """
    d = parse_chinese_amount(daxie_text) if daxie_text else None
    a = parse_arabic_amount(arabic_text) if arabic_text else None
    if daxie_text and d is None:
        return "parse_failed", None, a
    if arabic_text and a is None:
        return "parse_failed", d, None
    if d is None and a is None:
        return "unavailable", None, None
    if d is None or a is None:
        return "unavailable", d, a
    return ("match" if abs(d - a) <= tolerance else "mismatch"), d, a
