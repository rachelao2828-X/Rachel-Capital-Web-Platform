#!/usr/bin/env python3
"""Sync public daily Markdown files into the local Obsidian vault inbox."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil


DEFAULT_SOURCE = "public_site/daily"
DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_TARGET_DIR = "31_Inbox/Daily_Intelligence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy public daily intelligence Markdown files into the Obsidian vault inbox."
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Source daily directory inside the web platform project.",
    )
    parser.add_argument(
        "--vault",
        default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH),
        help="Absolute path to the local Obsidian vault.",
    )
    parser.add_argument(
        "--target-dir",
        default=os.getenv("DAILY_REPORT_OBSIDIAN_DIR", DEFAULT_TARGET_DIR),
        help="Target directory inside the Obsidian vault.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned copies without writing files.",
    )
    return parser.parse_args()


def iter_daily_markdown(source: Path):
    if not source.exists():
        return
    for path in sorted(source.rglob("*.md")):
        if path.name.startswith("."):
            continue
        yield path


def sync_daily_files(source: Path, vault: Path, target_dir: str, dry_run: bool = False) -> list[Path]:
    if not source.exists():
        raise FileNotFoundError(f"Source daily directory does not exist: {source}")
    if not vault.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault}")

    target_root = vault / target_dir
    copied: list[Path] = []

    for source_path in iter_daily_markdown(source):
        relative_path = source_path.relative_to(source)
        target_path = target_root / relative_path
        copied.append(target_path)
        if dry_run:
            print(f"DRY RUN copy {source_path} -> {target_path}")
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        print(f"Copied {source_path} -> {target_path}")

    return copied


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser()
    vault = Path(args.vault).expanduser()

    copied = sync_daily_files(
        source=source,
        vault=vault,
        target_dir=args.target_dir,
        dry_run=args.dry_run,
    )
    print(f"Daily files synced: {len(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
