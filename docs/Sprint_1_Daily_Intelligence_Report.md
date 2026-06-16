# Sprint 1 Daily Intelligence MVP Report

Generated: 2026-06-16

## Completed

- Confirmed official project structure:
  - `app/` = FastAPI backend
  - `streamlit_app/` = Streamlit frontend
- Added `POST /api/news` for receiving Daily Intelligence items from Coze or another upstream workflow.
- Added `GET /api/news` for listing recent Daily Intelligence items.
- Added optional `X-Coze-Secret` validation.
- Added SQLAlchemy database layer.
- Added `NewsItem` model.
- Added Alembic configuration.
- Added first migration: `create_news_items_table`.
- Upgraded Streamlit Home for Daily Intelligence display.
- Added Streamlit News page with date, ecosystem, and company filters.
- Added Streamlit Settings page that shows configuration status without exposing secrets.
- Added smoke tests for:
  - `GET /health`
  - `POST /api/news`
  - `GET /api/news`
- Updated `.env.example` with planned integration secrets and tokens.

## API Usage

### POST `/api/news`

Creates a Daily Intelligence news item.

Request body:

```json
{
  "date": "2026-06-16",
  "title": "今日科技投资日报",
  "summary": "摘要",
  "importance": "high",
  "category": "AI",
  "ecosystem": "AI基础设施生态",
  "companies": ["OpenAI", "NVIDIA", "中际旭创"],
  "tags": ["AI", "算力", "光模块"],
  "source": "coze"
}
```

Security behavior:

- If `COZE_WEBHOOK_SECRET` is empty, local development requests may omit `X-Coze-Secret`.
- If `COZE_WEBHOOK_SECRET` is configured, requests must include matching `X-Coze-Secret`.

### GET `/api/news`

Returns recent Daily Intelligence items.

Supported query parameters:

- `limit`
- `date`
- `ecosystem`
- `company`

## Example curl

```bash
curl -X POST http://localhost:8000/api/news \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-06-16",
    "title": "今日科技投资日报",
    "summary": "摘要",
    "importance": "high",
    "category": "AI",
    "ecosystem": "AI基础设施生态",
    "companies": ["OpenAI", "NVIDIA", "中际旭创"],
    "tags": ["AI", "算力", "光模块"],
    "source": "coze"
  }'
```

```bash
curl http://localhost:8000/api/news
```

With a configured Coze secret:

```bash
curl -X POST http://localhost:8000/api/news \
  -H "Content-Type: application/json" \
  -H "X-Coze-Secret: your-secret" \
  -d '{
    "date": "2026-06-16",
    "title": "今日科技投资日报",
    "summary": "摘要",
    "importance": "high",
    "category": "AI",
    "ecosystem": "AI基础设施生态",
    "companies": ["OpenAI", "NVIDIA", "中际旭创"],
    "tags": ["AI", "算力", "光模块"],
    "source": "coze"
  }'
```

## Database Table Structure

Table: `news_items`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key. |
| `date` | Date | News date. |
| `title` | String(255) | News title. |
| `summary` | Text | Summary body. |
| `importance` | String(32) | Example: `high`, `medium`, `low`. |
| `category` | String(100) | Optional category. |
| `ecosystem` | String(150) | Optional ecosystem. |
| `companies` | JSON | List of company names. |
| `tags` | JSON | List of tags. |
| `source` | String(80) | Example: `coze`. |
| `created_at` | DateTime | Creation timestamp. |
| `updated_at` | DateTime | Last update timestamp. |

Migration:

- `alembic/versions/20260616_0001_create_news_items_table.py`

## Streamlit Page Screenshot Notes

Actual screenshots are not stored in this repository yet.

Expected UI after posting sample data:

- Home page at `http://localhost:8501`
  - Shows `Rachel Capital OS Platform`.
  - Shows Daily Intelligence metrics.
  - Shows "今日十大科技投资事件".
  - Shows ecosystem grouping.
  - Shows key company counts.
  - Shows latest update time.
- News page
  - Shows Daily Intelligence list.
  - Provides filters for date, ecosystem, and company.
- Settings page
  - Shows whether `DATABASE_URL`, `OBSIDIAN_VAULT_PATH`, `COZE_WEBHOOK_SECRET`, `FEISHU_WEBHOOK_URL`, and `GITHUB_TOKEN` are configured.
  - Does not display raw secret values.

## Not Completed

- Analyze page is not implemented.
- Valuation page is not implemented.
- Portfolio page is not implemented.
- Committee page is not implemented.
- Coze workflow itself is not implemented inside this repo.
- Feishu integration is not implemented.
- GitHub product integration is not implemented.
- Obsidian read/write service is not implemented.
- Market data integrations are not implemented.
- Authentication and authorization are not implemented.
- Production deployment is not implemented.

## Next Recommendations

1. Connect Coze to `POST /api/news` and confirm the exact payload contract.
2. Add API-level validation for allowed `importance` values.
3. Add deduplication rules for repeated daily news items.
4. Add Alembic execution to deployment or startup procedure.
5. Add an Obsidian Service boundary for future vault writes without changing the vault structure.
6. Add UI screenshots to future release reports after Browser verification is available.

