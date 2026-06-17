# Public Research Portal Guide

## Purpose

The Public Research Portal is a GitHub Pages site for public technology investment and industry research content.

It is separate from the local Rachel Capital OS web app. The local app remains Rachel's private research cockpit.

## 1. What Can Be Public

Allowed:

- Public daily technology investment summaries
- Public ecosystem observations
- Public company research summaries
- Public monthly industry reports
- Public knowledge graph summaries
- Educational or informational industry notes

Not allowed:

- Real holdings
- Position sizes
- Private decision logs
- Complete internal valuation models
- Internal scores, target prices, or unpublished investment conclusions
- API keys, tokens, webhook secrets, account IDs, or private configuration

## 2. How To Mark Public Content

Only Obsidian Markdown files with frontmatter `public: true` are exported.

Example:

```markdown
---
public: true
type: daily_intelligence
title: 今日科技投资日报
date: 2026-06-17
summary: 今日公开研究摘要。
ecosystem: AI基础设施生态
companies:
  - OpenAI
  - NVIDIA
tags:
  - 科技投资
  - AI
---

正文内容可以公开展示。
```

Files without `public: true` are not exported.

## 3. How To Export `public_site`

From the project root:

```bash
python scripts/export_public_site.py
```

Optional explicit vault path:

```bash
python scripts/export_public_site.py --vault "/Users/rachelao/Documents/Rachel Capital"
```

Output:

```text
public_site/data/public_content.json
```

The exporter does not copy the whole Obsidian vault. It only writes structured JSON for files marked `public: true`.

## 4. How To Enable GitHub Pages

In the GitHub repository:

1. Open `Settings`.
2. Open `Pages`.
3. Set source to `GitHub Actions`.
4. Ensure the workflow `.github/workflows/pages.yml` exists on `main`.
5. Push updates to `main` or manually run the workflow.

The workflow deploys only:

```text
public_site/
```

## 5. How To Update The Website

1. Mark public Obsidian notes with `public: true`.
2. Run:

```bash
python scripts/export_public_site.py
```

3. Preview locally:

```bash
python -m http.server 9000 -d public_site
```

4. Open:

```text
http://localhost:9000
```

5. Commit and push the updated `public_site/data/public_content.json`.
6. Merge or push to `main` to deploy through GitHub Pages.

## 6. How To Avoid Private Leaks

Before marking a note `public: true`, check that it does not contain:

- Actual holdings
- Private watchlist rationale
- Internal decision memos
- Complete valuation models
- API keys or credentials
- Private meeting notes
- Non-public company information

Exporter safeguards:

- Files are skipped unless frontmatter contains `public: true`.
- Hidden folders, `.git`, `.obsidian`, and trash folders are skipped.
- Sensitive frontmatter keys such as `token`, `secret`, `api_key`, `holding`, `position`, and `valuation_model` are not exported.

The exporter cannot understand every private sentence in a Markdown body. Human review is still required before setting `public: true`.

## Disclaimer

文中涉及公司、行业、标的仅为信息整理与研究观察，不构成任何投资建议。投资有风险，决策需谨慎。
