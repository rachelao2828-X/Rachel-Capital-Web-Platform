# System Architecture

## Official Project Structure

Rachel Capital OS Platform uses the following official structure:

- `app/` = FastAPI backend
- `streamlit_app/` = Streamlit frontend

The project will continue using `app/` and `streamlit_app/` as canonical names. The directories should not be renamed to `backend/` and `frontend/` unless a future architecture decision explicitly approves that change.

## Backend

The FastAPI backend lives in `app/`.

Current backend responsibilities:

- Application entry point: `app/api/main.py`
- API routes: `app/api/routes/`
- Configuration: `app/core/config.py`
- Logging: `app/core/logging.py`
- Database session and metadata: `app/db/`
- SQLAlchemy models: `app/models/`
- Pydantic schemas: `app/schemas/`

Current API surface:

- `GET /health`
- `POST /api/news`
- `GET /api/news`

## Frontend

The Streamlit frontend lives in `streamlit_app/`.

Current frontend responsibilities:

- Home page: `streamlit_app/main.py`
- News page: `streamlit_app/pages/1_News.py`
- Settings page: `streamlit_app/pages/8_Settings.py`

The Sprint 1 frontend reads Daily Intelligence data from the FastAPI `/api/news` endpoint.

## Database

The application uses SQLAlchemy.

Local development defaults to SQLite:

```text
sqlite:///./data/rachel_capital.db
```

Docker Compose uses PostgreSQL:

```text
postgresql+psycopg://rachel:change_me@postgres:5432/rachel_capital
```

Alembic migrations live in `alembic/`.

## Sprint 1 Boundary

Sprint 1 implements only Daily Intelligence MVP capabilities:

- Receive daily technology investment news through `POST /api/news`.
- List recent daily intelligence items through `GET /api/news`.
- Display recent intelligence on Streamlit Home.
- Filter intelligence on the News page.
- Show configuration status on the Settings page.

Analyze, Valuation, Portfolio, and Committee are not implemented in Sprint 1.

