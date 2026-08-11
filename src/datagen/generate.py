"""数据集生成 CLI。

用法：
    python -m src.datagen.generate --n 100 --out data/cases --seed 42

产物：
    <out>/case_0001/contract.pdf, invoice.pdf, lease_items.pdf ...
    <out>/labels.jsonl  每案件一行真值标签（SPEC EvalLabel 结构）
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from .cases import FRAUD_A, FRAUD_B, FRAUD_C, CaseFactory, CaseSpec
from .pdfdoc import SimplePdfWriter

DOC_FILENAMES = {
    "contract": "contract.pdf",
    "invoice": "invoice.pdf",
    "lease_items": "lease_items.pdf",
}


def _pattern_plan(n: int, seed: int) -> tuple[list[str | None], list[int]]:
    """欺诈配比：30% 欺诈、三种模式均分（余数依次补给 a/b/c），确定性打散。"""
    n_fraud = round(n * 0.3)
    base = n_fraud // 3
    rem = n_fraud - base * 3
    counts = [base + (1 if i < rem else 0) for i in range(3)]
    patterns: list[str | None] = (
        [FRAUD_A] * counts[0]
        + [FRAUD_B] * counts[1]
        + [FRAUD_C] * counts[2]
        + [None] * (n - n_fraud)
    )
    random.Random(seed + 999).shuffle(patterns)
    return patterns, counts


def render_case(spec: CaseSpec, out_dir: Path) -> tuple[dict, dict]:
    """渲染一个案件的三份 PDF，并返回 files 映射与字段级 oracle。"""
    case_dir = out_dir / spec.case_id
    files: dict[str, str] = {}
    oracle: dict[str, dict] = {}
    for doc_type, doc in spec.docs.items():
        path = case_dir / DOC_FILENAMES[doc_type]
        writer = SimplePdfWriter(path, doc.title)
        for key, label, value in doc.fields:
            indent = 20.0 if key.startswith("items.") else 0.0
            writer.field_line(key, label, value, indent=indent)
        for line in doc.trailer_lines:
            writer.line(line)
        writer.save()

        files[doc_type] = f"{spec.case_id}/{DOC_FILENAMES[doc_type]}"
        oracle[doc_type] = {
            "title": doc.title,
            "fields": {
                key: {
                    "value": value,
                    "page": writer.positions[key].page,
                    "bbox": list(writer.positions[key].bbox),
                    "excerpt": writer.positions[key].excerpt,
                }
                for key, _label, value in doc.fields
            },
        }
    return files, oracle


def generate_dataset(n: int, out_dir: str | Path, seed: int) -> list[dict]:
    """生成 n 套案件（case_XXXX 四位零填充）与 labels.jsonl，返回标签列表。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    patterns, counts = _pattern_plan(n, seed)
    factory = CaseFactory(seed, pledge_pool_size=max(1, -(-counts[1] // 2)))

    labels: list[dict] = []
    for i, pattern in enumerate(patterns, start=1):
        case_id = f"case_{i:04d}"
        spec = factory.build(i, case_id, pattern)
        files, oracle = render_case(spec, out)
        labels.append(
            {
                "case_id": case_id,
                "is_fraud": spec.is_fraud,
                "fraud_pattern": spec.fraud_pattern,
                "injected_adversarial": False,
                "files": files,
                "oracle": oracle,
                "metadata": spec.metadata,
            }
        )

    with open(out / "labels.jsonl", "w", encoding="utf-8") as f:
        for row in labels:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return labels


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="src.datagen.generate", description="生成合成单据数据集（虚构演示数据）"
    )
    parser.add_argument("--n", type=int, default=100, help="案件总数（默认 100）")
    parser.add_argument("--out", type=Path, default=Path("data/cases"), help="输出目录")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（结果可复现）")
    args = parser.parse_args(argv)

    labels = generate_dataset(args.n, args.out, args.seed)
    dist = Counter(row["fraud_pattern"] or "normal" for row in labels)
    print(f"输出目录 : {args.out}")
    print(f"总案件数 : {len(labels)}")
    for key in ["normal", FRAUD_A, FRAUD_B, FRAUD_C]:
        print(f"  {key:<16}: {dist.get(key, 0)}")
    print(f"标签文件 : {args.out / 'labels.jsonl'}")


if __name__ == "__main__":
    main()
