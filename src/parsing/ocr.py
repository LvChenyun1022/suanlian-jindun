"""PaddleOCR 可选路径（预留能力，外部效度 v2 启用）。

纪律：
- 默认关闭：仅在 eval/run_external.py --ocr 或环境变量 ENABLE_OCR=1 时启用；
- 未安装 paddleocr/paddlepaddle 时 is_available()=False，一切行为与未安装前一致；
- 逐页结果写穿缓存（可中断续跑）；置信度低于阈值的行保留但标记，
  字段级低置信度由调用方转人工路由（ocr_low_confidence），不静默采用。
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

DEFAULT_DPI = 250
LOW_CONF_LINE_DROP = 0.30      # 低于此置信度的行直接丢弃（噪声）
FIELD_CONF_THRESHOLD = 0.80    # 字段级低置信度阈值（转人工路由）


def is_available() -> bool:
    try:
        import paddle  # noqa: F401
        import paddleocr  # noqa: F401
        return True
    except Exception:
        return False


def ocr_enabled() -> bool:
    return os.getenv("ENABLE_OCR") == "1"


_ocr_engine = None


def _get_engine():
    """惰性初始化 PaddleOCR 中文引擎（首次运行会下载模型）。"""
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        _ocr_engine = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="ch",
        )
    return _ocr_engine


def _cache_path(cache_dir: Path, pdf_path: Path, dpi: int) -> Path:
    return cache_dir / f"{pdf_path.stem}.ocr_{dpi}dpi.jsonl"


def load_ocr_cache(cache_dir: Path, pdf_path: Path, dpi: int) -> dict[int, dict]:
    """读取逐页 OCR 缓存 {page_index0: page_record}。"""
    pages: dict[int, dict] = {}
    path = _cache_path(cache_dir, pdf_path, dpi)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                pages[rec["page"]] = rec
    return pages


def ocr_pdf_pages(
    pdf_path: str | Path,
    dpi: int = DEFAULT_DPI,
    cache_dir: str | Path | None = None,
    max_pages: int | None = None,
    pages: list[int] | None = None,
) -> list[dict]:
    """PDF → 逐页 OCR（200–300 DPI 渲染，中文模型）。

    pages 指定 0 基页码子集（关键页成本控制）；为 None 时取前 max_pages 页。
    返回 [{page, width, height, dpi, seconds, lines: [{text, score, bbox}]}]
    bbox 为 PDF 用户空间坐标（左上原点，与渲染图像一致）。写穿缓存可续跑。
    """
    import pymupdf

    pdf_path = Path(pdf_path)
    cache_dir = Path(cache_dir) if cache_dir else pdf_path.parent / "ocr_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = load_ocr_cache(cache_dir, pdf_path, dpi)
    engine = _get_engine()
    doc = pymupdf.open(pdf_path)
    if pages is not None:
        want = [p for p in pages if 0 <= p < doc.page_count]
    else:
        n = doc.page_count if max_pages is None else min(max_pages, doc.page_count)
        want = list(range(n))
    cache_file = _cache_path(cache_dir, pdf_path, dpi)

    results: list[dict] = []
    for i in want:
        if i in cached:
            results.append(cached[i])
            continue
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        import numpy as np
        from PIL import Image

        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        t0 = time.perf_counter()
        preds = engine.predict(np.array(img))
        elapsed = time.perf_counter() - t0
        lines: list[dict] = []
        for pred in preds:
            texts = pred.get("rec_texts", []) if isinstance(pred, dict) else []
            scores = pred.get("rec_scores", []) if isinstance(pred, dict) else []
            polys = pred.get("rec_polys", []) if isinstance(pred, dict) else []
            for text, score, poly in zip(texts, scores, polys):
                if not text or score < LOW_CONF_LINE_DROP:
                    continue
                xs = [float(p[0]) for p in poly]
                ys = [float(p[1]) for p in poly]
                scale = 72.0 / dpi  # 像素 → PDF 点
                lines.append({
                    "text": text,
                    "score": round(float(score), 4),
                    "bbox": [min(xs) * scale, min(ys) * scale,
                             max(xs) * scale, max(ys) * scale],
                })
        rec = {"page": i, "width": page.rect.width, "height": page.rect.height,
               "dpi": dpi, "seconds": round(elapsed, 2), "lines": lines}
        with cache_file.open("a", encoding="utf-8") as f:  # 写穿：逐页落盘
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        results.append(rec)
        cached[i] = rec
    doc.close()
    results.sort(key=lambda r: r["page"])
    return results


def ocr_pages_to_text(ocr_pages: list[dict]) -> list[list[str]]:
    """OCR 结果 → 与 PdfTextReader.pages_text 对齐的逐页行文本（按阅读顺序 y,x 排序）。"""
    pages_text: list[list[str]] = []
    for rec in ocr_pages:
        lines = sorted(rec["lines"], key=lambda l: (round(l["bbox"][1], 1), l["bbox"][0]))
        pages_text.append([l["text"] for l in lines])
    return pages_text


def line_score_map(ocr_pages: list[dict]) -> dict[str, float]:
    """文本行 → 最高置信度（字段级低置信度路由用）。"""
    scores: dict[str, float] = {}
    for rec in ocr_pages:
        for l in rec["lines"]:
            scores[l["text"]] = max(scores.get(l["text"], 0.0), l["score"])
    return scores
