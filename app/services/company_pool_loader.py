from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.services.ecosystem_loader import extract_sections, parse_bool, parse_markdown_table, split_frontmatter
from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS


COMPANY_POOL_SOURCE_DIR = Path("03_公司数据库") / "战略生态公司池"
COMPANY_POOL_OVERVIEW_NAME = "七大战略生态公司池总览"


def company_pool_ecosystem_names() -> list[str]:
    return [name for name in ECOSYSTEM_OPTIONS if name not in {"中国关键技术攻关长期跟踪", "其他"}]


def company_pool_root(vault_path: str | None = None) -> Path:
    vault = Path(vault_path or settings.obsidian_vault_path or "")
    return vault / COMPANY_POOL_SOURCE_DIR


def company_pool_path(pool_name: str, vault_path: str | None = None) -> Path:
    return company_pool_root(vault_path=vault_path) / f"{pool_name}.md"


def company_pool_overview_path(vault_path: str | None = None) -> Path:
    return company_pool_path(COMPANY_POOL_OVERVIEW_NAME, vault_path=vault_path)


def load_company_pool_overview(vault_path: str | None = None) -> dict[str, object]:
    path = company_pool_overview_path(vault_path=vault_path)
    if not path.exists():
        return {
            "name": COMPANY_POOL_OVERVIEW_NAME,
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
            "name": COMPANY_POOL_OVERVIEW_NAME,
            "file_path": str(path),
            "status": "读取失败",
            "public": None,
            "sections": {},
            "raw_markdown": "",
        }

    metadata, body = split_frontmatter(raw)
    return {
        "name": str(metadata.get("title") or COMPANY_POOL_OVERVIEW_NAME),
        "file_path": str(path),
        "status": "已读取",
        "public": parse_bool(metadata.get("public")),
        "sections": extract_company_pool_sections(body),
        "raw_markdown": body.strip()[:1800],
    }


def load_ecosystem_company_pools(vault_path: str | None = None) -> list[dict[str, object]]:
    return [load_single_company_pool(name, vault_path=vault_path) for name in company_pool_ecosystem_names()]


def load_single_company_pool(ecosystem_name: str, vault_path: str | None = None) -> dict[str, object]:
    pool_name = f"{ecosystem_name}公司池"
    path = company_pool_path(pool_name, vault_path=vault_path)
    if not path.exists():
        return empty_company_pool(pool_name, ecosystem_name, path, "待建设")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return empty_company_pool(pool_name, ecosystem_name, path, "读取失败")

    metadata, body = split_frontmatter(raw)
    sections = extract_company_pool_sections(body)
    table_markdown = str(sections.get("公司池表格") or "")
    return {
        "name": str(metadata.get("title") or pool_name),
        "ecosystem": str(metadata.get("ecosystem") or ecosystem_name),
        "file_path": str(path),
        "status": "已读取",
        "public": parse_bool(metadata.get("public")),
        "companies": normalize_company_rows(parse_markdown_table(table_markdown)),
        "segments": extract_bullets(str(sections.get("细分环节分类") or "")),
        "priority_targets": extract_bullets(str(sections.get("高优先级跟踪对象") or "")),
        "to_fill": extract_bullets(str(sections.get("待补充清单") or "")),
        "cross_links": extract_wikilinks(str(sections.get("与其他生态交叉") or "")),
        "tasks": extract_bullets(str(sections.get("后续研究任务") or "")),
        "raw_markdown": body.strip()[:1800],
    }


def empty_company_pool(pool_name: str, ecosystem_name: str, path: Path, status: str) -> dict[str, object]:
    return {
        "name": pool_name,
        "ecosystem": ecosystem_name,
        "file_path": str(path),
        "status": status,
        "public": None,
        "companies": [],
        "segments": [],
        "priority_targets": [],
        "to_fill": [],
        "cross_links": [],
        "tasks": [],
        "raw_markdown": "",
    }


def extract_company_pool_sections(markdown_text: str) -> dict[str, str]:
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


def normalize_company_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        normalized_rows.append(
            {
                "name": row.get("公司 / 项目", ""),
                "market_type": row.get("市场类型", ""),
                "ticker_or_id": row.get("代码 / 编号", ""),
                "segment": row.get("细分环节", ""),
                "core_business": row.get("核心业务", ""),
                "ecosystem_relevance": row.get("生态相关性", ""),
                "research_priority": row.get("研究优先级", ""),
                "research_status": row.get("当前研究状态", ""),
                "linked_file": row.get("关联文件", ""),
                "notes": row.get("备注", ""),
            }
        )
    return normalized_rows


def extract_bullets(markdown_text: str) -> list[str]:
    values: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def extract_wikilinks(markdown_text: str) -> list[str]:
    links: list[str] = []
    for part in markdown_text.split("[["):
        if "]]" not in part:
            continue
        links.append(part.split("]]", 1)[0].strip())
    return links
