# Local Obsidian Daily Intelligence Backfill Guide

## Purpose

This guide documents the local repair workflow for missing Obsidian daily reports.

It is not the standard publishing flow.

The standard publishing flow is:

```text
Coze -> Obsidian Daily_Intelligence -> export_public_site.py -> public_site -> GitHub Pages
```

The local backfill workflow is allowed only when a report was already published to GitHub Pages but is missing from Obsidian.

## Obsidian Target

Daily reports must be present at:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

## Repair Script

The script is:

```text
scripts/sync_github_daily_to_obsidian.py
```

It reads Markdown files from:

```text
origin/main:public_site/daily
```

Then writes them into the local Obsidian vault.

Manual repair:

```bash
python3 scripts/sync_github_daily_to_obsidian.py
```

Dry run:

```bash
python3 scripts/sync_github_daily_to_obsidian.py --dry-run
```

## Important Constraint

Do not use this script as the normal Coze publishing route.

If this script is needed, it means the standard flow was bypassed:

```text
Coze -> Obsidian -> public_site -> GitHub Pages
```

After repair, future daily reports should again be created in Obsidian first.

## Verification

Check local Obsidian reports:

```bash
find "/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence" -name "*科技动向日报.md"
```

Check required frontmatter:

```bash
rg -n "^public: true|^type: daily_intelligence|^date:|^source: coze" "/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence"
```

## 2026-07-02 Backfill

The following files were manually backfilled from GitHub Pages into Obsidian:

```text
2026-07-01_科技动向日报.md
2026-07-02_科技动向日报.md
```

This correction should not be repeated as the normal publishing route.
