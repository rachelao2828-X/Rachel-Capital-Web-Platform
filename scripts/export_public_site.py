#!/usr/bin/env python3
"""Export public Obsidian notes into the static public research portal."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_OUTPUT_PATH = "public_site/data/public_content.json"
DEFAULT_ECOSYSTEMS_OUTPUT_PATH = "public_site/data/ecosystems.json"
PUBLIC_SITE_ROOT = Path("public_site")
EXCLUDED_DIRS = {".git", ".obsidian", ".trash", "__pycache__"}
PRIVATE_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "webhook",
    "password",
    "holding",
    "holdings",
    "position",
    "positions",
    "decision",
    "private",
    "internal_score",
    "valuation_model",
}
ALLOWED_FRONTMATTER_KEYS = {
    "id",
    "public",
    "publish_scope",
    "type",
    "title",
    "status",
    "created",
    "updated",
    "date",
    "summary",
    "ecosystem",
    "companies",
    "linked_companies",
    "tags",
    "source",
}

ECOSYSTEMS_SOURCE_DIR = "02_战略生态"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export public Obsidian notes for GitHub Pages.")
    parser.add_argument(
        "--vault",
        default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH),
        help="Absolute path to the Obsidian vault.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Output JSON path for the public site.",
    )
    parser.add_argument(
        "--ecosystems-output",
        default=DEFAULT_ECOSYSTEMS_OUTPUT_PATH,
        help="Output JSON path for public ecosystem data.",
    )
    return parser.parse_args()


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    stripped = text.lstrip()
    delimiter = None
    if stripped.startswith("---"):
        delimiter = "---"
    elif stripped.startswith("⸻"):
        delimiter = "⸻"
    if delimiter is None:
        return {}, text

    lines = stripped.splitlines()
    if not lines or lines[0].strip() != delimiter:
        return {}, text

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == delimiter:
            end_index = index
            break
    if end_index is None:
        return {}, text

    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).strip()
    return parse_frontmatter(frontmatter_text), body


def parse_frontmatter(frontmatter_text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        list_item = re.match(r"^\s*[-*]\s+(.+)$", line)
        if list_item and current_key:
            data.setdefault(current_key, []).append(clean_scalar(list_item.group(1)))
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        else:
            data[key] = clean_scalar(value)

    return data


def clean_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [clean_scalar(part.strip()) for part in inner.split(",")]
    return value


def is_public(frontmatter: dict[str, Any]) -> bool:
    value = frontmatter.get("public")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def public_metadata(frontmatter: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in frontmatter.items():
        normalized = key.lower()
        if normalized in PRIVATE_KEYS:
            continue
        if key in ALLOWED_FRONTMATTER_KEYS:
            sanitized[key] = value
    return sanitized


def excerpt(body: str, length: int = 220) -> str:
    compact = re.sub(r"\s+", " ", body).strip()
    if len(compact) <= length:
        return compact
    return compact[: length - 1].rstrip() + "..."


def section_map(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^##\s+(?:\d+\.\s*)?(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
            continue
        if current:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def strip_heading(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("## "):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def ecosystem_payload(body: str, metadata: dict[str, Any], path: Path, vault: Path) -> dict[str, Any]:
    sections = section_map(body)
    public_summary = strip_heading(sections.get("公开展示摘要", ""))
    next_research_tasks = strip_heading(sections.get("下一步研究任务", ""))
    linked_companies = as_list(metadata.get("linked_companies"))
    return {
        "public_summary": public_summary or metadata.get("summary") or excerpt(body),
        "summary": public_summary or metadata.get("summary") or excerpt(body),
        "next_research_tasks": next_research_tasks,
        "source_path": str(path.relative_to(vault)),
        "linked_companies": linked_companies,
        "company_count": len(linked_companies),
        "sections": {
            "ecosystem_definition": sections.get("生态定义", ""),
            "industry_chain": sections.get("产业链结构", ""),
            "value_chain": sections.get("核心价值链", ""),
            "company_pool": sections.get("关键公司观察池", ""),
            "tracking_indicators": sections.get("长期跟踪指标", ""),
            "key_questions": sections.get("关键问题", ""),
            "related_ecosystems": sections.get("与其他生态的关系", ""),
            "next_research_tasks": sections.get("下一步研究任务", ""),
        },
    }


def ecosystem_json_item(body: str, metadata: dict[str, Any], path: Path, vault: Path) -> dict[str, Any]:
    sections = section_map(body)
    summary = strip_heading(sections.get("公开展示摘要", "")) or metadata.get("summary") or excerpt(body)
    linked_companies = as_list(metadata.get("linked_companies"))
    return {
        "id": metadata.get("id") or "",
        "title": metadata.get("title") or path.stem,
        "tags": as_list(metadata.get("tags")),
        "linked_companies": linked_companies,
        "company_count": len(linked_companies),
        "publish_scope": metadata.get("publish_scope") or "",
        "summary": summary,
        "source_path": str(path.relative_to(vault)),
        "path": public_markdown_path("ecosystem", metadata, path).as_posix(),
        "sections": {
            "definition": sections.get("生态定义", ""),
            "industry_chain": sections.get("产业链结构", ""),
            "value_chain": sections.get("核心价值链", ""),
            "companies": sections.get("关键公司观察池", ""),
            "indicators": sections.get("长期跟踪指标", ""),
            "questions": sections.get("关键问题", ""),
            "relations": sections.get("与其他生态的关系", ""),
            "next_tasks": sections.get("下一步研究任务", ""),
        },
    }


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def public_markdown_path(item_type: str, metadata: dict[str, Any], source_path: Path) -> Path:
    if item_type == "daily_intelligence":
        date_value = str(metadata.get("date") or source_path.stem[:10])
        year = date_value[:4] if len(date_value) >= 4 else "undated"
        month = date_value[:7] if len(date_value) >= 7 else year
        filename = f"{date_value}_科技动向日报.md"
        return Path("daily") / year / month / filename

    slug = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "-", source_path.stem).strip("-") or "note"
    if item_type == "company":
        return Path("companies") / f"{slug}.md"
    if item_type == "ecosystem":
        return Path("ecosystems") / f"{slug}.md"
    if item_type in {"report", "knowledge_graph"}:
        return Path("reports") / f"{slug}.md"
    return Path("reports") / f"{slug}.md"


def iter_markdown_files(vault: Path):
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted([directory for directory in dirs if directory not in EXCLUDED_DIRS and not directory.startswith(".")])
        for filename in sorted(files):
            if filename.endswith(".md"):
                yield Path(root) / filename


def iter_public_ecosystem_files(vault: Path):
    ecosystem_dir = vault / ECOSYSTEMS_SOURCE_DIR
    if not ecosystem_dir.exists():
        return
    for path in sorted(ecosystem_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = split_frontmatter(text)
        if is_public(frontmatter):
            yield path, public_metadata(frontmatter), body


def export_public_content(vault: Path, site_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in iter_markdown_files(vault):
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = split_frontmatter(text)
        if not is_public(frontmatter):
            continue

        metadata = public_metadata(frontmatter)
        title = metadata.get("title") or path.stem
        item_type = metadata.get("type") or "note"
        relative_path = public_markdown_path(item_type, metadata, path)
        target_path = site_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target_path)

        item_payload: dict[str, Any] = {}
        if item_type == "ecosystem" and ECOSYSTEMS_SOURCE_DIR in path.relative_to(vault).parts:
            item_payload = ecosystem_payload(body=body, metadata=metadata, path=path, vault=vault)

        items.append(
            {
                **metadata,
                **item_payload,
                "title": title,
                "type": item_type,
                "path": relative_path.as_posix(),
                "excerpt": metadata.get("summary") or excerpt(body),
            }
        )

    return sorted(items, key=lambda item: (str(item.get("date") or ""), str(item.get("title") or "")), reverse=True)


def export_public_ecosystems(vault: Path, site_root: Path) -> list[dict[str, Any]]:
    ecosystems: list[dict[str, Any]] = []
    for path, metadata, body in iter_public_ecosystem_files(vault):
        if metadata.get("type") != "ecosystem":
            continue

        relative_path = public_markdown_path("ecosystem", metadata, path)
        target_path = site_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target_path)
        ecosystems.append(ecosystem_json_item(body=body, metadata=metadata, path=path, vault=vault))

    ecosystem_order = [
        "AI基础设施生态",
        "半导体生态",
        "华为生态",
        "机器人生态",
        "高端材料生态",
        "船舶与国防生态",
        "医疗科技生态",
    ]
    order = {title: index for index, title in enumerate(ecosystem_order)}
    return sorted(ecosystems, key=lambda item: order.get(str(item.get("title")), 999))


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser()
    output = Path(args.output)
    ecosystems_output = Path(args.ecosystems_output)
    site_root = PUBLIC_SITE_ROOT

    if not vault.exists() or not vault.is_dir():
        raise SystemExit(f"Obsidian vault path does not exist: {vault}")

    output.parent.mkdir(parents=True, exist_ok=True)
    ecosystems_output.parent.mkdir(parents=True, exist_ok=True)
    ecosystems = export_public_ecosystems(vault, site_root)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_vault": str(vault),
        "items": export_public_content(vault, site_root),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ecosystems_output.write_text(json.dumps(ecosystems, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(payload['items'])} public items to {output}")
    print(f"Exported {len(ecosystems)} public ecosystems to {ecosystems_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
