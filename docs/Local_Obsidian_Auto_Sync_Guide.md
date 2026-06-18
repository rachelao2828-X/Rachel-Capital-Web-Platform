# Local Obsidian Auto Sync Guide

## Goal

Make Coze daily reports appear in the local Obsidian vault automatically after they are published to GitHub Pages.

Pipeline:

```text
Coze -> GitHub main -> GitHub Pages -> local sync job -> Obsidian Daily_Intelligence
```

## Local Target

Daily reports are written to:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

## Sync Script

The script is:

```text
scripts/sync_github_daily_to_obsidian.py
```

It does not depend on the current Git branch. It fetches `origin/main`, reads Markdown files from:

```text
origin/main:public_site/daily
```

Then writes them into the local Obsidian vault.

Manual run:

```bash
python3 scripts/sync_github_daily_to_obsidian.py
```

Dry run:

```bash
python3 scripts/sync_github_daily_to_obsidian.py --dry-run
```

## macOS Auto Sync

The launch agent template is:

```text
scripts/com.rachelcapital.daily-intelligence-sync.plist
```

Installed path:

```text
~/Library/LaunchAgents/com.rachelcapital.daily-intelligence-sync.plist
```

Schedule:

- Runs once when loaded.
- Runs every 30 minutes.

Logs:

```text
~/Library/Logs/rachel-capital-daily-intelligence-sync.log
~/Library/Logs/rachel-capital-daily-intelligence-sync.err.log
```

## Verification

Check today's report:

```bash
find "/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence" -name "*科技动向日报.md"
```

If Coze has published today's report to GitHub but it does not appear locally, run:

```bash
python3 scripts/sync_github_daily_to_obsidian.py
```

## Notes

This local sync is separate from GitHub Pages deployment. GitHub Pages can update correctly while the local Obsidian vault remains stale unless the local machine fetches and syncs the new files.
