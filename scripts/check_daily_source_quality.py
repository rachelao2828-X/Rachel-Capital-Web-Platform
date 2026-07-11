#!/usr/bin/env python3
"""Reject incomplete Daily Intelligence source notes before export or Vault commit."""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import re

from export_public_site import is_public, split_frontmatter


DEFAULT_VAULT_PATH = "/Users/rachelao/Documents/Rachel Capital"
DAILY_SOURCE_DIR = Path("31_Inbox/Daily_Intelligence")
MIN_BODY_CHARACTERS = 1000
MIN_SECTION_HEADINGS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one Daily Intelligence source report.")
    parser.add_argument("--vault", default=os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))
    parser.add_argument("--report-date", required=True, help="Report date in YYYY-MM-DD format.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_date = str(args.report_date).strip()
    date.fromisoformat(report_date)
    path = (
        Path(args.vault).expanduser()
        / DAILY_SOURCE_DIR
        / report_date[:4]
        / report_date[:7]
        / f"{report_date}_科技动向日报.md"
    )
    if not path.exists():
        raise SystemExit(f"Daily Intelligence source is missing: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    compact_body = re.sub(r"\s+", "", body)
    section_count = len(re.findall(r"^##\s+", body, flags=re.MULTILINE))

    issues: list[str] = []
    if not is_public(frontmatter):
        issues.append("frontmatter must contain public: true")
    if frontmatter.get("type") != "daily_intelligence":
        issues.append("frontmatter type must be daily_intelligence")
    if str(frontmatter.get("date") or "") != report_date:
        issues.append("frontmatter date must match the report date")
    if len(compact_body) < MIN_BODY_CHARACTERS:
        issues.append(
            f"body is incomplete ({len(compact_body)} characters; minimum {MIN_BODY_CHARACTERS})"
        )
    if section_count < MIN_SECTION_HEADINGS:
        issues.append(
            f"body has too few sections ({section_count}; minimum {MIN_SECTION_HEADINGS})"
        )

    if issues:
        print(f"Daily Intelligence source quality check failed: {path}")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(
        f"Daily Intelligence source quality passed for {report_date}: "
        f"{len(compact_body)} characters, {section_count} sections."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
