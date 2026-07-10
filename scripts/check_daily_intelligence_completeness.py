#!/usr/bin/env python3
"""Check Daily Intelligence source and public-site export completeness."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_SOURCE_DIR = "31_Inbox/Daily_Intelligence"
DEFAULT_PUBLIC_CONTENT = "public_site/data/public_content.json"
DAILY_FILENAME_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})_科技动向日报\.md$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when Daily Intelligence files are missing from source metadata or public export."
    )
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--public-content", default=DEFAULT_PUBLIC_CONTENT)
    parser.add_argument("--start-date", help="Check source weekdays and exports from YYYY-MM-DD.")
    parser.add_argument("--end-date", default=date.today().isoformat(), help="Check through YYYY-MM-DD.")
    parser.add_argument(
        "--skip-source-calendar",
        action="store_true",
        help="Only validate existing source files and exported items; do not require weekday source files.",
    )
    return parser.parse_args()


def split_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in lines[1:end_index]:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        list_item = re.match(r"^\s*[-*]\s+(.+)$", line)
        if list_item and current_key:
            data.setdefault(current_key, []).append(list_item.group(1).strip().strip('"').strip("'"))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        current_key = key
        if value.lower() == "true":
            data[key] = True
        elif value.lower() == "false":
            data[key] = False
        elif value == "":
            data[key] = []
        else:
            data[key] = value
    return data


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def daily_path(source_root: Path, item_date: date) -> Path:
    value = item_date.isoformat()
    return source_root / value[:4] / value[:7] / f"{value}_科技动向日报.md"


def source_files(source_root: Path, start: date, end: date) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not source_root.exists():
        return found
    for path in sorted(source_root.rglob("*_科技动向日报.md")):
        match = DAILY_FILENAME_RE.match(path.name)
        if not match:
            continue
        item_date = date.fromisoformat(match.group("date"))
        if start <= item_date <= end:
            found[item_date.isoformat()] = path
    return found


def public_items(public_content: Path) -> tuple[dict[str, dict[str, Any]], set[str]]:
    payload = json.loads(public_content.read_text(encoding="utf-8"))
    by_date: dict[str, dict[str, Any]] = {}
    paths: set[str] = set()
    for item in payload.get("items", []):
        if item.get("type") != "daily_intelligence":
            continue
        item_date = str(item.get("date") or "")
        if item_date:
            by_date[item_date] = item
        if item.get("path"):
            paths.add(str(item["path"]))
    return by_date, paths


def main() -> int:
    args = parse_args()
    end = date.fromisoformat(args.end_date)
    start = date.fromisoformat(args.start_date) if args.start_date else end.replace(day=1)
    vault = Path(args.vault).expanduser()
    source_root = vault / args.source_dir
    public_content = Path(args.public_content)
    site_root = public_content.parent.parent

    issues: list[str] = []
    sources = source_files(source_root, start, end)

    if not args.skip_source_calendar:
        for item_date in iter_dates(start, end):
            if item_date.weekday() >= 5:
                continue
            value = item_date.isoformat()
            if value not in sources:
                issues.append(f"missing source weekday report: {daily_path(source_root, item_date)}")

    for item_date, path in sources.items():
        metadata = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        if metadata.get("public") is not True:
            issues.append(f"missing public: true in source: {path}")
        if metadata.get("type") != "daily_intelligence":
            issues.append(f"missing type: daily_intelligence in source: {path}")
        if str(metadata.get("date") or "") != item_date:
            issues.append(f"source date does not match filename: {path}")

    if not public_content.exists():
        issues.append(f"missing public content index: {public_content}")
    else:
        public_by_date, public_paths = public_items(public_content)
        for item_date in sorted(sources):
            source = sources[item_date]
            metadata = split_frontmatter(source.read_text(encoding="utf-8", errors="replace"))
            if metadata.get("public") is not True:
                continue
            if metadata.get("type") != "daily_intelligence":
                continue
            expected_path = f"daily/{item_date[:4]}/{item_date[:7]}/{item_date}_科技动向日报.md"
            if item_date not in public_by_date:
                issues.append(f"missing daily item in public_content.json: {item_date}")
            if expected_path not in public_paths:
                issues.append(f"missing daily path in public_content.json: {expected_path}")
            if not (site_root / expected_path).exists():
                issues.append(f"missing exported markdown file: {site_root / expected_path}")

    if issues:
        print("Daily Intelligence completeness check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Daily Intelligence completeness check passed for {start.isoformat()} through {end.isoformat()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
