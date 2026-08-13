"""field_validation 单元测试：金额交叉校验、期限边界与一致性。"""
from src.validation import (
    check_term,
    crosscheck_amount_fields,
    extract_amount_pairs,
    mask_value,
    validate_document,
)


def _reviews(flags):
    return [f for f in flags if f.severity == "review"]


# ---------------- 金额大写/小写交叉校验 ----------------

def test_amount_pair_extract_and_match():
    text = "租赁物转让价款：大写：【柒仟肆佰陆拾万】元整 小写：¥【74,600,000.00】元"
    pairs = extract_amount_pairs(text)
    assert pairs and pairs[0]["daxie"] and pairs[0]["arabic"]
    flags = crosscheck_amount_fields(text, "contract")
    assert not _reviews(flags)


def test_amount_mismatch_flagged():
    text = "合同总金额：大写：壹佰万元整 小写：¥1,100,000.00 元。"
    flags = crosscheck_amount_fields(text, "contract")
    reviews = _reviews(flags)
    assert len(reviews) == 1
    assert reviews[0].reason_code == "amount_mismatch_daxie"
    assert "1,10" in reviews[0].raw_masked or "*" in reviews[0].raw_masked


def test_amount_single_form_unavailable():
    text = "合同总金额：¥1,000,000.00 元，分两期支付。"
    flags = crosscheck_amount_fields(text, "contract")
    assert not _reviews(flags)
    assert any(f.reason_code == "amount_crosscheck_unavailable" for f in flags)


def test_amount_no_label_no_flag():
    assert crosscheck_amount_fields("今天天气不错。", "contract") == []


# ---------------- 期限解析增强 ----------------

def test_term_arabic_months():
    months, flags = check_term("租赁期限：【84】个月，自起租日起算。")
    assert months == 84 and not _reviews(flags)


def test_term_chinese_months():
    months, _ = check_term("租赁期限为叁拾陆个月。")
    assert months == 36


def test_term_year_conversion():
    months, _ = check_term("合同期限为 3 年。")
    assert months == 36


def test_term_out_of_bounds():
    months, flags = check_term("租赁期限：【360】个月。")
    assert months is None
    assert _reviews(flags)[0].reason_code == "term_out_of_bounds"


def test_term_conflict_relative_expiry():
    # contract_C 实例的通用形态：正文期限与相对到期表述冲突
    text = "租赁期限：租赁期限为44个月，自起租日起至起租日后第144个月对应日为止。"
    months, flags = check_term(text)
    assert months is None
    reviews = _reviews(flags)
    assert len(reviews) == 1 and reviews[0].reason_code == "term_inconsistent"
    assert "44" in reviews[0].detail


def test_term_consistent_with_dates():
    text = "租赁期限：36个月。起租日：2024年1月15日。到期日：2027年1月15日。"
    months, flags = check_term(text)
    assert months == 36 and not _reviews(flags)


def test_term_inconsistent_with_dates():
    text = "租赁期限：36个月。起租日：2024-01-15。到期日：2028-01-15。"
    months, flags = check_term(text)
    assert months is None
    assert _reviews(flags)[0].reason_code == "term_inconsistent"


def test_term_unparseable():
    months, flags = check_term("租赁期限：8B个月。")
    # "8B" 不能整体解析为有效期限 → 若无其他候选则为 None；
    # 该写法不命中任何候选模式时也允许返回无候选（不采信即可）
    assert months is None


def test_term_no_text_no_flag():
    months, flags = check_term("本合同无期限条款。")
    assert months is None and not _reviews(flags)


# ---------------- 单据级入口与掩码 ----------------

def test_validate_document_contract():
    text = "合同总金额：壹佰万元整（小写：¥1,000,000.00 元）。租赁期限：36个月。"
    flags = validate_document(text, "contract")
    assert not _reviews(flags)


def test_mask_value():
    # 掩码语义：≥3 位数字段保留前 2 位，其余 *
    assert mask_value("¥74,600,000.00") == "¥74,60*,00*.00"
    assert mask_value("无数字") == "无数字"
    assert "*" in mask_value("账号 123456789012345")
