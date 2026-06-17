# Obsidian Daily Intelligence Sync Guide

## Goal

Daily reports are published by Coze into the public web platform repository, then copied into the private Obsidian vault repository.

Pipeline:

```text
Coze daily report
-> Rachel-Capital-Web-Platform
-> GitHub Pages
-> Rachel-Capital-OS-Vault
-> Obsidian Git Pull
```

## Public Source

Coze writes public daily Markdown files to:

```text
public_site/daily/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

These files are safe for GitHub Pages and must not include private holdings, decision logs, full valuation models, API keys, tokens, or secrets.

## Obsidian Target

The sync workflow copies daily Markdown files into the private Obsidian vault repository:

```text
31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

The local Obsidian vault path is:

```text
/Users/rachelao/Documents/Rachel Capital
```

## GitHub Actions Setup

The workflow is:

```text
.github/workflows/sync-obsidian-vault.yml
```

It runs when `main` receives changes under:

```text
public_site/daily/**
```

Required repository secret on `Rachel-Capital-Web-Platform`:

```text
VAULT_SYNC_TOKEN
```

This should be a fine-grained GitHub token with contents read/write access to the private Obsidian vault repository.

Optional repository variable:

```text
OBSIDIAN_VAULT_REPO
```

Default value used by the workflow:

```text
rachelao2828-X/Rachel-Capital-OS-Vault
```

Set the variable only if the private vault repository uses a different name.

## Local One-Time Sync

To copy existing public daily reports into the local Obsidian vault:

```bash
python3 scripts/sync_public_daily_to_obsidian.py
```

Dry run:

```bash
python3 scripts/sync_public_daily_to_obsidian.py --dry-run
```

## Obsidian Setup

The local Obsidian vault should be connected to the private vault repository, not to the public web platform repository.

Recommended remote:

```text
git@github.com:rachelao2828-X/Rachel-Capital-OS-Vault.git
```

After the GitHub Actions workflow syncs a daily report into the private vault repo, run Git Pull in Obsidian or through the Obsidian Git plugin.

## Expected Result

After pull, the daily report appears in Obsidian:

```text
31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

## Troubleshooting

- If the workflow fails with `Missing repository secret: VAULT_SYNC_TOKEN`, add the secret in GitHub repository settings.
- If checkout of the vault repository fails, confirm the token can access the private vault repo.
- If Obsidian does not show the report, run Git Pull in the local vault and confirm the file exists under `31_Inbox/Daily_Intelligence`.
- If the private vault repo has a different name, set `OBSIDIAN_VAULT_REPO`.
- Do not connect Obsidian directly to the web platform repository, because that would pull app code and GitHub Pages files into the vault.
