# Rachel Capital Platform Go-Live Architecture Review

Generated: 2026-06-16

## 1. Project Root Directory Tree, Depth 3

`tree` is not available in the current environment. The following tree was generated with an equivalent Python `os.walk` script, excluding `.git`, `.venv`, `.env`, and Python cache directories.

```text
.
├── .env.example
├── .gitignore
├── Dockerfile.api
├── Dockerfile.streamlit
├── README.md
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   └── services/
├── docker-compose.yml
├── docs/
│   ├── Go_Live_Architecture_Review.md
│   └── Project_Bootstrap_Report.md
├── requirements.txt
├── scripts/
└── streamlit_app/
    └── main.py
```

## 2. Key File Inventory

| Required File | Current Status | Notes |
|---|---:|---|
| `README.md` | Present | Project setup and run instructions exist. |
| `docker-compose.yml` | Present | Defines PostgreSQL, FastAPI API service, and Streamlit service. |
| `requirements.txt` | Present | Python dependencies are pinned. No `pyproject.toml` exists. |
| `.env.example` | Present | Environment variable template exists. |
| `.gitignore` | Present | Ignores `.env`, `.venv`, Python cache, and local artifacts. |
| `backend/main.py` | Not present | Current backend entry is `app/api/main.py`. |
| `frontend/Home.py` | Not present | Current frontend entry is `streamlit_app/main.py`. |

## 3. FastAPI Route Inventory

Routes read from the current FastAPI app:

| Method | Path | Status | Notes |
|---|---|---:|---|
| GET | `/` | Implemented | Scaffold root endpoint. |
| GET | `/health` | Implemented | Health check endpoint. Verified locally with `{"status":"ok"}`. |
| GET | `/api/news` | Not implemented | Required future route; no handler exists. |
| GET | `/openapi.json` | Auto-generated | FastAPI OpenAPI schema. |
| GET | `/docs` | Auto-generated | Swagger UI. |
| GET | `/docs/oauth2-redirect` | Auto-generated | Swagger OAuth helper route. |
| GET | `/redoc` | Auto-generated | ReDoc UI. |

No custom POST routes are currently implemented.

## 4. Streamlit Page Inventory

| Page | Status | Current File |
|---|---:|---|
| Home | Implemented | `streamlit_app/main.py` provides the only current Streamlit page. |
| News | Not implemented | No page file exists. |
| Ecosystems | Not implemented | No page file exists. |
| Companies | Not implemented | No page file exists. |
| Analyze | Not implemented | No page file exists. |
| Valuation | Not implemented | No page file exists. |
| Portfolio | Not implemented | No page file exists. |
| Committee | Not implemented | No page file exists. |
| Settings | Not implemented | No page file exists. |

There is no Streamlit `pages/` directory yet. The non-Home pages are not even placeholder files at this stage.

## 5. Database Design

| Item | Current Status |
|---|---|
| Database engine | PostgreSQL is configured through Docker Compose using `postgres:16-alpine`. |
| SQLite | Not used. |
| ORM dependency | SQLAlchemy is installed, but no ORM models are defined. |
| PostgreSQL driver | `psycopg[binary]` is installed. |
| Created tables | None. |
| Table fields | Not applicable. No tables exist. |
| Migrations | Not implemented. No Alembic configuration or migration directory exists. |
| Persistence | Docker volume `postgres_data` is defined. |

## 6. Configuration And Secret Management

Variables currently present in `.env.example`:

```text
APP_NAME
APP_ENV
APP_DEBUG
LOG_LEVEL
API_HOST
API_PORT
STREAMLIT_PORT
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DATABASE_URL
OBSIDIAN_VAULT_PATH
```

Security status:

| Check | Status | Notes |
|---|---:|---|
| `.env` ignored by Git | Yes | `.gitignore` contains `.env`. |
| Real API keys committed | No evidence | No real API keys are present in tracked project files. |
| Example secrets | Present | `POSTGRES_PASSWORD=change_me` is an example value and must be changed before real deployment. |
| Centralized config | Present | `app/core/config.py` loads settings from environment variables. |
| Centralized logging | Present | `app/core/logging.py` configures console logging. |

## 7. Integration Module Status

| Integration | Status | Evidence |
|---|---:|---|
| Coze | Not implemented | No dependency, config, client, service, or route exists. |
| Feishu | Not implemented | No dependency, config, client, service, or route exists. |
| GitHub | Not implemented in app | Git repository exists, but no product integration module exists. |
| Obsidian | Placeholder, not implemented | `OBSIDIAN_VAULT_PATH` exists in `.env.example`; no service code exists. |
| AkShare | Not implemented | No dependency or integration module exists. |
| Tushare | Not implemented | No dependency or integration module exists. |
| yfinance | Not implemented | No dependency or integration module exists. |
| Alpha Vantage | Not implemented | No API key config or integration module exists. |
| FRED | Not implemented | No API key config or integration module exists. |

## 8. Local Run Instructions

Backend:

```bash
source .venv/bin/activate
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
source .venv/bin/activate
streamlit run streamlit_app/main.py --server.port 8501
```

Docker:

```bash
cp .env.example .env
docker compose up --build
```

Default local access:

| Service | URL |
|---|---|
| FastAPI | `http://localhost:8000` |
| FastAPI health check | `http://localhost:8000/health` |
| FastAPI docs | `http://localhost:8000/docs` |
| Streamlit | `http://localhost:8501` |
| PostgreSQL | `localhost:5432` |

Current environment note: Docker runtime was not verified locally because the `docker` command is not available in this environment.

## 9. Current Completed Capabilities

- Independent project scaffold exists.
- Python virtual environment exists at `.venv`.
- Dependencies from `requirements.txt` have been installed locally.
- Git repository has been initialized on branch `main`.
- FastAPI backend can start and serve `/health`.
- Streamlit frontend can start and serve the Home scaffold.
- PostgreSQL service is defined in Docker Compose.
- Environment configuration template exists.
- `.env` is excluded from Git.
- Basic logging setup exists.
- Bootstrap documentation exists.

## 10. Current Incomplete Capabilities

- No business workflows are implemented.
- `/api/news` does not exist.
- No database tables are defined.
- No migrations are configured.
- No ingestion jobs exist.
- No data source integrations exist.
- No Obsidian read/write service exists.
- No multi-page Streamlit application structure exists.
- No authentication or authorization exists.
- No tests are present.
- No CI/CD pipeline exists.
- No production deployment configuration exists.

## 11. Known Issues And Risks

| Risk | Current Impact | Notes |
|---|---|---|
| Port conflicts | Possible | Defaults use API `8000`, Streamlit `8501`, PostgreSQL `5432`. Conflicts must be resolved through environment variables. |
| API keys missing | Expected | No external integrations are implemented yet, so no API key variables exist for Coze, Feishu, AkShare, Tushare, Alpha Vantage, or FRED. |
| Data source instability | Future risk | No market data sources are integrated yet; reliability has not been tested. |
| Obsidian path not configured | Current blocker for future integration | `OBSIDIAN_VAULT_PATH` is empty in `.env.example`. |
| Docker unavailable in current environment | Current verification limitation | `docker compose` runtime was not tested locally. |
| Directory naming mismatch | Minor review risk | Requested key paths `backend/main.py` and `frontend/Home.py` do not exist; current paths are `app/api/main.py` and `streamlit_app/main.py`. |
| No migrations | Current architecture gap | Database schema cannot be versioned yet. |
| No tests | Current delivery risk | There are no automated checks beyond manual startup validation. |
| No auth | Future security risk | Platform is not ready for exposure beyond local development. |

## 12. Sprint 1 Recommendations

1. Normalize project structure for the agreed convention: either adopt `backend/` and `frontend/`, or document `app/` and `streamlit_app/` as the official layout.
2. Add a minimal backend API namespace, including `/api/news`, with placeholder responses if the data source is not ready.
3. Create Streamlit multi-page structure for Home, News, Ecosystems, Companies, Analyze, Valuation, Portfolio, Committee, and Settings.
4. Add database schema management with Alembic.
5. Define initial tables for source registry, research notes metadata, company registry, and ingestion logs.
6. Add an Obsidian Service boundary without touching the vault structure.
7. Add typed configuration variables for all planned integrations, using empty example values only.
8. Add smoke tests for FastAPI routes and config loading.
9. Add a Docker verification checklist once Docker is available locally.

## Go-Live Readiness Self-Score

Scale: 1 = not ready, 5 = production-ready.

| Area | Score | Rationale |
|---|---:|---|
| Architecture | 2.0 / 5 | Basic service separation exists, but no domain modules or schema boundaries exist yet. |
| Security | 2.0 / 5 | `.env` is ignored and no real keys are committed, but auth and secret rotation are absent. |
| Data Integration | 1.0 / 5 | PostgreSQL is configured, but no data integrations or tables exist. |
| Frontend | 1.5 / 5 | Streamlit Home scaffold runs; required pages are not implemented. |
| Backend | 2.0 / 5 | FastAPI runs with health check; business APIs are not implemented. |
| Obsidian Integration | 1.0 / 5 | Only a config placeholder exists. No service implementation exists. |
| Overall | 1.6 / 5 | Suitable as a local scaffold baseline, not ready for go-live beyond development bootstrap review. |
