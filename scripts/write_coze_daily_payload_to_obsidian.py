#!/usr/bin/env python3
"""Write a Coze Daily Intelligence repository_dispatch payload into Obsidian."""

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
DEFAULT_TARGET_DIR = "31_Inbox/Daily_Intelligence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write Coze repository_dispatch Daily Intelligence payload to the Obsidian vault."
    )
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--target-dir", default=os.getenv("DAILY_REPORT_OBSIDIAN_DIR", DEFAULT_TARGET_DIR))
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


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def event_markdown(events: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, event in enumerate(events, start=1):
        title = str(event.get("title") or f"事件 {index}")
        summary = str(event.get("summary") or "")
        ecosystem = str(event.get("ecosystem") or "综合")
        companies = as_list(event.get("companies"))
        impact = str(event.get("impact") or "")
        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- 生态：{ecosystem}",
                f"- 公司：{'、'.join(companies) if companies else '无'}",
                f"- 摘要：{summary or '暂无'}",
                f"- 影响：{impact or '暂无'}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def payload_markdown(payload: dict[str, Any], report_date: str) -> str:
    raw = ""
    if payload.get("markdown_base64"):
        raw = base64.b64decode(str(payload["markdown_base64"])).decode("utf-8", errors="replace")
    else:
        raw = str(payload.get("markdown") or payload.get("content") or payload.get("body") or "")

    body = strip_frontmatter(raw)
    if not body:
        events = payload.get("events") if isinstance(payload.get("events"), list) else []
        summary = str(payload.get("summary") or "")
        body = "\n\n".join(
            part
            for part in [
                f"# {report_date} 科技动向日报",
                "## 摘要\n\n" + (summary or "暂无"),
                "## 重点事件\n\n" + (event_markdown(events) or "暂无"),
            ]
            if part
        )
    elif not body.lstrip().startswith("#"):
        body = f"# {report_date} 科技动向日报\n\n{body.strip()}"
    return body.strip() + "\n"


def render_markdown(payload: dict[str, Any], report_date: str) -> str:
    body = payload_markdown(payload, report_date)
    title = str(payload.get("title") or f"{report_date} 科技动向日报")
    summary = str(payload.get("summary") or compact_summary(body))
    ecosystem = as_list(payload.get("ecosystem") or payload.get("ecosystems")) or ["综合"]
    companies = as_list(payload.get("companies"))
    tags = as_list(payload.get("tags")) or ["科技动向"]
    source = str(payload.get("source") or "coze")

    return f"""---
public: true
type: daily_intelligence
title: {yaml_scalar(title)}
date: {report_date}
summary: {yaml_scalar(summary)}
source: {yaml_scalar(source)}
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

    vault = Path(args.vault).expanduser()
    target = (
        vault
        / args.target_dir
        / report_date[:4]
        / report_date[:7]
        / f"{report_date}_科技动向日报.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(payload, report_date), encoding="utf-8")
    print(f"Wrote Coze Daily Intelligence payload to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
