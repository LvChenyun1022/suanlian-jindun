"""生成 live 模式字段补抽演示案件（仅含程序合成数据）。

用法（仓库根目录）：
    python -m src.datagen.generate --n 100 --out data/cases --seed 42
    python scripts/make_live_demo_case.py

随后启动 Streamlit，选择 ``case_live_0001``、关闭 mock LLM，并配置任意
OpenAI-compatible 模型服务。合同中的“签署日期”不是规则解析器的标准标签，
因此会触发 live 模式 LLM 补抽并回填原文证据坐标。

该案件不写入 ``labels.jsonl``，不参与任何评测指标计算。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.datagen.cases import CaseFactory
from src.datagen.generate import render_case

OUT_DIR = ROOT / "data" / "cases"
CASE_ID = "case_live_0001"
LABEL_VARIANTS = {"签订日期": "签署日期"}


def generate_live_demo_case(out_dir: str | Path = OUT_DIR) -> dict[str, str]:
    """生成确定性的正常演示案件，并返回三份 PDF 的相对路径映射。"""
    factory = CaseFactory(seed=42)
    spec = factory.build(1, CASE_ID, fraud_pattern=None)
    contract = spec.docs["contract"]
    contract.fields = [
        (key, LABEL_VARIANTS.get(label, label), value)
        for key, label, value in contract.fields
    ]
    files, _oracle = render_case(spec, Path(out_dir))
    return files


def main() -> None:
    files = generate_live_demo_case()
    print(f"已生成演示案件 {CASE_ID}: {files}")
    print("提示：该案件不参与评测；仅用于 live 模式 LLM 补抽演示。")


if __name__ == "__main__":
    main()
