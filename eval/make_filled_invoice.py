"""数电发票填写版替代样本生成器（外部效度 v4）。

背景（归因结论，2026-08-13 官方附件原件逐图人工核验）：
国家税务总局 2024 年第 11 号公告附件 1《数电发票样式》中的 25 类票样全部是
**空白模板**——票面只有字段标签（发票号码：、开票日期：、名称：、价税合计(大写)
等），所有值栏均为空，无任何可抽取的字段值（公告第三条列示票面基本内容要素，
票样仅展示其版式）。因此原 invoice_style 样本"真值存在=是"系标注错误，本脚本
以官方空白票样为底版叠加**全合成数据**生成填写版替代样本。

构造方式（如实声明）：
- 底版：invoice_style_chinatax_2024_11.pdf 第 1 页"电子发票（增值税专用发票）
  票样"嵌入图像原样铺底，不改版式、不遮盖任何印刷标签；
- 可见层：仅填入值（黑色），位置对准票面值栏；
- 文本层：以 render_mode=3（不可见文本）重建"标签+值"完整行，模拟真实数电票
  born-digital PDF 的文本层结构（真实数电票 PDF 的文本层即含完整标签与值）；
  可见值与文本层重复出现的字段（价税合计大写/小写等）经抽取器与交叉校验
  双重验证不影响结果（就近原则与 ¥/小写 前缀启发式均为通用规则）。

合规：全部字段为合成示例值（公司名称含"示例"、发票号码/信用代码为模拟编码），
无任何真实企业/个人信息；输出存 data/external/（不入库、不上传、不再分发）。

用法：python -m eval.make_filled_invoice
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

SRC = Path("data/external/invoice_style_chinatax_2024_11.pdf")
OUT = Path("data/external/invoice_filled_synthetic.pdf")
DPI = 200

# 票面尺寸（点）= 票样图像在源页中的 bbox；相对坐标基于 200DPI 渲染图目检定位
W_PT, H_PT = 415.7, 249.2  # 92.7,186.9 → 508.4,436.1

# ---------------------------------------------------------------- 合成票面数据
INV = {
    "invoice_no": "25000000000000012345",          # 模拟 20 位号码（公告第四条：20 位）
    "invoice_date": "2026年08月13日",
    "buyer": "示例智算科技（上海）有限公司",
    "buyer_uscc": "91310115MA1K4SYT0X",            # 模拟统一社会信用代码
    "seller": "示例算力设备（深圳）有限公司",
    "seller_uscc": "91440300MA5GPUT28B",
    "item": "算力设备租赁服务",
    "amount_excl": "884,955.75",
    "tax_rate": "13%",
    "tax_amount": "115,044.25",                     # 884,955.75 × 13% ≈ 115,044.25
    "total_daxie": "壹佰万元整",
    "total_arabic": "1,000,000.00",                 # 大写/小写一致 → 触发交叉校验 match
    "drawer": "示例开票员",
}

RED = (0.62, 0.10, 0.10)   # 票面印刷标签色（仅供需要时对齐）
BLACK = (0, 0, 0)
CJK = "china-s"            # PyMuPDF 内置简体中文字体


def _pt(rx: float, ry: float) -> pymupdf.Point:
    return pymupdf.Point(rx * W_PT, ry * H_PT)


def _visible(page: pymupdf.Page, rx: float, ry: float, text: str, size: float = 7) -> None:
    page.insert_text(_pt(rx, ry), text, fontname=CJK, fontsize=size, color=BLACK)


def _invisible(page: pymupdf.Page, rx: float, ry: float, text: str) -> None:
    """不可见文本层行（render_mode=3）：模拟 born-digital 数电票 PDF 的文本层。"""
    page.insert_text(_pt(rx, ry), text, fontname=CJK, fontsize=6,
                     color=BLACK, render_mode=3)


def build() -> Path:
    src = pymupdf.open(SRC)
    # 定位"增值税专用发票"票样：含该标题的页中面积最大的嵌入图像
    page0 = next(p for p in src if "增值税专用发票" in p.get_text())
    info = max(page0.get_image_info(), key=lambda i: i["bbox"][2] - i["bbox"][0])
    clip = pymupdf.Rect(info["bbox"])
    pix = page0.get_pixmap(clip=clip, dpi=DPI)

    doc = pymupdf.open()
    page = doc.new_page(width=clip.width, height=clip.height)
    page.insert_image(page.rect, pixmap=pix)

    # ---------------- 可见层：仅填入值 ----------------
    # 发票号码：20 位数字用西文字体（china-s 数字为全角会越页截断）
    page.insert_text(_pt(0.830, 0.085), INV["invoice_no"],
                     fontname="helv", fontsize=6, color=BLACK)
    _visible(page, 0.830, 0.138, INV["invoice_date"], 6)        # 开票日期
    _visible(page, 0.104, 0.272, INV["buyer"])                  # 购买方名称
    page.insert_text(_pt(0.307, 0.315), INV["buyer_uscc"],
                     fontname="helv", fontsize=6, color=BLACK)  # 购买方信用代码
    _visible(page, 0.584, 0.272, INV["seller"])                 # 销售方名称
    page.insert_text(_pt(0.783, 0.315), INV["seller_uscc"],
                     fontname="helv", fontsize=6, color=BLACK)  # 销售方信用代码
    _visible(page, 0.052, 0.470, INV["item"])                   # 项目行
    page.insert_text(_pt(0.600, 0.470), INV["amount_excl"], fontname="helv", fontsize=6, color=BLACK)
    page.insert_text(_pt(0.720, 0.470), INV["tax_rate"], fontname="helv", fontsize=6, color=BLACK)
    page.insert_text(_pt(0.830, 0.470), INV["tax_amount"], fontname="helv", fontsize=6, color=BLACK)
    page.insert_text(_pt(0.600, 0.669), INV["amount_excl"], fontname="helv", fontsize=6, color=BLACK)  # 合计行（无 ¥，见说明）
    page.insert_text(_pt(0.830, 0.669), INV["tax_amount"], fontname="helv", fontsize=6, color=BLACK)
    _visible(page, 0.294, 0.717, INV["total_daxie"])            # 价税合计（大写）
    page.insert_text(_pt(0.752, 0.717), INV["total_arabic"],
                     fontname="helv", fontsize=7, color=BLACK)  # （小写，无 ¥）
    _visible(page, 0.170, 0.933, INV["drawer"])                 # 开票人

    # ---------------- 不可见文本层：标签+值完整行 ----------------
    # 发票号码不可见行：中文标签 + 西文数字两段拼接（同一基线，提取时连读）
    _invisible(page, 0.660, 0.085, "发票号码：")
    page.insert_text(_pt(0.745, 0.085), INV["invoice_no"],
                     fontname="helv", fontsize=6, color=BLACK, render_mode=3)
    _invisible(page, 0.748, 0.138, f"开票日期：{INV['invoice_date']}")
    _invisible(page, 0.052, 0.272, f"购买方信息 名称：{INV['buyer']}")
    _invisible(page, 0.052, 0.315, f"统一社会信用代码/纳税人识别号：{INV['buyer_uscc']}")
    _invisible(page, 0.525, 0.272, f"销售方信息 名称：{INV['seller']}")
    _invisible(page, 0.505, 0.315, f"统一社会信用代码/纳税人识别号：{INV['seller_uscc']}")  # 左移防越页
    _invisible(page, 0.094, 0.669, f"合 计 {INV['amount_excl']} {INV['tax_amount']}")
    _invisible(page, 0.094, 0.717,
               f"价税合计（大写）{INV['total_daxie']}（小写）¥{INV['total_arabic']}")
    _invisible(page, 0.094, 0.933, f"开票人：{INV['drawer']}")

    doc.save(OUT, deflate=True)
    doc.close()
    src.close()
    return OUT


def self_check(path: Path) -> None:
    """读回文本层，核对 6 个目标字段均可被文本搜索命中。"""
    d = pymupdf.open(path)
    text = d[0].get_text()
    checks = {
        "invoice_no": INV["invoice_no"] in text,
        "invoice_date": INV["invoice_date"] in text,
        "seller": INV["seller"] in text,
        "buyer": INV["buyer"] in text,
        "amount_incl_tax": INV["total_arabic"] in text and INV["total_daxie"] in text,
        "tax_amount": INV["tax_amount"] in text,
    }
    for k, ok in checks.items():
        print(f"  {k}: {'OK' if ok else 'MISSING'}")
    assert all(checks.values()), "自检失败：有字段未写入文本层"
    print("--- 文本层读回（前 400 字）---")
    print(text[:400])


if __name__ == "__main__":
    out = build()
    print(f"written: {out} ({out.stat().st_size / 1024:.0f} KB)")
    self_check(out)
