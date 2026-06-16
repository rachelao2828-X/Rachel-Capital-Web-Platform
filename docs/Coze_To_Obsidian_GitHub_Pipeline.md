# Coze to Obsidian to GitHub Daily Intelligence Pipeline

## Purpose

This pipeline receives a daily technology investment report from Coze, saves it through the Rachel Capital OS Platform API, writes a Markdown copy into the Obsidian vault, and optionally commits and pushes the vault changes to GitHub.

Flow:

```text
Coze -> POST /api/news -> Database -> Streamlit Platform -> Obsidian Inbox -> Git commit + push
```

## 1. Coze POST Endpoint

Coze should send the report to the FastAPI endpoint:

```text
POST http://localhost:8000/api/news
```

For a deployed server, replace the host:

```text
POST https://your-domain.example/api/news
```

Required header:

```text
Content-Type: application/json
```

If `COZE_WEBHOOK_SECRET` is configured:

```text
X-Coze-Secret: your-secret
```

## 2. Request JSON Example

```json
{
  "date": "2026-06-16",
  "title": "今日科技投资日报",
  "summary": "AI 基础设施、半导体和云计算方向出现多条重要产业事件。",
  "importance": "high",
  "category": "AI",
  "ecosystem": "AI基础设施生态",
  "companies": ["OpenAI", "NVIDIA", "中际旭创"],
  "tags": ["AI", "算力", "光模块"],
  "source": "coze",
  "events": [
    {
      "title": "AI 算力基础设施继续扩张",
      "summary": "头部 AI 公司继续推动推理与训练基础设施投入。",
      "ecosystem": "AI基础设施生态",
      "companies": ["OpenAI", "NVIDIA"],
      "impact": "提升算力链条景气度。",
      "importance": "high",
      "tags": ["AI", "算力"]
    }
  ]
}
```

Successful response:

```json
{
  "status": "ok",
  "news_id": 1,
  "db_sync": "success",
  "obsidian_sync": "success",
  "git_sync": "success"
}
```

## 3. Environment Configuration

Use `.env.example` as the template:

```text
DATABASE_URL=sqlite:///./data/rachel_capital.db
OBSIDIAN_VAULT_PATH=/absolute/path/to/Rachel-Capital-OS-Vault
DAILY_REPORT_OBSIDIAN_DIR=31_Inbox/Daily_Intelligence
GIT_AUTO_COMMIT=true
GIT_BRANCH=develop
COZE_WEBHOOK_SECRET=
```

Notes:

- `OBSIDIAN_VAULT_PATH` must be the absolute path to the root of the Obsidian vault.
- `DAILY_REPORT_OBSIDIAN_DIR` is created automatically inside the vault.
- `COZE_WEBHOOK_SECRET` can be empty for local development.
- If `COZE_WEBHOOK_SECRET` is set, Coze must send the matching `X-Coze-Secret` header.
- `.env` must not be committed.

## 4. Obsidian Vault Path

Example macOS path:

```text
/Users/rachelao/Documents/Rachel-Capital-OS-Vault
```

The API writes Markdown files to:

```text
{OBSIDIAN_VAULT_PATH}/31_Inbox/Daily_Intelligence/YYYY-MM-DD_科技投资日报.md
```

If the vault path is not configured, the database save still succeeds and the API returns:

```text
obsidian_sync: skipped_not_configured
git_sync: skipped
```

If the vault path does not exist, the database save still succeeds and the API returns:

```text
obsidian_sync: failed
git_sync: skipped
```

## 5. GitHub Auto Backup

If `GIT_AUTO_COMMIT=true`, the API attempts to run the following inside the Obsidian vault after the Markdown file is written:

```bash
git add .
git commit -m "Add daily intelligence report YYYY-MM-DD"
git push origin HEAD:${GIT_BRANCH}
```

Safety behavior:

- If the vault is not a Git repository, backup is skipped with `git_sync: skipped_not_git_repo`.
- If there are no staged changes, backup is skipped with `git_sync: skipped_no_changes`.
- `.env` and `.env.*` are explicitly unstaged before commit.
- Git failure does not roll back the database save or Obsidian write.

## 6. Local Test

Start the API:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Post a sample report:

```bash
curl -X POST http://localhost:8000/api/news \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-06-16",
    "title": "今日科技投资日报",
    "summary": "AI 基础设施、半导体和云计算方向出现多条重要产业事件。",
    "importance": "high",
    "category": "AI",
    "ecosystem": "AI基础设施生态",
    "companies": ["OpenAI", "NVIDIA", "中际旭创"],
    "tags": ["AI", "算力", "光模块"],
    "source": "coze",
    "events": [
      {
        "title": "AI 算力基础设施继续扩张",
        "summary": "头部 AI 公司继续推动推理与训练基础设施投入。",
        "ecosystem": "AI基础设施生态",
        "companies": ["OpenAI", "NVIDIA"],
        "impact": "提升算力链条景气度。",
        "importance": "high",
        "tags": ["AI", "算力"]
      }
    ]
  }'
```

Start the platform:

```bash
streamlit run streamlit_app/main.py --server.port 8501
```

Open:

```text
http://localhost:8501
http://localhost:8501/News
http://localhost:8501/Settings
```

## 7. Troubleshooting

### `obsidian_sync: skipped_not_configured`

`OBSIDIAN_VAULT_PATH` is empty. Add the absolute vault path to `.env`.

### `obsidian_sync: failed`

Common causes:

- Vault path does not exist.
- The process does not have write permission.
- The configured daily report directory is invalid.

### `git_sync: skipped_not_git_repo`

The Obsidian vault is not initialized as a Git repository. Run this inside the vault if Git backup is desired:

```bash
git init
git remote add origin <your-vault-backup-repo-url>
```

### `git_sync: skipped_no_changes`

The Markdown file was already up to date or no files were staged after `.env` was excluded.

### `git_sync: failed`

Common causes:

- Remote is missing.
- Authentication is not configured.
- Branch push is rejected.
- Network is unavailable.

Run inside the vault to debug:

```bash
git status
git remote -v
git push origin HEAD:develop
```

