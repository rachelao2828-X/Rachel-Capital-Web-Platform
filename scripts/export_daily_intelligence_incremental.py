#!/usr/bin/env python3
"""Incrementally export one Daily Intelligence note without rebuilding the site."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from export_public_site import (
    excerpt,
    is_public,
    public_markdown_path,
    public_metadata,
    sanitize_public_text,
    sanitize_public_value,
    split_frontmatter,
)


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_SITE_ROOT = "public_site"
DAILY_SOURCE_DIR = Path("31_Inbox/Daily_Intelligence")
DAILY_TYPE = "daily_intelligence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incrementally export one Daily Intelligence report.")
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--site-root", default=DEFAULT_SITE_ROOT)
    parser.add_argument("--report-date", required=True, help="Report date in YYYY-MM-DD format.")
    return parser.parse_args()


def source_path(vault: Path, report_date: str) -> Path:
    return (
        vault
        / DAILY_SOURCE_DIR
        / report_date[:4]
        / report_date[:7]
        / f"{report_date}_科技动向日报.md"
    )


def load_public_payload(site_root: Path) -> dict[str, Any]:
    path = site_root / "data/public_content.json"
    if not path.exists():
        return {"items": []}
    return json.loads(path.read_text(encoding="utf-8"))


def export_daily_note(source: Path, site_root: Path, report_date: str) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    if not is_public(frontmatter):
        raise SystemExit(f"Daily Intelligence report is not public: {source}")

    metadata = public_metadata(frontmatter)
    if metadata.get("type") != DAILY_TYPE:
        raise SystemExit(f"Daily Intelligence report has invalid type: {source}")
    if str(metadata.get("date") or "") != report_date:
        raise SystemExit(f"Daily Intelligence report date does not match filename: {source}")

    relative_path = public_markdown_path(DAILY_TYPE, metadata, source)
    target_path = site_root / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(sanitize_public_text(text), encoding="utf-8")
    return {
        **metadata,
        "title": metadata.get("title") or source.stem,
        "type": DAILY_TYPE,
        "path": relative_path.as_posix(),
        "excerpt": metadata.get("summary") or excerpt(body),
    }


def main() -> int:
    args = parse_args()
    report_date = str(args.report_date).strip()
    date.fromisoformat(report_date)

    vault = Path(args.vault).expanduser()
    site_root = Path(args.site_root)
    source = source_path(vault, report_date)
    if not source.exists():
        raise SystemExit(f"Daily Intelligence report does not exist: {source}")

    payload = load_public_payload(site_root)
    daily_item = export_daily_note(source, site_root, report_date)
    existing_items = [
        item
        for item in payload.get("items", [])
        if not (item.get("type") == DAILY_TYPE and str(item.get("date") or "") == report_date)
    ]
    payload = sanitize_public_value(
        {
            **payload,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_vault": str(vault),
            "items": sorted(
                [*existing_items, daily_item],
                key=lambda item: (str(item.get("date") or ""), str(item.get("title") or "")),
                reverse=True,
            ),
        }
    )
    output = site_root / "data/public_content.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Incrementally exported Daily Intelligence {report_date} into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
