"""外部效度测试：公开版式单据上的解析鲁棒性检验（v1 文本层口径 + v2 OCR 复测）。

用法：
    python -m eval.run_external                        # v1 口径（文本层，输出 external_validity.*）
    python -m eval.run_external --ocr                  # v3 口径（OCR+交叉校验，输出 external_validity_v3.*）
    ENABLE_OCR=1 python -m eval.run_external           # 等价于 --ocr

设计纪律：
- 只测解析鲁棒性与 pipeline 优雅降级，不测欺诈指标（样本无正常/欺诈标签）；
- 字段抽取器为**通用标签正则/通用同义标签表**，不针对任何样本写特例规则；
- 样本文件（data/external/）不入库、不上传、不再分发；输出不含银行账号/电话/身份证类
  敏感字段原文，样本以来源类型+渠道+日期描述，不附原件截图；
- "示范文本+模拟填写"样本（template_*）为官方空白模板填入合成示例值，不是真实合同；
- OCR（paddleocr）为可选能力：仅 --ocr 或 ENABLE_OCR=1 时启用，未安装时自动跳过且
  v1 口径结果不受影响；OCR 只跑含目标字段的关键页（成本裁剪，报告中注明）；
- OCR 低置信字段（行置信度 < 0.80）标记 ocr_low_confidence 转人工路由，
  不静默计为命中，也不计为失败。
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from config.settings import LLMSettings
from src.errors import ParseError
from src.parsing import ocr as ocr_mod
from src.parsing.parser import parse_document
from src.parsing.reader import PdfTextReader
from src.schemas import DocType
from src.validation import validate_document

# ---------------------------------------------------------------- 通用字段抽取器
# 标签型正则 + 通用同义标签表（出租人/出卖人/委托方……），面向中文合同/发票的
# 一般写法，不含任何样本特例。v2 相对 v1 的扩充仅为同义标签与通用条款标签。

_PARTY = r"([^\s，,；;：:]{3,40}?(?:公司|厂|中心))"
_NUM = r"([\d][\d,]*(?:\.\d{1,2})?)"
_CN_DATE = r"([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日|[0-9]{4}-[0-9]{2}-[0-9]{2})"

GENERIC_EXTRACTORS: dict[str, list[str]] = {
    "contract_no": [
        r"合同编号[：:\s]*【?([A-Za-z0-9][A-Za-z0-9\-/]{3,})】?",
    ],
    "lessor": [
        r"出租人[（(]?[^\n：:（(）)]{0,8}[）)]?\s*[：:]\s*【?" + _PARTY,
        r"甲方[（(]出租人[）)]\s*[：:]\s*【?" + _PARTY,
        r"甲方\s*[：:]\s*【?" + _PARTY,  # 融资租赁合同通用甲方=出租人
    ],
    "lessee": [
        r"承租人[（(]?[^\n：:（(）)]{0,8}[）)]?\s*[：:]\s*【?" + _PARTY,
        r"乙方[（(]承租人[）)]\s*[：:]\s*【?" + _PARTY,
        r"乙方\s*[：:]\s*【?" + _PARTY,  # 融资租赁合同通用乙方=承租人
    ],
    # 通用甲乙方（买卖/服务合同的签约主体）
    "party_a": [
        r"甲方[（(][^）)\n]{0,8}[）)]\s*[：:]\s*" + _PARTY,
        r"甲方\s*[：:]\s*" + _PARTY,
    ],
    "party_b": [
        r"乙方[（(][^）)\n]{0,8}[）)]\s*[：:]\s*" + _PARTY,
        r"乙方\s*[：:]\s*" + _PARTY,
    ],
    "amount": [
        r"(?:租赁物转让价款|转让价款|租赁本金|租赁成本|租赁物价款|合同总金额|租赁价款|"
        r"概算租赁本金|费用总额|合同金额|合同总价)"
        r"[^0-9¥￥]{0,25}[¥￥]?\s*【?\s*" + _NUM,
        # 买卖合同通用大写合计行：（大写）：…（￥8000000.00）
        r"合计人民币金额（大写）[^）\n]{0,40}（?\s*[¥￥]\s*【?\s*" + _NUM,
    ],
    "term_months": [
        r"租赁期限[^0-9]{0,25}?【?(\d{1,3})】?\s*个?月",
        r"【?(\d{1,3})】?\s*个?月(?=[^\n]{0,25}租赁期限)",  # 大表式版式：值在标签前行
    ],
    # 买卖/服务合同的通用期限写法
    "term_days": [
        r"(?:结算方式|付款方式|账期)[^。]{0,80}?(\d{1,3})\s*(?:个)?(?:日|天)",
    ],
    "term_end": [
        r"有效期至\s*" + _CN_DATE,
        r"(?:合同期限|服务期限|处理期限)[^。]{0,30}?至\s*" + _CN_DATE,
    ],
    # 标的物/标的数据（通用）
    "item_name": [
        r"数据名称[：:\s]*([^\n。]{2,40})",
        r"(?:标的名称|标的物|规格型号)[：:\s]*([A-Za-z0-9一-鿿][A-Za-z0-9\-一-鿿（）()]{2,40})",
    ],
    # 发票类
    "invoice_no": [r"发票号码[：:\s]*([0-9]{8,20})"],
    "invoice_date": [r"开票日期[：:\s]*" + _CN_DATE],
    "seller": [
        r"销售方[^：:\n]{0,6}名称[：:\s]*" + _PARTY,
        r"销售方[：:\s]*" + _PARTY,
        r"出卖人\s*[：:]\s*" + _PARTY,
    ],
    "buyer": [
        r"购买方[^：:\n]{0,6}名称[：:\s]*" + _PARTY,
        r"购买方[：:\s]*" + _PARTY,
        r"买受人\s*[：:]\s*" + _PARTY,
    ],
    "amount_incl_tax": [r"价税合计[^0-9¥￥]{0,15}[¥￥]?\s*" + _NUM],
    "tax_amount": [
        r"税\s*额[：:\s]*[¥￥]?\s*" + _NUM,
        # 发票通用版式：合计行双数值（金额、税额），取第二值为税额
        r"合\s*计[^0-9\n]{0,15}(?:[\d][\d,]*(?:\.\d{1,2})?)[^0-9\n]{0,15}" + _NUM,
    ],
}

_NUMERIC_FIELDS = {"amount", "amount_incl_tax", "tax_amount", "term_months",
                   "term_days", "lease_list_rows"}

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
    patterns = GENERIC_EXTRACTORS.get(field, [])
    if field == "amount":
        # 通用策略：合同金额通常为文中最大货币候选值（同一金额在价款/本金条款
        # 重复出现；误配的小额编号、期次等候选被自然淘汰）
        cands: list[float] = []
        best_raw: str | None = None
        for pattern in patterns:
            for m in re.finditer(pattern, full_text):
                try:
                    v = float(m.group(1).replace(",", ""))
                except ValueError:
                    continue
                if v > (cands[0] if cands else -1):
                    cands = [v]
                    best_raw = m.group(1).strip()
        return best_raw
    for pattern in patterns:
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
    if truth_value is None:  # 官方空白票样：抽到任意合理值即算命中
        return True
    if field in ("amount", "amount_incl_tax", "tax_amount"):
        try:
            return abs(float(truth_value) - float(extracted.replace(",", ""))) < 0.01
        except ValueError:
            return False
    if field in ("term_months", "term_days", "lease_list_rows"):
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


# ---------------------------------------------------------------- OCR 辅助


def _ocr_confidence(extracted: str | None, scores: dict[str, float]) -> float | None:
    """在 OCR 行中定位含抽取值的行，返回其最高置信度（用于低置信转人工路由）。"""
    if not extracted:
        return None
    target = _norm_text(extracted)
    best: float | None = None
    for text, score in scores.items():
        if target and target in _norm_text(text):
            best = score if best is None else max(best, score)
    return best


def _ocr_text(pdf_path: Path, pages: list[int] | None) -> tuple[str, dict]:
    """对指定页跑 OCR，返回拼接文本与成本/置信度元数据。无文本层样本专用。"""
    ocr_pages = ocr_mod.ocr_pdf_pages(pdf_path, pages=pages)
    pages_text = ocr_mod.ocr_pages_to_text(ocr_pages)
    full_text = "\n".join(ln for page in pages_text for ln in page)
    meta = {
        "pages_ocr": len(ocr_pages),
        "seconds_total": round(sum(r["seconds"] for r in ocr_pages), 2),
        "seconds_per_page": round(
            sum(r["seconds"] for r in ocr_pages) / max(len(ocr_pages), 1), 2),
        "scores": ocr_mod.line_score_map(ocr_pages),
    }
    return full_text, meta


# ---------------------------------------------------------------- 主流程


def run_external(truth_path: str | Path, out_dir: str | Path,
                 use_ocr: bool = False, stem: str | None = None,
                 title: str | None = None, preamble: str | None = None) -> dict:
    if stem is None:
        stem = "external_validity_v3" if use_ocr else "external_validity"
    truths = [
        json.loads(l)
        for l in Path(truth_path).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    mock_settings = LLMSettings(api_key=None, base_url="", model="mock")
    ocr_active = use_ocr and ocr_mod.is_available()
    samples: list[dict] = []
    mode_counts: dict[str, int] = {}
    total_low_conf = 0
    total_validation_review = 0

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

        # 两遍抽取：第一遍文本层；配置了 ocr_key_pages 且存在未命中字段时，
        # 第二遍 OCR 兜底（仅重抽未命中字段，保留文本层命中）。
        # 覆盖两类样本：无文本层扫描件、文本层仅标题而要素为嵌入图片的票样。
        ocr_meta: dict | None = None
        key_pages = t.get("ocr_key_pages")
        pass1: dict[str, str | None] = {
            f: extract_field(f, full_text) for f in t["fields"]
        }
        failed_present = [
            f for f, truth in t["fields"].items()
            if truth.get("present")
            and not match_value(f, truth.get("value"), pass1[f])
        ]
        need_ocr = bool(ocr_active and key_pages is not None and failed_present)
        ocr_text = ""
        scores: dict[str, float] = {}
        if need_ocr:
            ocr_text, ocr_meta = _ocr_text(path, key_pages)
            scores = ocr_meta.pop("scores")

        fields: dict[str, dict] = {}
        n_present = n_hit = 0
        for field, truth in t["fields"].items():
            present = bool(truth.get("present"))
            extracted = pass1[field]
            matched = present and match_value(field, truth.get("value"), extracted)
            via_ocr = False
            if need_ocr and present and not matched:
                cand = extract_field(field, ocr_text)
                if cand is not None:
                    extracted = cand
                    via_ocr = True
                    matched = match_value(field, truth.get("value"), extracted)
            low_conf = False
            if via_ocr and extracted is not None:
                conf = _ocr_confidence(extracted, scores)
                if conf is not None and conf < ocr_mod.FIELD_CONF_THRESHOLD:
                    low_conf = True
            annotated_mode = truth.get("failure_class")  # 人工标注的失败模式（仅失败时使用）
            if not present:
                status, mode, note = "expected_absent", "字段缺失", truth.get("note", "")
            elif low_conf and matched:
                status, mode = "ocr_low_confidence", None
                note = f"OCR 行置信度 < {ocr_mod.FIELD_CONF_THRESHOLD}，转人工路由（不静默计命中）"
            elif matched:
                status, mode, note = "ok", None, ("OCR 兜底命中" if via_ocr else "")
            elif low_conf:
                status, mode = "ocr_low_confidence", None
                note = "OCR 低置信且与真值不符，转人工路由"
            elif need_ocr:
                status = "fail"
                if annotated_mode:
                    mode = annotated_mode
                elif extracted is None:
                    mode = "ocr 漏识别（遮挡/水印/跨页断裂）"
                else:
                    mode = "ocr 误识别（字形混淆）"
                note = "OCR 复测未命中"
            elif not reader.has_text_layer:
                status, mode, note = "fail", "扫描页无文本层", "整本无文本层，正则/LLM 均无可抽取文本"
            elif extracted is None:
                if annotated_mode:
                    status, mode, note = "fail", annotated_mode, "标签/结构未被通用正则覆盖"
                elif t["sample_id"] == "invoice_style":
                    status, mode, note = "fail", "字段缺失", "票面要素以图片嵌入，文本层仅分节标题"
                else:
                    status, mode, note = "fail", "条款结构差异", "标签写法未被通用正则覆盖"
            else:
                wm = _watermark_hint(reader)
                status = "fail"
                if annotated_mode:
                    mode, note = annotated_mode, "抽取到值但与真值不符"
                else:
                    mode = "水印干扰" if wm else "条款结构差异"
                    note = "抽取到值但与真值不符" + ("（疑似水印字符干扰）" if wm else "")
            fields[field] = {
                "truth_present": present,
                "extracted": extracted is not None,
                "matched": matched,
                "status": status,
                "failure_mode": mode,
                "note": note,
            }

        # ---------------- v3：字段级交叉校验（仅 OCR/v3 模式；默认 v1 口径不受影响）
        # 金额大写/小写交叉 + 期限边界/一致性；review 级标记 → 字段置信度置 0 转人审，
        # 不静默采信（如 contract_C term_months 的 "44 vs 144" 多值冲突）。
        sample_flags: list[dict] = []
        if use_ocr:
            eff_text = ocr_text if need_ocr else full_text
            doc_kind = "invoice" if t["sample_id"].startswith("invoice") else "contract"
            for vf in validate_document(eff_text, doc_kind):
                entry = {"field_name": vf.field_name, "reason_code": vf.reason_code,
                         "severity": vf.severity, "detail": vf.detail,
                         "raw_masked": vf.raw_masked}
                sample_flags.append(entry)
                if vf.severity != "review":
                    continue
                if vf.reason_code.startswith("amount"):
                    target = "amount" if "amount" in fields else (
                        "amount_incl_tax" if "amount_incl_tax" in fields else None)
                else:
                    target = next((f for f in ("term_months", "term_days", "term_end")
                                   if f in fields), None)
                if target and fields[target]["truth_present"]:
                    fr = fields[target]
                    fr["status"] = "validation_review"
                    fr["failure_mode"] = vf.reason_code
                    fr["note"] = vf.detail + "（字段置信度置 0，转人审）"
                    fr["matched"] = False

        # 校验覆盖后统一计数：命中=status ok；失败模式只统计 fail；review 单列
        n_present = n_hit = 0
        for f, r_ in fields.items():
            if not r_["truth_present"]:
                continue
            n_present += 1
            if r_["status"] == "ok":
                n_hit += 1
            elif r_["status"] == "fail" and r_["failure_mode"]:
                mode_counts[r_["failure_mode"]] = mode_counts.get(r_["failure_mode"], 0) + 1
        n_validation_review = sum(1 for r_ in fields.values()
                                  if r_["status"] == "validation_review")
        total_validation_review += n_validation_review
        n_low_conf = sum(1 for r_ in fields.values()
                         if r_["status"] == "ocr_low_confidence")
        total_low_conf += n_low_conf

        # 优雅降级验证：现有解析入口对样本的行为（强制 mock，不触 LLM）
        # 无文本层样本期望结构化 ParseError；有文本层样本（示范文本）解析成功也属正常，
        # 只有未结构化异常才算降级失败。
        degradation: dict
        try:
            dt = DocType.INVOICE if t["sample_id"].startswith("invoice") else DocType.CONTRACT
            parse_document(path, dt, mock_settings)
            if reader.has_text_layer:
                degradation = {"graceful": True, "outcome": "parsed_successfully",
                               "note": "有文本层样本解析成功（mock 模式）"}
            else:
                degradation = {"graceful": False, "outcome": "unexpected_success",
                               "note": "无文本层样本竟解析成功，需排查"}
        except ParseError as e:
            degradation = {"graceful": True, "outcome": "structured_parse_error",
                           "code": e.code, "message": str(e)[:120]}
        except Exception as e:  # 未结构化异常 = 降级失败
            degradation = {"graceful": False, "outcome": "unhandled_exception",
                           "note": f"{type(e).__name__}: {str(e)[:120]}"}
        reader.close()

        sample = {
            "sample_id": t["sample_id"],
            "source": t["source"],
            "annotation_method": t["annotation_method"],
            "text_layer": text_layer,
            "fields": fields,
            "extraction_rate": round(n_hit / n_present, 4) if n_present else None,
            "fields_hit": f"{n_hit}/{n_present}",
            "degradation": degradation,
        }
        if sample_flags:
            sample["validation_flags"] = sample_flags
        if ocr_meta is not None:
            sample["ocr"] = {
                "pages_ocr": ocr_meta["pages_ocr"],
                "seconds_total": ocr_meta["seconds_total"],
                "seconds_per_page": ocr_meta["seconds_per_page"],
                "key_pages_only": t.get("ocr_key_pages") is not None,
            }
        samples.append(sample)

    total_present = sum(int(s["fields_hit"].split("/")[1]) for s in samples)
    total_hit = sum(int(s["fields_hit"].split("/")[0]) for s in samples)
    result = {
        "test": stem,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ocr_enabled": ocr_active,
        "ocr_note": (
            "OCR（paddleocr 3.7 + paddlepaddle 3.2.2，250DPI，仅关键页）已启用；"
            "低置信字段转人工路由（ocr_low_confidence）；"
            "字段级交叉校验（金额大写/小写、期限边界/一致性）已启用，review 级标记转人审。"
            if ocr_active else
            "OCR 未启用（--ocr 或 ENABLE_OCR=1 可开启）；扫描件无文本层属预期行为边界。"
        ),
        "samples_dir": "data/external/（不入库、不上传、不再分发）",
        "samples": samples,
        "summary": {
            "samples_n": len(samples),
            "fields_hit": total_hit,
            "fields_present": total_present,
            "overall_extraction_rate": round(total_hit / total_present, 4) if total_present else None,
            "ocr_low_confidence_fields": total_low_conf,
            "validation_review_fields": total_validation_review,
            "failure_mode_counts": mode_counts,
            "degradation_all_graceful": all(s["degradation"]["graceful"] for s in samples),
        },
        "sensitive_policy": "输出不含银行账号/电话/身份证类敏感字段原文；样本以来源类型+渠道+日期描述。",
    }
    if not use_ocr:
        result["summary"]["untouched_modes"] = {
            "水印干扰": "合同 C 全文对角水印，但因无文本层未触及该失败面（--ocr 复测触及）",
            "跨页表格断裂": "合同 B/C 清单均为跨页表格，但因无文本层未触及该失败面（--ocr 复测触及）",
        }

    # v3 与 v1/v2 对比（若结果存在）；并列出 v2→v3 字段级状态变化（校验拦截记录）
    if use_ocr:
        v1_path = Path(out_dir) / "external_validity.json"
        if v1_path.exists():
            v1 = json.loads(v1_path.read_text(encoding="utf-8"))
            cmp_rows = []
            v1_by_id = {s["sample_id"]: s for s in v1["samples"]}
            for s in samples:
                v1s = v1_by_id.get(s["sample_id"])
                cmp_rows.append({
                    "sample_id": s["sample_id"],
                    "v1_hit": v1s["fields_hit"] if v1s else "—（v3 新增样本）",
                    "v3_hit": s["fields_hit"],
                })
            result["v1_comparison"] = cmp_rows
        v2_path = Path(out_dir) / "external_validity_v2.json"
        if v2_path.exists():
            v2 = json.loads(v2_path.read_text(encoding="utf-8"))
            v2_by_id = {s["sample_id"]: s for s in v2["samples"]}
            changes = []
            for s in samples:
                v2s = v2_by_id.get(s["sample_id"])
                if not v2s:
                    continue
                for f, r_ in s["fields"].items():
                    old = v2s["fields"].get(f, {})
                    if old.get("status") != r_["status"]:
                        changes.append({
                            "sample_id": s["sample_id"], "field": f,
                            "v2_status": f"{old.get('status')}/{old.get('failure_mode') or ''}",
                            "v3_status": f"{r_['status']}/{r_.get('failure_mode') or ''}",
                        })
            result["v2_to_v3_changes"] = changes

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_text = render_md(result, title=title, stem=stem)
    if preamble:
        md_text = preamble.rstrip() + "\n\n---\n\n" + md_text
    (out / f"{stem}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / f"{stem}.md").write_text(md_text, encoding="utf-8")
    return result


# ---------------------------------------------------------------- 报告


def _src_desc(s: dict) -> str:
    src = s["source"]
    return f"{src['type']}（{src['channel']}，{src['date']}）"


def render_md(r: dict, title: str | None = None, stem: str | None = None) -> str:
    L: list[str] = []
    if title is None:
        title = ("外部效度测试报告 v3（OCR + 字段级交叉校验）" if r["ocr_enabled"]
                 else "外部效度 mini-test 报告")
    L.append(f"# {title}\n")
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
    has_ocr = any("ocr" in s for s in r["samples"])
    if has_ocr:
        L.append("| 样本 | 抽取成功率 | OCR 页数/耗时 | 优雅降级行为 |")
        L.append("|---|---|---|---|")
    else:
        L.append("| 样本 | 抽取成功率 | 优雅降级行为 |")
        L.append("|---|---|---|")
    for s in r["samples"]:
        rate = "N/A" if s["extraction_rate"] is None else f"{s['extraction_rate']:.0%}"
        d = s["degradation"]
        dtxt = (f"✅ {d.get('outcome', '')} {d.get('code', '')}".strip()
                if d["graceful"] else f"❌ {d['outcome']}")
        if has_ocr:
            o = s.get("ocr")
            otxt = (f"{o['pages_ocr']} 页 / {o['seconds_total']:.0f}s"
                    f"（{o['seconds_per_page']:.0f}s/页"
                    f"{'，仅关键页' if o['key_pages_only'] else ''}）") if o else "—"
            L.append(f"| {_src_desc(s)} | {s['fields_hit']}（{rate}） | {otxt} | {dtxt} |")
        else:
            L.append(f"| {_src_desc(s)} | {s['fields_hit']}（{rate}） | {dtxt} |")
    L.append("")
    L.append("### 逐字段明细\n")
    L.append("| 样本 | 字段 | 真值存在 | 抽到值 | 命中 | 失败模式/状态 |")
    L.append("|---|---|---|---|---|---|")
    for s in r["samples"]:
        for f, r_ in s["fields"].items():
            if r_["status"] == "ocr_low_confidence":
                mark, mode = "⚠️转人工", "ocr_low_confidence"
            elif r_["status"] == "validation_review":
                mark, mode = "🛑转人审", r_["failure_mode"] or "validation"
            else:
                mark = "✅" if r_["matched"] else "—" if not r_["truth_present"] else "❌"
                mode = r_["failure_mode"] or ""
            L.append(f"| {s['sample_id']} | {f} | "
                     f"{'是' if r_['truth_present'] else '否(预期不可抽取)'} | "
                     f"{'是' if r_['extracted'] else '否'} | {mark} | {mode} |")
    L.append("")
    # v3：字段级交叉校验标记明细
    flag_rows = [
        (s["sample_id"], vf)
        for s in r["samples"] for vf in s.get("validation_flags", [])
    ]
    if flag_rows:
        L.append("### 字段级交叉校验标记（v3 新增）\n")
        L.append("| 样本 | 字段 | 原因码 | 级别 | 说明 |")
        L.append("|---|---|---|---|---|")
        for sid, vf in flag_rows:
            icon = "🛑" if vf["severity"] == "review" else "ℹ️"
            L.append(f"| {sid} | {vf['field_name']} | {vf['reason_code']} | "
                     f"{icon}{vf['severity']} | {vf['detail'][:60]} |")
        L.append("")
    sm = r["summary"]
    L.append("## 失败模式分类汇总\n")
    L.append("| 失败模式 | 字段数 | 说明 |")
    L.append("|---|---|---|")
    for mode, n in sm["failure_mode_counts"].items():
        L.append(f"| {mode} | {n} | |")
    for mode, note in sm.get("untouched_modes", {}).items():
        L.append(f"| {mode} | 0 | {note} |")
    L.append("")
    L.append(f"**总体抽取率：{sm['fields_hit']}/{sm['fields_present']}"
             + (f"（{sm['overall_extraction_rate']:.0%}）" if sm["overall_extraction_rate"] is not None else "")
             + f"；OCR 低置信转人工：{sm['ocr_low_confidence_fields']}；"
             f"交叉校验转人审：{sm.get('validation_review_fields', 0)}；"
             f"优雅降级全部正常：{'是' if sm['degradation_all_graceful'] else '否'}**")
    L.append("")
    cur = stem or ("external_validity_v3" if r["ocr_enabled"] else "external_validity")
    if r.get("v2_to_v3_changes"):
        L.append(f"## v2 → 本轮（{cur}）字段级状态变化（交叉校验拦截记录）\n")
        L.append("| 样本 | 字段 | v2 状态 | v3 状态 |")
        L.append("|---|---|---|---|")
        for c in r["v2_to_v3_changes"]:
            L.append(f"| {c['sample_id']} | {c['field']} | {c['v2_status']} | {c['v3_status']} |")
        L.append("")
    if r.get("v1_comparison"):
        L.append(f"## 与 v1（纯文本层口径）对比\n")
        L.append(f"| 样本 | v1 命中 | 本轮（{cur}）命中 |")
        L.append("|---|---|---|")
        for c in r["v1_comparison"]:
            L.append(f"| {c['sample_id']} | {c['v1_hit']} | {c['v3_hit']} |")
        L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="eval.run_external")
    ap.add_argument("--truth", type=Path, default=Path("eval/external_truth.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("eval/results"))
    ap.add_argument("--ocr", action="store_true",
                    help="启用 PaddleOCR 可选路径复测无文本层样本（输出 *_v2.*）")
    ap.add_argument("--stem", default=None,
                    help="输出文件名前缀（默认 external_validity / external_validity_v3）")
    ap.add_argument("--title", default=None, help="报告标题（默认按模式自动选择）")
    ap.add_argument("--preamble-file", type=Path, default=None,
                    help="可选：报告开头追加的说明文件（如修正/归因说明）")
    args = ap.parse_args(argv)
    use_ocr = args.ocr or os.getenv("ENABLE_OCR") == "1"
    preamble = (args.preamble_file.read_text(encoding="utf-8")
                if args.preamble_file else None)
    r = run_external(args.truth, args.out, use_ocr=use_ocr,
                     stem=args.stem, title=args.title, preamble=preamble)
    print(render_md(r, title=args.title, stem=args.stem))
    stem = args.stem or ("external_validity_v3" if use_ocr else "external_validity")
    print(f"结果已落盘: {args.out / (stem + '.json')} / {args.out / (stem + '.md')}")
    return r


if __name__ == "__main__":
    main()
