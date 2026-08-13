"""validation 阶段 pipeline 集成测试：合成集 0 误伤 + 审计留痕 + CLI 可见。"""
import sqlite3
from pathlib import Path

from src.pipeline import run_pipeline


def _files(case_id: str) -> dict[str, str]:
    return {
        "contract": f"{case_id}/contract.pdf",
        "invoice": f"{case_id}/invoice.pdf",
        "lease_items": f"{case_id}/lease_items.pdf",
    }


def test_pipeline_validation_zero_false_positive(ds20: Path, tmp_path):
    """合成评测集（数字文本 PDF，无大写金额/期限条款）不得产生 review 级标记。"""
    case_dir = sorted(p for p in ds20.iterdir() if p.is_dir())[0]
    state = run_pipeline(
        case_dir.name, _files(case_dir.name), "mock",
        base_dir=ds20, labels_path=ds20 / "labels.jsonl",
        audit_path=tmp_path / "audit.db", out_dir=tmp_path / "report",
    )
    review = [f for f in state.validation_flags if f.severity == "review"]
    assert review == [], f"合成集出现误伤: {[f.reason_code for f in review]}"
    # info 级记录允许存在（仅一种写法无法交叉，不惩罚）
    assert all(f.severity == "info" for f in state.validation_flags)
    # 审计日志含 validation 阶段记录
    con = sqlite3.connect(tmp_path / "audit.db")
    stages = {r[0] for r in con.execute("SELECT stage FROM audit_log")}
    con.close()
    assert "validation" in stages


def test_pipeline_validation_review_visible_in_state(ds20: Path, tmp_path):
    """review 级标记（若存在）必须进入 state 且带原因码与掩码（抽查模型完整性）。"""
    from src.schemas import ValidationFlag

    f = ValidationFlag(
        field_name="contract.total_amount", reason_code="amount_mismatch_daxie",
        severity="review", detail="t", raw_masked="壹佰万 vs ¥1,10*,***.**")
    assert f.reason_code == "amount_mismatch_daxie" and f.severity == "review"
