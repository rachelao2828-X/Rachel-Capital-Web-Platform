# Public Daily Full Text Rendering Fix

## Issue

The Public Research Portal Daily Intelligence page only displayed the `summary` from `public_site/data/public_content.json`. It did not load or render the full Markdown report.

## Fix

The portal now uses a static-site friendly flow:

1. `public_site/data/public_content.json` stores metadata and summary only.
2. Each Daily Intelligence item includes a Markdown path:

```text
daily/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

3. The Daily page renders a list of report cards with:
   - Date
   - Title
   - Summary
   - `阅读全文` button
4. Clicking `阅读全文` runs:

```javascript
fetch(item.path)
```

5. The returned Markdown is rendered on the page.

## Markdown Rendering

The front-end renderer supports:

- H1 headings
- H2 headings
- Lists
- Bold text
- Frontmatter hiding

Both `---` and `⸻` frontmatter delimiters are hidden before rendering.

## Export Behavior

`scripts/export_public_site.py` now copies public Markdown files into the static site.

For Daily Intelligence notes, the exported path is:

```text
public_site/daily/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

The JSON item path is:

```json
{
  "path": "daily/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md"
}
```

## Privacy Boundary

Only Markdown notes with frontmatter `public: true` are exported. The full Obsidian vault is not copied.

The portal still must not publish:

- Real holdings
- Private decision logs
- Complete internal valuation models
- API keys or secrets

