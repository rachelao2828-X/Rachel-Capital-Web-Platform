#!/usr/bin/env python3
"""Incrementally export Market Radar notes without rebuilding the whole site."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from export_public_site import (
    excerpt,
    is_public,
    public_markdown_path,
    public_metadata,
    safe_slug,
    sanitize_public_text,
    sanitize_public_value,
    split_frontmatter,
)


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_SITE_ROOT = "public_site"
MARKET_RADAR_SOURCE_DIR = Path("31_Inbox/Market_Radar")
MARKET_RADAR_TYPES = {"market_radar", "market_review", "review_report"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incrementally export Market Radar reports.")
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--site-root", default=DEFAULT_SITE_ROOT)
    return parser.parse_args()


def iter_market_radar_files(vault: Path):
    source_dir = vault / MARKET_RADAR_SOURCE_DIR
    if not source_dir.exists():
        return
    for path in sorted(source_dir.glob("**/*.md")):
        yield path


def load_public_payload(site_root: Path) -> dict[str, Any]:
    path = site_root / "data/public_content.json"
    if not path.exists():
        return {"items": []}
    return json.loads(path.read_text(encoding="utf-8"))


def export_market_radar(vault: Path, site_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in iter_market_radar_files(vault) or []:
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = split_frontmatter(text)
        if not is_public(frontmatter):
            continue

        metadata = public_metadata(frontmatter)
        item_type = str(metadata.get("type") or "market_radar")
        if item_type not in MARKET_RADAR_TYPES:
            continue
        if not metadata.get("slug"):
            metadata["slug"] = safe_slug(path.stem)

        title = metadata.get("title") or path.stem
        relative_path = public_markdown_path(item_type, metadata, path)
        target_path = site_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(sanitize_public_text(text), encoding="utf-8")
        items.append(
            {
                **metadata,
                "title": title,
                "type": item_type,
                "path": relative_path.as_posix(),
                "excerpt": metadata.get("summary") or excerpt(body),
            }
        )
    return items


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser()
    site_root = Path(args.site_root)
    if not vault.exists() or not vault.is_dir():
        raise SystemExit(f"Obsidian vault path does not exist: {vault}")

    payload = load_public_payload(site_root)
    existing_items = [item for item in payload.get("items", []) if item.get("type") not in MARKET_RADAR_TYPES]
    market_radar_items = export_market_radar(vault, site_root)
    payload = sanitize_public_value(
        {
            **payload,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_vault": str(vault),
            "items": sorted(
                [*existing_items, *market_radar_items],
                key=lambda item: (str(item.get("date") or ""), str(item.get("title") or "")),
                reverse=True,
            ),
        }
    )
    output = site_root / "data/public_content.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(market_radar_items)} market radar items into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
