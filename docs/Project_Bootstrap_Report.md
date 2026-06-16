# Project Bootstrap Report

## Project

- Name: Rachel Capital Platform
- Version: V1 scaffold
- Purpose: AI-powered personal research platform for technology investing and industry research
- Entry point: Web App as Single Pane of Glass

## Completed Bootstrap Items

1. Initialized project directory structure.
2. Created Python virtual environment at `.venv`.
3. Initialized Git repository.
4. Added Docker configuration.
5. Added FastAPI backend scaffold.
6. Added Streamlit frontend scaffold.
7. Added PostgreSQL service via Docker Compose.
8. Added centralized configuration in `app/core/config.py`.
9. Added centralized logging in `app/core/logging.py`.
10. Added documentation directory and bootstrap report.

## Generated Files

- `README.md`
- `.env.example`
- `docker-compose.yml`
- `requirements.txt`
- `docs/Project_Bootstrap_Report.md`
- `Dockerfile.api`
- `Dockerfile.streamlit`
- `.gitignore`
- `app/api/main.py`
- `app/core/config.py`
- `app/core/logging.py`
- `streamlit_app/main.py`

## Obsidian Vault Boundary

The existing `Rachel-Capital-OS-Vault` remains independent.

This bootstrap does not copy, move, or modify Obsidian vault content or directory structure. Future integration should be implemented through an explicit Obsidian Service layer.

## Run Commands

Install local dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Run frontend:

```bash
streamlit run streamlit_app/main.py --server.port 8501
```

Run Docker stack:

```bash
cp .env.example .env
docker compose up --build
```

## Current Phase Boundary

Phase 1 only provides the project scaffold and infrastructure baseline. No business workflows, research agents, market data ingestion, portfolio logic, or Obsidian read/write behavior have been implemented.

## Verification

- Python virtual environment created at `.venv`.
- Dependencies installed from `requirements.txt`.
- Python modules compiled successfully.
- FastAPI app imported successfully.
- FastAPI `/health` endpoint returned `{"status":"ok"}` during local verification.
- Streamlit app started successfully and returned HTTP 200 during local verification.
- `docker-compose.yml` passed YAML parsing.
- Docker Compose runtime verification was not executed because the local `docker` command is not currently available in this environment.

## Git

- Repository initialized.
- Current branch: `main`.
- `.env`, `.venv`, and Python cache directories are ignored by Git.
