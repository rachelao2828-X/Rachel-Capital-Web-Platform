from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.services.ecosystem_loader import extract_sections, parse_bool, parse_markdown_table, split_frontmatter
from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS


QUARTERLY_TRACKING_SOURCE_DIR = Path("02_战略生态") / "季度跟踪表"
QUARTERLY_TRACKING_OVERVIEW_NAME = "七大战略生态季度跟踪总览"


def quarterly_tracking_ecosystem_names() -> list[str]:
    return [name for name in ECOSYSTEM_OPTIONS if name not in {"中国关键技术攻关长期跟踪", "其他"}]


def quarterly_tracking_root(vault_path: str | None = None) -> Path:
    vault = Path(vault_path or settings.obsidian_vault_path or "")
    return vault / QUARTERLY_TRACKING_SOURCE_DIR


def quarterly_tracking_path(name: str, vault_path: str | None = None) -> Path:
    return quarterly_tracking_root(vault_path=vault_path) / f"{name}.md"


def quarterly_tracking_overview_path(vault_path: str | None = None) -> Path:
    return quarterly_tracking_path(QUARTERLY_TRACKING_OVERVIEW_NAME, vault_path=vault_path)


def load_quarterly_tracking_overview(vault_path: str | None = None) -> dict[str, object]:
    path = quarterly_tracking_overview_path(vault_path=vault_path)
    if not path.exists():
        return {
            "name": QUARTERLY_TRACKING_OVERVIEW_NAME,
            "file_path": str(path),
            "status": "待建设",
            "public": None,
            "sections": {},
            "raw_markdown": "",
        }

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {
            "name": QUARTERLY_TRACKING_OVERVIEW_NAME,
            "file_path": str(path),
            "status": "读取失败",
            "public": None,
            "sections": {},
            "raw_markdown": "",
        }

    metadata, body = split_frontmatter(raw)
    return {
        "name": str(metadata.get("title") or QUARTERLY_TRACKING_OVERVIEW_NAME),
        "file_path": str(path),
        "status": "已读取",
        "public": parse_bool(metadata.get("public")),
        "sections": extract_quarterly_tracking_sections(body),
        "raw_markdown": body.strip()[:1800],
    }


def load_ecosystem_quarterly_trackings(vault_path: str | None = None) -> list[dict[str, object]]:
    return [load_single_quarterly_tracking(name, vault_path=vault_path) for name in quarterly_tracking_ecosystem_names()]


def load_single_quarterly_tracking(ecosystem_name: str, vault_path: str | None = None) -> dict[str, object]:
    tracking_name = f"{ecosystem_name}季度跟踪表"
    path = quarterly_tracking_path(tracking_name, vault_path=vault_path)
    if not path.exists():
        return empty_quarterly_tracking(tracking_name, ecosystem_name, path, "待建设")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return empty_quarterly_tracking(tracking_name, ecosystem_name, path, "读取失败")

    metadata, body = split_frontmatter(raw)
    sections = extract_quarterly_tracking_sections(body)
    return {
        "name": str(metadata.get("title") or tracking_name),
        "ecosystem": str(metadata.get("ecosystem") or ecosystem_name),
        "file_path": str(path),
        "status": "已读取",
        "public": parse_bool(metadata.get("public")),
        "current_quarter": first_content_line(str(sections.get("当前季度") or "")),
        "core_conclusions": parse_markdown_table(str(sections.get("本季度核心结论") or "")),
        "key_indicators": parse_markdown_table(str(sections.get("关键指标跟踪") or "")),
        "company_changes": parse_markdown_table(str(sections.get("公司池变化") or "")),
        "project_changes": parse_markdown_table(str(sections.get("一级项目变化") or "")),
        "industry_chain_changes": extract_bullets(str(sections.get("产业链变化") or "")),
        "policy_changes": extract_bullets(str(sections.get("政策与监管变化") or "")),
        "technology_changes": extract_bullets(str(sections.get("技术变化") or "")),
        "risk_changes": parse_markdown_table(str(sections.get("风险变化") or "")),
        "research_task_review": parse_markdown_table(str(sections.get("研究任务复盘") or "")),
        "next_quarter_focus": extract_bullets(str(sections.get("下季度重点跟踪方向") or "")),
        "raw_markdown": body.strip()[:1800],
    }


def empty_quarterly_tracking(name: str, ecosystem_name: str, path: Path, status: str) -> dict[str, object]:
    return {
        "name": name,
        "ecosystem": ecosystem_name,
        "file_path": str(path),
        "status": status,
        "public": None,
        "current_quarter": "",
        "core_conclusions": [],
        "key_indicators": [],
        "company_changes": [],
        "project_changes": [],
        "industry_chain_changes": [],
        "policy_changes": [],
        "technology_changes": [],
        "risk_changes": [],
        "research_task_review": [],
        "next_quarter_focus": [],
        "raw_markdown": "",
    }


def extract_quarterly_tracking_sections(markdown_text: str) -> dict[str, str]:
    sections = extract_sections(markdown_text)
    normalized: dict[str, str] = {}
    for title, content in sections.items():
        normalized[strip_heading_number(title)] = content
    return normalized


def strip_heading_number(title: str) -> str:
    parts = title.split(maxsplit=1)
    if len(parts) == 2 and parts[0].rstrip(".、").replace(".", "").isdigit():
        return parts[1]
    return title


def extract_bullets(markdown_text: str) -> list[str]:
    values: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def first_content_line(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
