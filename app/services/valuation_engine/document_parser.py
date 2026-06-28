from __future__ import annotations

from pathlib import Path
from typing import Any


SCAN_WARNING = "该 PDF 可能为扫描件，当前版本可能无法完整识别。后续可接入 OCR。"


def parse_project_document(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path).expanduser()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    return empty_result(path, [f"当前版本暂不支持 {suffix or '未知'} 文件解析，请优先上传 PDF。"])


def parse_pdf(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path).expanduser()
    warnings: list[str] = []
    pages: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []

    try:
        import fitz  # type: ignore
    except ImportError:
        fitz = None
        warnings.append("未安装 PyMuPDF，PDF 正文提取能力受限。")

    if fitz is not None:
        try:
            with fitz.open(path) as doc:
                for index, page in enumerate(doc, start=1):
                    pages.append(
                        {
                            "page_number": index,
                            "text": (page.get_text("text") or "").strip(),
                        }
                    )
        except Exception as exc:  # pragma: no cover - defensive UI guard
            warnings.append(f"PyMuPDF 读取失败：{exc}")

    try:
        import pdfplumber  # type: ignore
    except ImportError:
        pdfplumber = None
        warnings.append("未安装 pdfplumber，PDF 表格提取能力受限。")

    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                if not pages:
                    pages = [
                        {"page_number": index, "text": (page.extract_text() or "").strip()}
                        for index, page in enumerate(pdf.pages, start=1)
                    ]
                for index, page in enumerate(pdf.pages, start=1):
                    for table_index, table in enumerate(page.extract_tables() or [], start=1):
                        tables.append(
                            {
                                "page_number": index,
                                "table_index": table_index,
                                "rows": table,
                            }
                        )
        except Exception as exc:  # pragma: no cover - defensive UI guard
            warnings.append(f"pdfplumber 读取失败：{exc}")

    raw_text = "\n\n".join(page["text"] for page in pages if page.get("text")).strip()
    if len(raw_text) < 120:
        warnings.append(SCAN_WARNING)

    return {
        "file_name": path.name,
        "file_path": str(path),
        "pages": pages,
        "raw_text": raw_text,
        "tables": tables,
        "warnings": dedupe(warnings),
    }


def empty_result(file_path: Path, warnings: list[str]) -> dict[str, Any]:
    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "pages": [],
        "raw_text": "",
        "tables": [],
        "warnings": warnings,
    }


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
