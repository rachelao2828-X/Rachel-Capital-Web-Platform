#!/usr/bin/env python3
"""Fetch public daily reports from origin/main and write them into Obsidian."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


DEFAULT_REPO = "/Users/rachelao/Documents/Rachel Capital Web Platform"
DEFAULT_VAULT = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_REF = "origin/main"
DEFAULT_SOURCE_PREFIX = "public_site/daily"
DEFAULT_TARGET_DIR = "31_Inbox/Daily_Intelligence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync public daily intelligence reports from GitHub into the local Obsidian vault."
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Local web platform repository path.")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help="Local Obsidian vault path.")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref to sync from.")
    parser.add_argument("--source-prefix", default=DEFAULT_SOURCE_PREFIX, help="Source prefix in the Git ref.")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help="Target directory in the Obsidian vault.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned writes without writing files.")
    return parser.parse_args()


def run_git(repo: Path, args: list[str], *, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=False,
    )


def list_daily_files(repo: Path, ref: str, source_prefix: str) -> list[str]:
    result = run_git(repo, ["ls-tree", "-r", "--name-only", ref, source_prefix])
    paths = result.stdout.decode("utf-8", errors="replace").splitlines()
    return sorted(path for path in paths if path.endswith(".md"))


def show_file(repo: Path, ref: str, path: str) -> bytes:
    return run_git(repo, ["show", f"{ref}:{path}"]).stdout


def sync_from_git_ref(
    repo: Path,
    vault: Path,
    ref: str,
    source_prefix: str,
    target_dir: str,
    dry_run: bool = False,
) -> list[Path]:
    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo}")
    if not vault.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault}")

    run_git(repo, ["fetch", "origin", "main"], capture=True)

    target_root = vault / target_dir
    written: list[Path] = []
    for source_path in list_daily_files(repo, ref, source_prefix):
        relative_path = Path(source_path).relative_to(source_prefix)
        target_path = target_root / relative_path
        written.append(target_path)
        if dry_run:
            print(f"DRY RUN write {ref}:{source_path} -> {target_path}")
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(show_file(repo, ref, source_path))
        print(f"Wrote {ref}:{source_path} -> {target_path}")

    return written


def main() -> int:
    args = parse_args()
    try:
        written = sync_from_git_ref(
            repo=Path(args.repo).expanduser(),
            vault=Path(args.vault).expanduser(),
            ref=args.ref,
            source_prefix=args.source_prefix,
            target_dir=args.target_dir,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"Daily intelligence sync failed: {exc}", file=sys.stderr)
        return 1

    print(f"Daily intelligence files synced: {len(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
