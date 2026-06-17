# Rachel Capital Public Research Portal

This directory contains the static GitHub Pages site for public research output.

The public site is intentionally separate from the local Rachel Capital OS web app.

## Public Boundary

The public site may include:

- Public daily technology investment summaries
- Public ecosystem observations
- Public company research summaries
- Public monthly industry reports
- Public knowledge graph summaries

The public site must not include:

- Real holdings
- Private decision logs
- Complete internal valuation models
- API keys, tokens, webhook secrets, or private configuration

## Data Export

Run:

```bash
python scripts/export_public_site.py
```

Only Obsidian Markdown files with frontmatter `public: true` are exported.

Output is written to:

```text
public_site/data/public_content.json
```

## Local Preview

Use any static file server from the repository root:

```bash
python -m http.server 9000 -d public_site
```

Then open:

```text
http://localhost:9000
```
