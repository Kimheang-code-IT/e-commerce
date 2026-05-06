# E-Commerce Backend (FastAPI)

SQLite-first FastAPI backend that implements all API contracts documented in `docs/`.

## Run

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Start API:
   - `uvicorn app.main:app --reload`
3. Open docs:
   - `http://127.0.0.1:8000/docs`

## Auth Bootstrap

- Default admin:
  - email: `admin@example.com`
  - password: `secret`

Use `POST /api/v1/auth/login` to get a bearer token.

## Testing

- `pytest -q`

## PostgreSQL + Redis Later

See `docs/postgresql-redis-migration.md` for migration steps from SQLite-first phase.
