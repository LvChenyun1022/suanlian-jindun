"""chinese_amount 单元测试：大写金额解析、阿拉伯金额归一化、交叉校验。"""
from decimal import Decimal

import pytest

from src.parsing.chinese_amount import (
    crosscheck_amount,
    parse_arabic_amount,
    parse_chinese_amount,
    parse_chinese_int,
)

D = Decimal


@pytest.mark.parametrize("text,expected", [
    ("壹佰零伍元整", D("105")),
    ("壹拾万元整", D("100000")),
    ("贰亿零叁佰万元整", D("203000000")),
    ("柒仟肆佰陆拾万元整", D("74600000")),
    ("叁亿捌仟万元整", D("380000000")),
    ("壹佰贰拾万元整", D("1200000")),
    ("捌佰万元整", D("8000000")),
    ("人民币肆亿叁仟伍佰万元整", D("435000000")),
    ("壹元贰角叁分", D("1.23")),
    ("伍角", D("0.5")),
    ("玖分", D("0.09")),
    ("壹拾伍元零伍分", D("15.05")),
    ("壹万元整", D("10000")),
    ("壹万亿圆整", D("1000000000000")),
    ("零元整", D("0")),
    ("壹拾万零伍佰元整", D("100500")),
    ("贰拾叁万肆仟伍佰陆拾柒元捌角玖分", D("234567.89")),
    ("壹佰零伍圆", D("105")),
    ("壹万零壹元正", D("10001")),
])
def test_parse_chinese_amount_valid(text, expected):
    assert parse_chinese_amount(text) == expected


@pytest.mark.parametrize("text", [
    "", "一百万元整",            # 小写中文非大写金额（走 parse_chinese_int，不是本函数）
    "ABC", "12345",            # 纯阿拉伯/字母
    "壹佰拾万元整",            # 非法单位组合
    "壹元贰角叁",              # 尾字残缺
    None if False else "　",   # 全角空格
])
def test_parse_chinese_amount_invalid(text):
    assert parse_chinese_amount(text) is None


@pytest.mark.parametrize("text,expected", [
    ("¥1,000,000.00", D("1000000")),
    ("￥380,000,000.00", D("380000000")),
    ("RMB 8000000.00", D("8000000")),
    ("人民币 1,200,000.00 元", D("1200000")),
    ("120万元", D("1200000")),
    ("3.8亿元", D("380000000")),
    ("74600000", D("74600000")),
    ("¥0.00", D("0")),
])
def test_parse_arabic_amount(text, expected):
    assert parse_arabic_amount(text) == expected


def test_parse_arabic_invalid():
    assert parse_arabic_amount("没有数字") is None


@pytest.mark.parametrize("text,expected", [
    ("叁拾陆", 36), ("十二", 12), ("壹拾", 10), ("十五", 15),
    ("拾", 10), ("壹佰零伍", 105), ("一百四十四", 144),
])
def test_parse_chinese_int(text, expected):
    assert parse_chinese_int(text) == expected


def test_crosscheck_match():
    status, d, a = crosscheck_amount("壹佰万元整", "¥1,000,000.00")
    assert status == "match" and d == a == D("1000000")


def test_crosscheck_mismatch():
    status, d, a = crosscheck_amount("壹佰万元整", "¥1,100,000.00")
    assert status == "mismatch" and d == D("1000000") and a == D("1100000")


def test_crosscheck_unavailable_single_form():
    assert crosscheck_amount(None, "¥100.00")[0] == "unavailable"
    assert crosscheck_amount("壹佰元整", None)[0] == "unavailable"
    assert crosscheck_amount(None, None)[0] == "unavailable"


def test_crosscheck_parse_failed():
    assert crosscheck_amount("壹佰拾万元整", "¥100.00")[0] == "parse_failed"
