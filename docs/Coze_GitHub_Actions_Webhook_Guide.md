# Coze to GitHub Actions Daily Intelligence Webhook

## Goal

Coze is cloud-hosted, so it must not send Daily Intelligence reports to `localhost`.

The stable cloud path is:

```text
Coze
-> GitHub repository_dispatch
-> GitHub Actions
-> Obsidian Vault repository
-> public_site export
-> completeness check
-> GitHub Pages
```

Obsidian remains the source of truth. GitHub Pages is only the public display layer.

## GitHub API Endpoint for Coze

Configure Coze to send an HTTP POST request to:

```text
https://api.github.com/repos/rachelao2828-X/Rachel-Capital-Web-Platform/dispatches
```

Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer <COZE_GITHUB_DISPATCH_TOKEN>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Body:

```json
{
  "event_type": "coze_daily_intelligence",
  "client_payload": {
    "date": "YYYY-MM-DD",
    "title": "YYYY-MM-DD 科技动向日报",
    "summary": "日报公开摘要",
    "source": "coze",
    "ecosystem": ["AI基础设施生态"],
    "companies": ["OpenAI", "NVIDIA"],
    "tags": ["科技动向", "AI"],
    "markdown": "# YYYY-MM-DD 科技动向日报\n\n## 摘要\n\n..."
  }
}
```

`date` is required. `markdown` should contain the full Daily Intelligence report body.

If Coze has trouble escaping long Markdown text in JSON, send `markdown_base64` instead of `markdown`. The GitHub Actions script supports both fields.

## Required GitHub Configuration

In the Web Platform repository:

- The workflow `.github/workflows/auto-publish-daily-intelligence.yml` must exist on the default branch, currently `main`.
- GitHub Actions must be enabled.
- `GITHUB_TOKEN` must have permission to write repository contents.
- The repository dispatch token used by Coze should be a fine-grained token scoped to the Web Platform repository with permission to create repository dispatch events.

In repository secrets:

- `VAULT_SYNC_TOKEN` must allow read/write access to the private Obsidian Vault repository.

In Coze:

- Store the GitHub dispatch token as a secret, not in prompt text.
- Use the token only in the `Authorization` header.
- Treat a non-2xx GitHub response as failure and retry. A successful repository dispatch normally returns an empty success response.

## No-Omission Rules

Coze must consider the run successful only after the GitHub dispatch request returns success.

GitHub Actions then enforces:

1. The Coze payload is written to Obsidian as `YYYY-MM-DD_科技动向日报.md`.
2. Frontmatter is normalized with `public: true` and `type: daily_intelligence`.
3. `public_site` is exported from Obsidian.
4. The completeness check must pass.
5. GitHub Pages is updated only after the check passes.

If the payload is missing, malformed, or incomplete, the workflow fails and does not publish incomplete content.
