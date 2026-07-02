# Coze Daily Intelligence Integration Guide

## Publishing Rule

Coze daily reports must be written to Obsidian first.

Standard flow:

```text
Coze -> Obsidian Daily_Intelligence -> scripts/export_public_site.py -> public_site -> GitHub Pages
```

GitHub Pages is not the source of truth. It is only the public display layer.

Coze must not write daily source content only to `public_site`. If `public_site` is updated without the matching Obsidian file, Obsidian will miss the report and future exports may break the public index.

Required Obsidian target:

```text
/Users/rachelao/Documents/Rachel Capital/31_Inbox/Daily_Intelligence/YYYY/YYYY-MM/YYYY-MM-DD_科技动向日报.md
```

Required filename:

```text
YYYY-MM-DD_科技动向日报.md
```

Required frontmatter:

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

`public: true` is mandatory for GitHub Pages export.

## Target Endpoint

Coze should send the Daily Technology Investment Report to:

```text
POST http://localhost:8000/api/news
```

For Docker Compose local networking, if Coze is simulated from another container in the same Compose network, use:

```text
POST http://api:8000/api/news
```

For production or a tunnel URL, replace the host with the deployed FastAPI base URL.

## Headers

Local development without a configured secret:

```text
Content-Type: application/json
```

If `COZE_WEBHOOK_SECRET` is configured in `.env`, Coze must include:

```text
Content-Type: application/json
X-Coze-Secret: your-configured-secret
```

The API does not display or return the configured secret.

## Request JSON Example

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
    },
    {
      "title": "光模块需求保持高景气",
      "summary": "AI 数据中心建设继续带动高速光模块需求。",
      "ecosystem": "AI网络与光通信生态",
      "companies": ["中际旭创"],
      "impact": "强化光通信产业链关注度。",
      "importance": "high",
      "tags": ["光模块", "数据中心"]
    }
  ]
}
```

`events` is optional. If present, the API saves both the daily report record and each event detail.

## curl Test

Start FastAPI:

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

With secret validation:

```bash
curl -X POST http://localhost:8000/api/news \
  -H "Content-Type: application/json" \
  -H "X-Coze-Secret: your-configured-secret" \
  -d '{"date":"2026-06-16","title":"今日科技投资日报","summary":"摘要","importance":"high","category":"AI","ecosystem":"AI基础设施生态","companies":["OpenAI"],"tags":["AI"],"source":"coze","events":[]}'
```

Read back the reports:

```bash
curl http://localhost:8000/api/news
```

Open the frontend:

```bash
streamlit run streamlit_app/main.py --server.port 8501
```

Then visit:

```text
http://localhost:8501
http://localhost:8501/News
```
