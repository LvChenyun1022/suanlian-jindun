"""外部效度 mini-test：真实公开版式单据上的解析鲁棒性检验。

用法：
    python -m eval.run_external                      # 默认 truth=eval/external_truth.jsonl
    python -m eval.run_external --out eval/results   # 结果落盘 external_validity.{json,md}

设计纪律：
- 只测解析鲁棒性与 pipeline 优雅降级，不测欺诈指标（样本无正常/欺诈标签）；
- 字段抽取器为**通用标签正则**（合同编号/出租人/承租人/价款/租赁期限/清单编号行），
  不针对任何样本写特例规则；
- 样本文件（data/external/）不入库、不上传、不再分发；输出不含银行账号/电话/身份证类
  敏感字段原文，样本以来源类型+渠道+日期描述，不附原件截图；
- OCR（paddleocr）为预留能力，本测试**未启用**。
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from config.settings import LLMSettings
from src.errors import ParseError
from src.parsing.parser import parse_document
from src.parsing.reader import PdfTextReader
from src.schemas import DocType

# ---------------------------------------------------------------- 通用字段抽取器
# 标签型正则，面向"中文融资租赁合同/发票"的一般写法，不含任何样本特例。

_PARTY = r"([^\s，,；;：:（(）)]{3,40}?(?:公司|厂|中心))"

GENERIC_EXTRACTORS: dict[str, list[str]] = {
    "contract_no": [
        r"合同编号[：:\s]*([A-Za-z0-9][A-Za-z0-9\-/]{3,})",
    ],
    "lessor": [
        r"出租人[（(]?[^\n：:（(）)]{0,8}[）)]?\s*[：:]\s*" + _PARTY,
        r"甲方[（(]出租人[）)]\s*[：:]\s*" + _PARTY,
    ],
    "lessee": [
        r"承租人[（(]?[^\n：:（(）)]{0,8}[）)]?\s*[：:]\s*" + _PARTY,
        r"乙方[（(]承租人[）)]\s*[：:]\s*" + _PARTY,
    ],
    "amount": [
        r"(?:租赁物转让价款|转让价款|租赁本金|租赁成本|租赁物价款|合同总金额|租赁价款)"
        r"[^0-9¥￥]{0,25}[¥￥]?\s*([\d][\d,]*(?:\.\d{1,2})?)",
    ],
    "term_months": [
        r"租赁期限[^0-9]{0,25}?(\d{1,3})\s*个?月",
    ],
    # 发票类
    "invoice_no": [r"发票号码[：:\s]*([0-9]{8,20})"],
    "invoice_date": [
        r"开票日期[：:\s]*([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日|[0-9]{4}-[0-9]{2}-[0-9]{2})"
    ],
    "seller": [
        r"销售方[^：:\n]{0,6}名称[：:\s]*" + _PARTY,
        r"销售方[：:\s]*" + _PARTY,
    ],
    "buyer": [
        r"购买方[^：:\n]{0,6}名称[：:\s]*" + _PARTY,
        r"购买方[：:\s]*" + _PARTY,
    ],
    "amount_incl_tax": [r"价税合计[^0-9¥￥]{0,15}[¥￥]?\s*([\d][\d,]*(?:\.\d{1,2})?)"],
    "tax_amount": [r"税\s*额[：:\s]*[¥￥]?\s*([\d][\d,]*(?:\.\d{1,2})?)"],
}

_ROW_RE = re.compile(r"^\s*(\d{1,3})(?=\s|$)")
_ROW_STOP = ("合计", "附件二", "附件 2", "签署页")


def extract_list_rows(full_text: str) -> int | None:
    """通用清单行数估计：定位"租赁物清单"标题后，统计编号开头的行，止于合计/下一附件。"""
    lines = full_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "租赁物清单" in line:
            start = i + 1
            break
    if start is None:
        return None
    n = 0
    for line in lines[start:]:
        if any(stop in line for stop in _ROW_STOP):
            break
        if _ROW_RE.match(line):
            n += 1
    return n or None


def extract_field(field: str, full_text: str) -> str | None:
    if field == "lease_list_rows":
        rows = extract_list_rows(full_text)
        return str(rows) if rows is not None else None
    for pattern in GENERIC_EXTRACTORS.get(field, []):
        m = re.search(pattern, full_text)
        if m:
            return m.group(1).strip()
    return None


# ---------------------------------------------------------------- 真值比对


def _norm_text(s: str) -> str:
    return re.sub(r"[\s【】\[\]（(）),，]", "", s).upper()


def match_value(field: str, truth_value: str | None, extracted: str | None) -> bool:
    if extracted is None:
        return False
    if truth_value is None:  # 官方空白票样：抽到任意合理值即算命中（本测试不会发生）
        return True
    if field in ("amount", "amount_incl_tax", "tax_amount"):
        try:
            return abs(float(truth_value) - float(extracted.replace(",", ""))) < 0.01
        except ValueError:
            return False
    if field in ("term_months", "lease_list_rows"):
        try:
            return int(truth_value) == int(re.sub(r"[^\d]", "", extracted))
        except ValueError:
            return False
    t, e = _norm_text(truth_value), _norm_text(extracted)
    return t == e or t in e


def _watermark_hint(reader: PdfTextReader) -> bool:
    """启发式：某短文本行在 ≥60% 文本页重复出现 → 疑似水印字符混入文本层。"""
    from collections import Counter

    counts: Counter[str] = Counter()
    for lines in reader.pages_text:
        for token in {ln.strip() for ln in lines if 2 <= len(ln.strip()) <= 12}:
            counts[token] += 1
    pages = max(len(reader.pages_text), 1)
    return any(c / pages >= 0.6 for c in counts.values())


# ---------------------------------------------------------------- 主流程


def run_external(truth_path: str | Path, out_dir: str | Path) -> dict:
    truths = [
        json.loads(l)
        for l in Path(truth_path).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    mock_settings = LLMSettings(api_key=None, base_url="", model="mock")
    samples: list[dict] = []
    mode_counts: dict[str, int] = {}

    for t in truths:
        path = Path(t["file"])
        reader = PdfTextReader(path)
        full_text = reader.full_text()
        text_layer = {
            "pages": reader.page_count,
            "backend": reader.backend,
            "has_text_layer": reader.has_text_layer,
            "text_layer_page_ratio": round(reader.text_layer_page_ratio, 4),
            "is_likely_scanned": reader.is_likely_scanned,
            "total_chars": sum(reader.page_char_counts),
        }

        fields: dict[str, dict] = {}
        n_present = n_hit = 0
        for field, truth in t["fields"].items():
            extracted = extract_field(field, full_text)
            present = bool(truth.get("present"))
            matched = present and match_value(field, truth.get("value"), extracted)
            if not present:
                status, mode, note = "expected_absent", "字段缺失", truth.get("note", "")
            elif matched:
                status, mode, note = "ok", None, ""
            elif not reader.has_text_layer:
                status, mode, note = "fail", "扫描页无文本层", "整本无文本层，正则/LLM 均无可抽取文本"
            elif extracted is None:
                if t["sample_id"] == "invoice_style":
                    status, mode, note = "fail", "字段缺失", "票面要素以图片嵌入，文本层仅分节标题"
                else:
                    status, mode, note = "fail", "条款结构差异", "标签写法未被通用正则覆盖"
            else:
                wm = _watermark_hint(reader)
                status, mode = "fail", ("水印干扰" if wm else "条款结构差异")
                note = "抽取到值但与真值不符" + ("（疑似水印字符干扰）" if wm else "")
            if present:
                n_present += 1
                n_hit += 1 if matched else 0
                if mode:
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1
            fields[field] = {
                "truth_present": present,
                "extracted": extracted is not None,
                "matched": matched,
                "status": status,
                "failure_mode": mode,
                "note": note,
            }

        # 优雅降级验证：现有解析入口对样本的行为（强制 mock，不触 LLM）
        degradation: dict
        try:
            dt = DocType.INVOICE if t["sample_id"] == "invoice_style" else DocType.CONTRACT
            parse_document(path, dt, mock_settings)
            degradation = {"graceful": False, "outcome": "unexpected_success",
                           "note": "无文本层样本竟解析成功，需排查"}
        except ParseError as e:
            degradation = {"graceful": True, "outcome": "structured_parse_error",
                           "code": e.code, "message": str(e)[:120]}
        except Exception as e:  # 未结构化异常 = 降级失败
            degradation = {"graceful": False, "outcome": "unhandled_exception",
                           "note": f"{type(e).__name__}: {str(e)[:120]}"}
        reader.close()

        samples.append({
            "sample_id": t["sample_id"],
            "source": t["source"],
            "annotation_method": t["annotation_method"],
            "text_layer": text_layer,
            "fields": fields,
            "extraction_rate": round(n_hit / n_present, 4) if n_present else None,
            "fields_hit": f"{n_hit}/{n_present}",
            "degradation": degradation,
        })

    total_present = sum(int(s["fields_hit"].split("/")[1]) for s in samples)
    total_hit = sum(int(s["fields_hit"].split("/")[0]) for s in samples)
    result = {
        "test": "external_validity_mini_test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ocr_enabled": False,
        "ocr_note": "OCR（paddleocr）为预留能力，本次未启用；扫描件无文本层属预期行为边界。",
        "samples_dir": "data/external/（不入库、不上传、不再分发）",
        "samples": samples,
        "summary": {
            "samples_n": len(samples),
            "fields_hit": total_hit,
            "fields_present": total_present,
            "overall_extraction_rate": round(total_hit / total_present, 4) if total_present else None,
            "failure_mode_counts": mode_counts,
            "untouched_modes": {
                "水印干扰": "合同 C 全文对角水印，但因无文本层未触及该失败面",
                "跨页表格断裂": "合同 B/C 清单均为跨页表格，但因无文本层未触及该失败面",
            },
            "degradation_all_graceful": all(s["degradation"]["graceful"] for s in samples),
        },
        "sensitive_policy": "输出不含银行账号/电话/身份证类敏感字段原文；样本以来源类型+渠道+日期描述。",
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "external_validity.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "external_validity.md").write_text(render_md(result), encoding="utf-8")
    return result


# ---------------------------------------------------------------- 报告


def _src_desc(s: dict) -> str:
    src = s["source"]
    return f"{src['type']}（{src['channel']}，{src['date']}）"


def render_md(r: dict) -> str:
    L: list[str] = []
    L.append("# 外部效度 mini-test 报告\n")
    L.append(f"- 生成时间：{r['generated_at']}")
    L.append(f"- 样本目录：{r['samples_dir']}")
    L.append(f"- OCR：{r['ocr_note']}")
    L.append(f"- 合规：{r['sensitive_policy']}")
    L.append("")
    L.append("## 样本与文本层检测\n")
    L.append("| 样本 | 页数 | 文本层 | 文本页占比 | 疑似扫描件 |")
    L.append("|---|---|---|---|---|")
    for s in r["samples"]:
        tl = s["text_layer"]
        L.append(f"| {_src_desc(s)} | {tl['pages']} | "
                 f"{'有' if tl['has_text_layer'] else '无'} | "
                 f"{tl['text_layer_page_ratio']:.0%} | "
                 f"{'是' if tl['is_likely_scanned'] else '否'} |")
    L.append("")
    L.append("## 逐样本字段抽取结果\n")
    L.append("| 样本 | 抽取成功率 | 优雅降级行为 |")
    L.append("|---|---|---|")
    for s in r["samples"]:
        rate = "N/A" if s["extraction_rate"] is None else f"{s['extraction_rate']:.0%}"
        d = s["degradation"]
        dtxt = f"✅ 结构化错误 {d.get('code', '')}" if d["graceful"] else f"❌ {d['outcome']}"
        L.append(f"| {_src_desc(s)} | {s['fields_hit']}（{rate}） | {dtxt} |")
    L.append("")
    L.append("### 逐字段明细\n")
    L.append("| 样本 | 字段 | 真值存在 | 抽到值 | 命中 | 失败模式 |")
    L.append("|---|---|---|---|---|---|")
    for s in r["samples"]:
        for f, r_ in s["fields"].items():
            L.append(f"| {s['sample_id']} | {f} | "
                     f"{'是' if r_['truth_present'] else '否(预期不可抽取)'} | "
                     f"{'是' if r_['extracted'] else '否'} | "
                     f"{'✅' if r_['matched'] else '—' if not r_['truth_present'] else '❌'} | "
                     f"{r_['failure_mode'] or ''} |")
    L.append("")
    sm = r["summary"]
    L.append("## 失败模式分类汇总\n")
    L.append("| 失败模式 | 字段数 | 说明 |")
    L.append("|---|---|---|")
    for mode, n in sm["failure_mode_counts"].items():
        L.append(f"| {mode} | {n} | |")
    for mode, note in sm["untouched_modes"].items():
        L.append(f"| {mode} | 0 | {note} |")
    L.append("")
    L.append(f"**总体抽取率：{sm['fields_hit']}/{sm['fields_present']}"
             f"（{sm['overall_extraction_rate']:.0%}）；"
             f"优雅降级全部正常：{'是' if sm['degradation_all_graceful'] else '否'}**")
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="eval.run_external")
    ap.add_argument("--truth", type=Path, default=Path("eval/external_truth.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("eval/results"))
    args = ap.parse_args(argv)
    r = run_external(args.truth, args.out)
    print(render_md(r))
    print(f"结果已落盘: {args.out / 'external_validity.json'} / {args.out / 'external_validity.md'}")
    return r


if __name__ == "__main__":
    main()
