"""案例构建：三类单据字段（f-string 模板）+ 三种造假模式注入。

造假模式（与 SPEC EvalLabel.fraud_pattern 枚举一致）：
- a_chengxing    承兴系：虚构对大型核心企业应收账款，发票与合同主体不一致
- b_multi_pledge 一单多押：同一租赁物编号/序列号出现在多案件清单中
- c_circular_trade 空转贸易：买卖双方受同一实控人（名称含关联特征）、金额闭环

敏感字段（证件号/银行账号/信用代码）一律掩码，不生成真实样式号码。
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import date, timedelta

from faker import Faker

FRAUD_A = "a_chengxing"
FRAUD_B = "b_multi_pledge"
FRAUD_C = "c_circular_trade"

VAT_RATE = 0.13

GPU_POOL: list[tuple[str, float]] = [
    ("NVIDIA H100 80GB SXM", 225_000.0),
    ("NVIDIA H800 80GB SXM", 185_000.0),
    ("NVIDIA A100 80GB PCIe", 88_000.0),
    ("NVIDIA A800 80GB PCIe", 76_000.0),
    ("NVIDIA L40S 48GB PCIe", 62_000.0),
    ("NVIDIA RTX 4090 24GB", 16_500.0),
]

# 虚构"大型核心企业"（承兴系造假用），名称明显虚构、不指向真实企业
CORE_ENTERPRISE_POOL = [
    "中恒联合控股集团有限公司",
    "国瑞宏远能源集团有限公司",
    "华兴远洋供应链集团有限公司",
    "中晟安泰重工股份有限公司",
    "国建锦程产业集团有限公司",
]

# 空转贸易关联主体共用名前缀（同一实控人可检测特征）
CIRCULAR_PREFIX_POOL = ["华鼎", "瑞联", "宏晟", "金侨", "泰合"]

BANKS = ["中国工商银行", "中国建设银行", "招商银行", "交通银行", "中国农业银行"]

SYNTH_NOTICE = "本单据为程序合成的虚构演示数据，不构成任何授信或投资建议。"


def _digits(rng: random.Random, k: int) -> str:
    return "".join(rng.choices(string.digits, k=k))


def _masked_number(rng: random.Random) -> str:
    """掩码号码：前3 + 11个* + 后4（如 110***********1234），不出现长连续数字。"""
    return f"{_digits(rng, 3)}{'*' * 11}{_digits(rng, 4)}"


def _masked_credit_code(rng: random.Random) -> str:
    """掩码统一社会信用代码：'91' + 12个* + 4位字母数字。"""
    tail = "".join(rng.choices(string.ascii_uppercase + string.digits, k=4))
    return f"91{'*' * 12}{tail}"


def _serial_no(rng: random.Random) -> str:
    return "SN" + "".join(rng.choices(string.ascii_uppercase + string.digits, k=8))


@dataclass
class ItemSpec:
    """租赁物清单条目（对应 SPEC LeaseItem 的生成侧字段）。"""

    item_id: str
    model: str
    serial_no: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass
class DocSpec:
    """单份单据：标题 + 有序字段（key, 标签, 渲染值）+ 尾部说明行。"""

    doc_type: str
    title: str
    fields: list[tuple[str, str, str]]
    trailer_lines: list[str] = field(default_factory=list)


@dataclass
class CaseSpec:
    case_id: str
    index: int
    is_fraud: bool
    fraud_pattern: str | None
    docs: dict[str, DocSpec]
    metadata: dict


class CaseFactory:
    """确定性案例工厂：同一 seed 生成结果完全可复现。"""

    def __init__(self, seed: int, pledge_pool_size: int = 5) -> None:
        self.seed = seed
        # 一单多押共享租赁物池：同一池条目将被多个 b 类案件重复引用
        pool_rng = random.Random(seed * 31 + 7)
        self._pledge_pool: list[dict] = []
        for i in range(max(1, pledge_pool_size)):
            model, _price = pool_rng.choice(GPU_POOL)
            self._pledge_pool.append(
                {
                    "item_id": f"ZL-POOL-{i + 1:03d}",
                    "serial_no": _serial_no(pool_rng),
                    "model": model,
                }
            )
        self._b_counter = 0

    def build(self, index: int, case_id: str, fraud_pattern: str | None) -> CaseSpec:
        stream = self.seed * 1_000_003 + index
        rng = random.Random(stream)
        fake = Faker("zh_CN")
        fake.seed_instance(stream + 1)

        # ---- 交易主体 ----
        fraud_detail: dict = {}
        if fraud_pattern == FRAUD_C:
            prefix = rng.choice(CIRCULAR_PREFIX_POOL)
            city = fake.city_name()
            seller = f"{prefix}科技（{city}）有限公司"
            buyer = f"{prefix}贸易（{city}）有限公司"
            account_days = 0  # 闭环：无真实账期
        else:
            prefix = None
            seller = fake.company()
            buyer = fake.company()
            while buyer == seller:
                buyer = fake.company()
            account_days = rng.choice([30, 60, 90, 180])

        # ---- 租赁物（GPU）明细 ----
        n_items = rng.randint(1, 3)
        items: list[ItemSpec] = []
        for k, (model, base_price) in enumerate(rng.sample(GPU_POOL, n_items)):
            items.append(
                ItemSpec(
                    item_id=f"ZL-{index:04d}-{chr(65 + k)}",
                    model=model,
                    serial_no=_serial_no(rng),
                    quantity=rng.randint(4, 48),
                    unit_price=round(base_price * rng.uniform(0.95, 1.05), 2),
                )
            )

        if fraud_pattern == FRAUD_B:
            self._b_counter += 1
            entry = self._pledge_pool[(self._b_counter - 1) % len(self._pledge_pool)]
            items[0].item_id = entry["item_id"]
            items[0].serial_no = entry["serial_no"]
            items[0].model = entry["model"]
            fraud_detail["shared_item_id"] = entry["item_id"]
            fraud_detail["shared_serial_no"] = entry["serial_no"]
            fraud_detail["note"] = "同一租赁物编号/序列号出现在多案件清单（一单多押）"

        total = round(sum(it.total for it in items), 2)
        amount_excl = round(total / (1 + VAT_RATE), 2)
        tax = round(total - amount_excl, 2)

        sign_date = date(2025, 1, 6) + timedelta(days=rng.randint(0, 330))
        invoice_date = sign_date + timedelta(days=rng.randint(3, 30))
        delivery_date = sign_date + timedelta(days=rng.randint(10, 60))

        contract_no = f"HT-{sign_date:%Y}-{index:04d}"
        invoice_no = _digits(rng, 8)
        list_no = f"QD-{index:04d}"

        # ---- 发票主体（承兴系造假注入）----
        inv_seller, inv_buyer = seller, buyer
        if fraud_pattern == FRAUD_A:
            core = rng.choice(CORE_ENTERPRISE_POOL)
            inv_buyer = core
            fraud_detail["fabricated_core_enterprise"] = core
            fraud_detail["mismatched_fields"] = ["invoice.buyer_name"]
            fraud_detail["note"] = "虚构对大型核心企业应收账款，发票与合同主体不一致"
        elif fraud_pattern == FRAUD_C:
            fraud_detail["related_party_token"] = prefix
            fraud_detail["same_controller"] = True
            fraud_detail["amount_closed_loop"] = True

        # ---- 三类单据字段 ----
        subject = "；".join(f"{it.model} x {it.quantity} 台" for it in items)
        total_qty = sum(it.quantity for it in items)
        avg_price_excl = round(amount_excl / total_qty, 2)

        contract_fields: list[tuple[str, str, str]] = [
            ("contract_no", "合同编号", contract_no),
            ("sign_date", "签订日期", sign_date.isoformat()),
            ("seller_name", "卖方（出卖人）", seller),
            ("seller_credit_code", "卖方统一社会信用代码", _masked_credit_code(rng)),
            ("seller_legal_id", "卖方法定代表人证件号", _masked_number(rng)),
            ("seller_bank", "卖方开户行及账号", f"{rng.choice(BANKS)}{fake.city_name()}分行 {_masked_number(rng)}"),
            ("buyer_name", "买方（买受人）", buyer),
            ("buyer_credit_code", "买方统一社会信用代码", _masked_credit_code(rng)),
            ("buyer_legal_id", "买方法定代表人证件号", _masked_number(rng)),
            ("buyer_bank", "买方开户行及账号", f"{rng.choice(BANKS)}{fake.city_name()}分行 {_masked_number(rng)}"),
            ("subject", "标的物", subject),
            ("total_amount", "合同总金额（含税）", f"{total:,.2f} 元"),
            ("account_days", "账期", f"{account_days} 天"),
        ]
        contract = DocSpec(
            "contract",
            "购销合同",
            contract_fields,
            trailer_lines=[
                "一、卖方按约定交付标的物，买方在账期内支付货款。",
                "二、标的物所有权于货款结清后转移至买方。",
                "三、本合同一式两份，双方各执一份，自签章之日起生效。",
                SYNTH_NOTICE,
            ],
        )

        invoice_fields: list[tuple[str, str, str]] = [
            ("invoice_no", "发票号码", invoice_no),
            ("invoice_date", "开票日期", invoice_date.isoformat()),
            ("seller_name", "销售方名称", inv_seller),
            ("buyer_name", "购买方名称", inv_buyer),
            ("item_name", "货物或应税劳务、服务名称", "*电子设备*GPU加速卡"),
            ("quantity", "数量", str(total_qty)),
            ("unit_price", "单价（不含税）", f"{avg_price_excl:,.2f}"),
            ("amount_excl_tax", "金额（不含税）", f"{amount_excl:,.2f}"),
            ("tax_rate", "税率", "13%"),
            ("tax_amount", "税额", f"{tax:,.2f}"),
            ("amount_incl_tax", "价税合计（含税）", f"{total:,.2f} 元"),
            ("remark", "备注", f"合同编号：{contract_no}"),
        ]
        invoice = DocSpec("invoice", "增值税专用发票", invoice_fields, trailer_lines=[SYNTH_NOTICE])

        lease_fields: list[tuple[str, str, str]] = [
            ("list_no", "清单编号", list_no),
            ("contract_no", "关联合同编号", contract_no),
        ]
        for k, it in enumerate(items):
            lease_fields += [
                (f"items.{k}.item_id", f"租赁物编号（{k + 1}）", it.item_id),
                (f"items.{k}.model", f"GPU型号（{k + 1}）", it.model),
                (f"items.{k}.serial_no", f"序列号（{k + 1}）", it.serial_no),
                (f"items.{k}.quantity", f"数量（{k + 1}）", str(it.quantity)),
                (f"items.{k}.unit_price", f"单价（{k + 1}）", f"{it.unit_price:,.2f} 元"),
                (f"items.{k}.total", f"总价（{k + 1}）", f"{it.total:,.2f} 元"),
            ]
        lease_fields += [
            ("delivery_date", "交付日期", delivery_date.isoformat()),
            ("total_value", "清单总价值", f"{total:,.2f} 元"),
        ]
        lease_items = DocSpec(
            "lease_items",
            "租赁物（GPU）清单",
            lease_fields,
            trailer_lines=["清单所列租赁物均已验收并交付使用。", SYNTH_NOTICE],
        )

        metadata = {
            "index": index,
            "seed": self.seed,
            "seller": seller,
            "buyer": buyer,
            "sign_date": sign_date.isoformat(),
            "invoice_date": invoice_date.isoformat(),
            "total_amount": total,
            "account_days": account_days,
            "fraud_detail": fraud_detail,
        }

        return CaseSpec(
            case_id=case_id,
            index=index,
            is_fraud=fraud_pattern is not None,
            fraud_pattern=fraud_pattern,
            docs={"contract": contract, "invoice": invoice, "lease_items": lease_items},
            metadata=metadata,
        )
