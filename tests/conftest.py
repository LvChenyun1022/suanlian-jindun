"""共享测试辅助：最小要素模型构造器 + 小型合成数据集 fixture。"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from src.datagen.generate import generate_dataset
from src.schemas import (
    ContractEssentials,
    FieldCheckResult,
    InvoiceEssentials,
    LeaseItem,
    LeaseItemEssentials,
    MoneyAmount,
    Party,
    VerificationResult,
)


@pytest.fixture(scope="session")
def ds20(tmp_path_factory) -> Path:
    """20 案小数据集（含三种欺诈模式），供解析/核验测试使用。"""
    out = tmp_path_factory.mktemp("ds20") / "cases"
    generate_dataset(20, out, 99)
    return out


def make_contract(
    total: float = 1_000_000.0,
    account_days: int = 30,
    sign_date: date = date(2025, 6, 1),
    seller: str = "甲供应商有限公司",
    buyer: str = "乙承租人有限公司",
    contract_no: str = "HT-2025-9001",
) -> ContractEssentials:
    return ContractEssentials(
        contract_no=contract_no,
        sign_date=sign_date,
        lessor=None,
        vendor=Party(name=seller, role="vendor"),
        lessee=Party(name=buyer, role="lessee"),
        total_amount=MoneyAmount(amount=total),
        account_days=account_days,
        subject="NVIDIA H100 80GB SXM x 4 台",
    )


def make_invoice(
    total: float = 1_000_000.0,
    seller: str = "甲供应商有限公司",
    buyer: str = "乙承租人有限公司",
    invoice_date: date = date(2025, 6, 10),
) -> InvoiceEssentials:
    excl = round(total / 1.13, 2)
    return InvoiceEssentials(
        invoice_no="12345678",
        invoice_date=invoice_date,
        seller=Party(name=seller, role="vendor"),
        buyer=Party(name=buyer, role="lessee"),
        item_name="*电子设备*GPU加速卡",
        quantity=4,
        unit_price=round(excl / 4, 2),
        amount_excl_tax=MoneyAmount(amount=excl),
        tax_amount=MoneyAmount(amount=round(total - excl, 2)),
        amount_incl_tax=MoneyAmount(amount=total),
    )


def make_lease(
    total: float = 1_000_000.0,
    item_id: str = "ZL-9001-A",
    serial_no: str = "SNTEST0001",
    contract_no: str = "HT-2025-9001",
) -> LeaseItemEssentials:
    return LeaseItemEssentials(
        list_no="QD-9001",
        contract_no=contract_no,
        items=[
            LeaseItem(
                item_id=item_id,
                model="NVIDIA H100 80GB SXM",
                category="gpu",
                serial_no=serial_no,
                quantity=4,
                purchase_price=MoneyAmount(amount=total),
                delivery_date=date(2025, 6, 15),
            )
        ],
        total_value=MoneyAmount(amount=total),
    )


def make_verification(case_id: str = "case_9001", all_pass: bool = True) -> VerificationResult:
    checks = [
        FieldCheckResult(check_name="c1", passed=all_pass, detail="d1"),
        FieldCheckResult(check_name="c2", passed=True, detail="d2"),
    ]
    passed = sum(1 for c in checks if c.passed)
    return VerificationResult(
        case_id=case_id, checks=checks, passed_count=passed, failed_count=len(checks) - passed
    )
