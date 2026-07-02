# Coze Daily Intelligence Publishing Rules

## Source of Truth

Obsidian is the source of truth for daily intelligence reports.

Coze must write each daily report to the Obsidian vault first:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

GitHub Pages is only the public display layer. It must be generated from Obsidian through the public export workflow.

## Required Flow

```text
Coze
-> Obsidian Daily_Intelligence Markdown
-> scripts/export_public_site.py
-> public_site
-> GitHub Pages
```

Do not use this as the primary flow:

```text
Coze -> public_site -> GitHub Pages -> Obsidian
```

That reverse sync path is allowed only as a repair/backfill workflow when published Pages content is missing from Obsidian.

## File Naming

Each report must use:

```text
YYYY-MM-DD_科技动向日报.md
```

The parent directory must use:

```text
YYYY/YYYY-MM/
```

Example:

```text
31_Inbox/Daily_Intelligence/2026/2026-07/2026-07-02_科技动向日报.md
```

## Required Frontmatter

Each Coze daily report must include:

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

`public: true` is required. Without it, `scripts/export_public_site.py` will not export the report to GitHub Pages.

## Public Boundary

Daily reports may include public technology and industry research content.

Daily reports must not include:

- internal holdings
- private decision logs
- full valuation models
- unapproved private-market project details
- customer lists
- commercial terms
- API keys, tokens, or secrets

## Publish Rule

After Coze writes the Obsidian file:

```bash
python3 scripts/export_public_site.py --vault "/Users/rachelao/Documents/Rachel Capital"
```

Then review the generated `public_site` diff before publishing GitHub Pages.

GitHub Pages publishing still requires an explicit user instruction.

## Backfill Rule

If GitHub Pages contains a daily report but Obsidian does not, treat it as a sync failure.

Allowed repair workflow:

1. Fetch the published Markdown from GitHub Pages.
2. Write it back to the Obsidian path.
3. Ensure frontmatter includes `public: true`, `type: daily_intelligence`, `date`, `summary`, `source: coze`, `ecosystem`, `companies`, and `tags`.
4. Do not treat `public_site` as the new source of truth.

## Current Correction Record

On 2026-07-02, `2026-07-01_科技动向日报.md` and `2026-07-02_科技动向日报.md` were backfilled from GitHub Pages into:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/2026/2026-07/
```

This was a repair action. Future daily reports should be written to Obsidian first.
