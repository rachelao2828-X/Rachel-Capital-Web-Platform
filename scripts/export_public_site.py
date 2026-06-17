#!/usr/bin/env python3
"""Export public Obsidian notes into the static public research portal."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DEFAULT_OUTPUT_PATH = "public_site/data/public_content.json"
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
    "public",
    "type",
    "title",
    "date",
    "summary",
    "ecosystem",
    "companies",
    "tags",
    "source",
}


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


def iter_markdown_files(vault: Path):
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted([directory for directory in dirs if directory not in EXCLUDED_DIRS and not directory.startswith(".")])
        for filename in sorted(files):
            if filename.endswith(".md"):
                yield Path(root) / filename


def export_public_content(vault: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in iter_markdown_files(vault):
        text = path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = split_frontmatter(text)
        if not is_public(frontmatter):
            continue

        metadata = public_metadata(frontmatter)
        title = metadata.get("title") or path.stem
        item_type = metadata.get("type") or "note"
        relative_path = path.relative_to(vault).as_posix()
        items.append(
            {
                **metadata,
                "title": title,
                "type": item_type,
                "path": relative_path,
                "excerpt": metadata.get("summary") or excerpt(body),
                "body": body,
            }
        )

    return sorted(items, key=lambda item: (str(item.get("date") or ""), str(item.get("title") or "")), reverse=True)


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser()
    output = Path(args.output)

    if not vault.exists() or not vault.is_dir():
        raise SystemExit(f"Obsidian vault path does not exist: {vault}")

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_vault": str(vault),
        "items": export_public_content(vault),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(payload['items'])} public items to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
