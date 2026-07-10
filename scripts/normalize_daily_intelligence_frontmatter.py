#!/usr/bin/env python3
"""Normalize Daily Intelligence Markdown frontmatter for public export."""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import re


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_SOURCE_DIR = "31_Inbox/Daily_Intelligence"
DAILY_FILENAME_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})_科技动向日报\.md$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure Daily Intelligence files have the public export frontmatter required by GitHub Pages."
    )
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--start-date", help="Only normalize files on or after YYYY-MM-DD.")
    parser.add_argument("--end-date", help="Only normalize files on or before YYYY-MM-DD.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing files.")
    return parser.parse_args()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def daily_date(path: Path) -> str | None:
    match = DAILY_FILENAME_RE.match(path.name)
    if not match:
        return None
    return match.group("date")


def iter_daily_files(root: Path, start: date | None, end: date | None):
    if not root.exists():
        return
    for path in sorted(root.rglob("*_科技动向日报.md")):
        value = daily_date(path)
        if not value:
            continue
        item_date = date.fromisoformat(value)
        if start and item_date < start:
            continue
        if end and item_date > end:
            continue
        yield path, value


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :])
    return [], text


def line_key(line: str) -> str | None:
    if ":" not in line or line.lstrip().startswith(("-", "#")):
        return None
    return line.split(":", 1)[0].strip()


def upsert_scalar(lines: list[str], key: str, value: str) -> bool:
    for index, line in enumerate(lines):
        if line_key(line) == key:
            if line.strip() == f"{key}: {value}":
                return False
            lines[index] = f"{key}: {value}"
            return True
    lines.append(f"{key}: {value}")
    return True


def normalize_file(path: Path, item_date: str, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    changed = False

    if not frontmatter:
        body = text
        frontmatter = []
        changed = True

    changed = upsert_scalar(frontmatter, "public", "true") or changed
    changed = upsert_scalar(frontmatter, "type", "daily_intelligence") or changed
    changed = upsert_scalar(frontmatter, "title", f"{item_date} 科技动向日报") or changed
    changed = upsert_scalar(frontmatter, "date", item_date) or changed
    changed = upsert_scalar(frontmatter, "source", "coze") or changed

    if not changed:
        return False

    normalized = "---\n" + "\n".join(frontmatter).rstrip() + "\n---\n\n" + body.lstrip()
    if dry_run:
        print(f"DRY RUN normalize {path}")
    else:
        path.write_text(normalized, encoding="utf-8")
        print(f"Normalized {path}")
    return True


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser()
    source_root = vault / args.source_dir
    if not source_root.exists():
        raise SystemExit(f"Daily Intelligence source directory does not exist: {source_root}")

    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    changed = 0
    scanned = 0
    for path, item_date in iter_daily_files(source_root, start, end):
        scanned += 1
        if normalize_file(path, item_date, args.dry_run):
            changed += 1

    print(f"Daily Intelligence files scanned: {scanned}")
    print(f"Daily Intelligence files changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
