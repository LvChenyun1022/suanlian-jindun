"""提交前离线预检：文件、正式结果、Demo 历史序列与回归测试。

默认只做只读静态检查；--run-demo 实跑 case_0021 -> case_0058；
--run-tests 运行 pytest；--all 同时执行两者。全程不调用外部网络或 LLM。
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "cases"
RESULT_DIR = ROOT / "eval" / "results_live_temporal_20260823"
RESULT_JSON = RESULT_DIR / "eval_results.json"
sys.path.insert(0, str(ROOT))


def ok(message: str) -> None:
    print(f"[OK] {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    ok(message)


def read_labels() -> list[dict]:
    labels_path = CASES / "labels.jsonl"
    require(labels_path.is_file(), "data/cases/labels.jsonl 存在")
    labels = [
        json.loads(line)
        for line in labels_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(labels) == 100, "合成评测集为 100 案")
    return labels


def check_required_files() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "SPEC.md",
        ROOT / "requirements.txt",
        ROOT / "requirements-lock.txt",
        ROOT / "docs" / "demo_script.md",
        ROOT / "config" / "rules_77.yaml",
        RESULT_JSON,
        RESULT_DIR / "eval_results.md",
        RESULT_DIR / "RUN_METADATA.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, "提交必需文件齐全" if not missing else f"缺少文件：{missing}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    require(".env" in gitignore and ".venv/" in gitignore, ".env 与 .venv 已排除版本控制")
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    require("your_api_key_here" in example, ".env.example 仅含占位凭据")


def check_imports() -> None:
    missing: list[str] = []
    for module in (
        "pydantic",
        "streamlit",
        "pymupdf",
        "pdfplumber",
        "reportlab",
        "markdown_it",
        "openai",
        "yaml",
    ):
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            missing.append(module)
    if missing:
        venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
        if venv_python.is_file():
            command = f'& "{venv_python}" -X utf8 scripts\\preflight.py --all'
            hint = f"检测到项目虚拟环境，请在 PowerShell 运行：\n  {command}"
        else:
            hint = (
                "请先创建虚拟环境并安装锁定依赖：\n"
                "  python -m venv .venv\n"
                "  .\\.venv\\Scripts\\python.exe -m pip install -r requirements-lock.txt"
            )
        raise RuntimeError(
            f"当前解释器 {sys.executable} 缺少依赖：{', '.join(missing)}。\n{hint}"
        )
    ok("核心 Python 依赖可导入")


def check_formal_result() -> dict:
    data = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    expected = {
        "run_mode": "live",
        "baseline_version": "v2-fixed-2026-08-11",
        "cases": 100,
        "system_llm_tokens": 0,
    }
    for key, value in expected.items():
        require(data.get(key) == value, f"正式结果 {key}={value}")

    numeric = {
        "fraud_recall": 0.8333,
        "fraud_fpr": 0.0,
        "rule_accuracy": 0.95,
        "ablation_lift_pp": 50.0,
    }
    for key, value in numeric.items():
        require(math.isclose(float(data.get(key)), value, abs_tol=1e-6), f"正式结果 {key}={value}")

    baseline = data.get("baseline", {})
    require(math.isclose(float(baseline.get("recall")), 0.3333, abs_tol=1e-6), "纯 LLM 基线召回=33.33%")
    require(math.isclose(float(baseline.get("fpr")), 0.0286, abs_tol=1e-6), "纯 LLM 基线误报率=2.86%")
    require(baseline.get("tokens") == 306201, "纯 LLM 基线 tokens=306,201")
    require(baseline.get("invalid_count") == 0 and not data.get("baseline_errors"), "基线 0 invalid / 0 errors")
    return data


def check_demo_contract(labels: list[dict], result: dict) -> None:
    by_id = {row["case_id"]: row for row in labels}
    require({"case_0021", "case_0058"} <= by_id.keys(), "Demo 案件对 case_0021 / case_0058 存在")

    def item_id(row: dict) -> str:
        return row["oracle"]["lease_items"]["fields"]["items.0.item_id"]["value"]

    require(item_id(by_id["case_0021"]) == item_id(by_id["case_0058"]), "Demo 案件对共享同一租赁物编号")
    per_case = result["per_case"]
    require(per_case["case_0021"]["grade"] == "pass", "首次出现 case_0021 的正式结果为 pass")
    require(
        per_case["case_0058"]["grade"] == "reject" and "R77-005" in per_case["case_0058"]["rules"],
        "后出现 case_0058 的正式结果命中 R77-005 并为 reject",
    )

    demo_text = (ROOT / "docs" / "demo_script.md").read_text(encoding="utf-8")
    require("case_0021" in demo_text and "case_0058" in demo_text, "路演脚本采用正确的历史案件序列")
    require("召回为 0%" in demo_text, "路演脚本采用正式重复资产基线召回 0%")


def context_row_from_state(state) -> dict:
    lease_fields: dict[str, dict[str, str]] = {}
    for index, item in enumerate(state.lease_items.items):
        lease_fields[f"items.{index}.item_id"] = {"value": item.item_id}
        lease_fields[f"items.{index}.serial_no"] = {"value": item.serial_no}
    return {
        "case_id": state.case_id,
        "oracle": {"lease_items": {"fields": lease_fields}},
        "metadata": {
            "buyer": state.contract.lessee.name,
            "seller": state.contract.vendor.name if state.contract.vendor else "",
            "sign_date": state.contract.sign_date.isoformat(),
            "total_amount": float(state.contract.total_amount.amount),
        },
    }


def run_demo_sequence(labels: list[dict]) -> None:
    from src.pipeline import run_pipeline

    by_id = {row["case_id"]: row for row in labels}
    with tempfile.TemporaryDirectory(prefix="jindun-preflight-") as temp:
        tmp = Path(temp)
        context = tmp / "history.jsonl"
        context.write_text("", encoding="utf-8")
        first = run_pipeline(
            "case_0021",
            by_id["case_0021"]["files"],
            "mock",
            base_dir=CASES,
            labels_path=context,
            audit_path=tmp / "audit.db",
            out_dir=tmp / "reports" / "case_0021",
            guard_llm=False,
        )
        require(first.risk_score is not None and first.risk_score.grade == "pass", "实跑首次出现 case_0021 为 pass")
        context.write_text(json.dumps(context_row_from_state(first), ensure_ascii=False) + "\n", encoding="utf-8")
        second = run_pipeline(
            "case_0058",
            by_id["case_0058"]["files"],
            "mock",
            base_dir=CASES,
            labels_path=context,
            audit_path=tmp / "audit.db",
            out_dir=tmp / "reports" / "case_0058",
            guard_llm=False,
        )
        require(any(hit.rule_id == "R77-005" for hit in second.rule_hits), "实跑后出现 case_0058 命中 R77-005")
        require(second.risk_score is not None and second.risk_score.grade == "reject", "实跑后出现 case_0058 为 reject")


def run_tests() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "pytest",
            "-q",
            "tests",
            "--basetemp",
            ".pytest-local",
        ],
        cwd=ROOT,
        check=False,
    )
    require(completed.returncode == 0, "pytest 回归测试通过")


def main() -> None:
    parser = argparse.ArgumentParser(description="算链金盾提交前离线预检")
    parser.add_argument("--run-demo", action="store_true", help="实跑 case_0021 -> case_0058 历史序列")
    parser.add_argument("--run-tests", action="store_true", help="运行 pytest 回归测试")
    parser.add_argument("--all", action="store_true", help="同时运行 Demo 序列与 pytest")
    args = parser.parse_args()

    check_required_files()
    check_imports()
    labels = read_labels()
    result = check_formal_result()
    check_demo_contract(labels, result)
    if args.run_demo or args.all:
        run_demo_sequence(labels)
    if args.run_tests or args.all:
        run_tests()
    ok("提交前预检完成")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1) from None
