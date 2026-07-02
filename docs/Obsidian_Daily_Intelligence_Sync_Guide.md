# Obsidian Daily Intelligence Sync Guide

## Current Rule

Obsidian is the source of truth for daily intelligence reports.

The standard pipeline is:

```text
Coze daily report
-> Obsidian Daily_Intelligence Markdown
-> scripts/export_public_site.py
-> public_site
-> GitHub Pages
```

The reverse path below is not the primary publishing flow:

```text
GitHub Pages -> Obsidian
```

Use it only to repair missing Obsidian source files when a daily report was already published publicly.

## Obsidian Target

Daily reports must live under:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

## Required Frontmatter

Each daily report must include:

```yaml
---
public: true
type: daily_intelligence
title: YYYY-MM-DD 科技动向日报
date: YYYY-MM-DD
summary: 一句话公开摘要
source: coze
ecosystem:
  - AI基础设施生态
companies:
  - 示例公司
tags:
  - 科技动向
---
```

`public: true` is required for export to GitHub Pages.

## Export to Public Site

After Coze writes the Obsidian file, export public content with:

```bash
python3 scripts/export_public_site.py --vault "/Users/rachelao/Documents/Rachel Capital"
```

Then review generated changes under `public_site` before publishing.

GitHub Pages publishing still requires an explicit user instruction.

## Backfill / Repair

If a report exists on GitHub Pages but does not exist in Obsidian, treat it as a sync failure.

Repair steps:

1. Download the published Markdown from GitHub Pages.
2. Write it into the Obsidian target path.
3. Ensure frontmatter includes `public: true`, `type: daily_intelligence`, `date`, `summary`, `source: coze`, `ecosystem`, `companies`, and `tags`.
4. Keep Obsidian as the source of truth after repair.

## Correction Record

On 2026-07-02, the following reports were backfilled into Obsidian:

```text
31_Inbox/Daily_Intelligence/2026/2026-07/2026-07-01_科技动向日报.md
31_Inbox/Daily_Intelligence/2026/2026-07/2026-07-02_科技动向日报.md
```

This was a repair action, not the preferred publishing path.
