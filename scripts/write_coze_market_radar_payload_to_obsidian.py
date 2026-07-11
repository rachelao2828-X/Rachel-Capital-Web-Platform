#!/usr/bin/env python3
"""Write a Coze Market Radar repository_dispatch payload into Obsidian."""

from __future__ import annotations

import argparse
import base64
from datetime import date
import json
import os
from pathlib import Path
import re
from typing import Any


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_TARGET_DIR = "31_Inbox/Market_Radar"
MIN_BODY_CHARACTERS = 800
MARKDOWN_FIELDS = (
    "markdown",
    "content",
    "body",
    "report_markdown",
    "report_content",
    "full_content",
    "full_report",
    "report",
    "text",
    "output",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write Coze repository_dispatch Market Radar payload to the Obsidian vault."
    )
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--target-dir", default=os.getenv("MARKET_RADAR_OBSIDIAN_DIR", DEFAULT_TARGET_DIR))
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH"))
    return parser.parse_args()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in re.split(r"[,，、\n]", value) if part.strip()]
        return parts or [value.strip()]
    return [str(value).strip()]


def frontmatter_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n".join(f"  - {value}" for value in values)


def strip_frontmatter(markdown: str) -> str:
    text = markdown.lstrip()
    if not text.startswith("---"):
        return markdown.strip()
    lines = text.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return markdown.strip()


def compact_summary(text: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def safe_slug(value: str, fallback: str = "market-radar-review") -> str:
    slug = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "-", value).strip("-")
    return slug or fallback


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def payload_markdown(payload: dict[str, Any], report_date: str) -> str:
    raw = ""
    if payload.get("markdown_base64"):
        raw = base64.b64decode(str(payload["markdown_base64"])).decode("utf-8", errors="replace")
    else:
        raw = str(next((payload.get(field) for field in MARKDOWN_FIELDS if payload.get(field)), ""))

    body = strip_frontmatter(raw)
    title = str(payload.get("title") or f"{report_date} 市场雷达复盘报告")
    if not body:
        summary = str(payload.get("summary") or "暂无")
        body = "\n\n".join(
            [
                f"# {title}",
                "## 复盘摘要\n\n" + summary,
                "## 市场观察\n\n暂无",
            ]
        )
    elif not body.lstrip().startswith("#"):
        body = f"# {title}\n\n{body.strip()}"
    compact_body = re.sub(r"\s+", "", body)
    if len(compact_body) < MIN_BODY_CHARACTERS:
        raise SystemExit(
            "Coze payload does not contain a complete Market Radar report body "
            f"({len(compact_body)} characters; minimum {MIN_BODY_CHARACTERS}). "
            "Send the full report in markdown, markdown_base64, content, body, "
            "report_markdown, report_content, or full_report."
        )
    return body.strip() + "\n"


def render_markdown(payload: dict[str, Any], report_date: str) -> str:
    body = payload_markdown(payload, report_date)
    title = str(payload.get("title") or f"{report_date} 市场雷达复盘报告")
    summary = str(payload.get("summary") or compact_summary(body))
    markets = as_list(payload.get("markets") or payload.get("market")) or ["综合"]
    ecosystem = as_list(payload.get("ecosystem") or payload.get("ecosystems"))
    companies = as_list(payload.get("companies"))
    tags = as_list(payload.get("tags")) or ["市场雷达", "复盘报告"]
    source = str(payload.get("source") or "coze")
    review_type = str(payload.get("review_type") or payload.get("report_kind") or "复盘报告")
    slug = safe_slug(str(payload.get("slug") or f"{report_date}_{title}"))

    return f"""---
public: true
type: market_radar
title: {yaml_scalar(title)}
date: {report_date}
slug: {yaml_scalar(slug)}
summary: {yaml_scalar(summary)}
source: {yaml_scalar(source)}
review_type: {yaml_scalar(review_type)}
markets:
{frontmatter_list(markets)}
ecosystem:
{frontmatter_list(ecosystem)}
companies:
{frontmatter_list(companies)}
tags:
{frontmatter_list(tags)}
---

{body}"""


def read_payload(event_path: str | None) -> dict[str, Any]:
    if not event_path:
        raise SystemExit("GITHUB_EVENT_PATH is not configured.")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    payload = event.get("client_payload") or {}
    if not isinstance(payload, dict):
        raise SystemExit("repository_dispatch client_payload must be an object.")
    return payload


def main() -> int:
    args = parse_args()
    payload = read_payload(args.event_path)
    report_date = str(payload.get("date") or "").strip()
    if not report_date:
        raise SystemExit("Coze payload missing required field: date")
    date.fromisoformat(report_date)

    title = str(payload.get("title") or f"{report_date} 市场雷达复盘报告")
    filename_slug = safe_slug(str(payload.get("slug") or title), "市场雷达复盘报告")
    vault = Path(args.vault).expanduser()
    target = (
        vault
        / args.target_dir
        / report_date[:4]
        / report_date[:7]
        / f"{report_date}_{filename_slug}.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(payload, report_date), encoding="utf-8")
    print(f"Wrote Coze Market Radar payload to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
