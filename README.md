# Rachel Capital Platform

Rachel Capital OS Platform V1 is an AI-powered personal research platform for technology investing and industry research.

This repository is the Web App entry point, designed as a Single Pane of Glass. The existing Obsidian vault, `Rachel-Capital-OS-Vault`, remains independent and is not copied or modified by this project. Future vault access should be implemented through an Obsidian Service integration.

## Current Scope

Sprint 1 implements the Daily Intelligence MVP: Coze or another upstream workflow can POST daily technology investment news into `/api/news`, and the Streamlit app can display and filter those items.

## Project Structure

Official structure:

- `app/` is the FastAPI backend.
- `streamlit_app/` is the Streamlit frontend.
- The project will continue using these names. Do not rename them to `backend/` or `frontend/` without a deliberate architecture decision.

```text
Rachel-Capital-Platform/
├── alembic/
├── app/
│   ├── api/
│   │   └── main.py
│   ├── db/
│   ├── models/
│   ├── schemas/
│   └── core/
│       ├── config.py
│       └── logging.py
├── streamlit_app/
│   ├── main.py
│   └── pages/
│       ├── 1_News.py
│       └── 8_Settings.py
├── docs/
│   └── Project_Bootstrap_Report.md
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.streamlit
├── requirements.txt
├── .env.example
└── README.md
```

## Local Setup

Create and activate the Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Run FastAPI locally:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

API endpoints:

- `GET /health`
- `POST /api/news`
- `GET /api/news`

Run Streamlit locally:

```bash
streamlit run streamlit_app/main.py --server.port 8501
```

## Docker

Start the stack:

```bash
docker compose up --build
```

Services:

- FastAPI: http://localhost:8000
- FastAPI health check: http://localhost:8000/health
- Streamlit: http://localhost:8501
- PostgreSQL: localhost:5432

## Configuration

Configuration is centralized in `app/core/config.py` and loaded from environment variables.

Use `.env.example` as the template for local development. Do not commit `.env`.

Local development defaults to SQLite at `sqlite:///./data/rachel_capital.db` so the MVP can run with only FastAPI and Streamlit. Docker Compose overrides `DATABASE_URL` to use PostgreSQL.

## Logging

Logging is initialized in `app/core/logging.py`. The default format is stable and console-friendly for local development and Docker logs.
