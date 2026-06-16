from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.models.news import NewsItem


@dataclass
class SyncResult:
    status: str
    path: str | None = None
    detail: str | None = None


def _format_list(values: list[str] | None) -> str:
    values = values or []
    if not values:
        return "无"
    return "、".join(values)


def _format_markdown_list(values: list[str] | None) -> str:
    values = values or []
    if not values:
        return "无"
    return "\n".join(f"- {value}" for value in values)


def _collect_companies(news_item: NewsItem) -> list[str]:
    companies = list(news_item.companies or [])
    for event in news_item.events or []:
        for company in event.companies or []:
            if company not in companies:
                companies.append(company)
    return companies


def _collect_tags(news_item: NewsItem) -> list[str]:
    tags = list(news_item.tags or [])
    for event in news_item.events or []:
        for tag in event.tags or []:
            if tag not in tags:
                tags.append(tag)
    return tags


def _event_markdown(news_item: NewsItem) -> str:
    lines: list[str] = []
    for event in news_item.events or []:
        lines.extend(
            [
                event.title,
                "",
                "生态：",
                event.ecosystem or "综合",
                "",
                "公司：",
                _format_list(event.companies),
                "",
                "重要性：",
                event.importance,
                "",
                "摘要：",
                event.summary,
                "",
                "影响：",
                event.impact or "暂无",
                "",
            ]
        )
    if not lines:
        lines.extend(
            [
                news_item.title,
                "",
                "生态：",
                news_item.ecosystem or "综合",
                "",
                "公司：",
                _format_list(news_item.companies),
                "",
                "重要性：",
                news_item.importance,
                "",
                "摘要：",
                news_item.summary,
                "",
                "影响：",
                "暂无",
                "",
            ]
        )
    return "\n".join(lines).strip()


def render_daily_report_markdown(news_item: NewsItem) -> str:
    report_date = news_item.date.isoformat()
    companies = _collect_companies(news_item)
    tags = _collect_tags(news_item)

    return f"""⸻

type: daily_intelligence
source: platform
date: {report_date}
tags:

* 科技投资
* AI

⸻

{report_date} 科技投资日报

摘要

{news_item.summary}

重点事件

{_event_markdown(news_item)}

关联公司

{_format_list(companies)}

标签

{_format_markdown_list(tags)}
"""


def write_daily_report_to_obsidian(
    news_item: NewsItem,
    vault_path: str | None = None,
    daily_report_dir: str | None = None,
) -> SyncResult:
    configured_vault_path = vault_path if vault_path is not None else settings.obsidian_vault_path
    if not configured_vault_path:
        return SyncResult(status="skipped_not_configured", detail="OBSIDIAN_VAULT_PATH is not configured.")

    vault = Path(configured_vault_path).expanduser()
    vault.mkdir(parents=True, exist_ok=True)
    if not vault.is_dir():
        return SyncResult(status="failed", detail=f"Obsidian vault path is not a directory: {vault}")

    target_dir = vault / (daily_report_dir or settings.daily_report_obsidian_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{news_item.date.isoformat()}_科技投资日报.md"
    target_file = target_dir / filename
    target_file.write_text(render_daily_report_markdown(news_item), encoding="utf-8")
    return SyncResult(status="success", path=str(target_file))
