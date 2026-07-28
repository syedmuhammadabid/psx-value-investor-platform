# Backend — PSX Value Investor Platform

FastAPI (Python 3.12) service providing the REST API, financial calculations, and
valuation engine.

## Layout

```text
app/
  api/            # versioned routers (v1) and dependencies
  core/           # config, logging, middleware, exceptions, security
  models/         # SQLAlchemy models
  schemas/        # Pydantic request/response models
  services/       # business logic layer
  calculations/   # pure, unit-tested financial math
  valuation/      # valuation models
  scraper/        # PSX ingestion + parsers
  repositories/   # data-access layer
  jobs/           # scheduled/background tasks
tests/            # pytest unit + integration
alembic/          # database migrations
```

## Local development

### With Docker (recommended)

```bash
docker compose -f ../infra/docker-compose.yml up --build
```

### Without Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Unix: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Quality gates

```bash
ruff check .          # lint
black --check .        # format
mypy app               # type check (strict)
pytest --cov=app       # tests + coverage
```

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
