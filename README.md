# PSX Value Investor Platform

> Pakistan's first AI-powered fundamental analysis platform — helping investors
> answer one question: **"What is this company actually worth, and should I buy it today?"**

This is a monorepo containing the frontend, backend, database, and infrastructure
for the platform. See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for the full product
vision and engineering standards.

---

## Repository layout

```text
frontend/    # Next.js 16 (App Router) + TypeScript + Tailwind CSS
backend/     # FastAPI (Python 3.12) + Pydantic v2 + SQLAlchemy 2.0 + Alembic
database/    # SQL migrations, seeds, and RLS policy definitions
infra/       # Docker Compose, environment templates
scripts/     # Data ops, backfills, maintenance
docs/        # ADRs, API docs, runbooks
```

---

## Tech stack (locked, all free-tier)

| Layer      | Choice                                                       |
| ---------- | ----------------------------------------------------------- |
| Frontend   | Next.js 16 (App Router), React, TypeScript (strict), Tailwind |
| Backend    | FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic               |
| Database   | PostgreSQL (Supabase)                                        |
| Auth       | Supabase Auth (JWT + RLS)                                    |
| CI/CD      | GitHub Actions                                              |
| Hosting    | Vercel (frontend), Render (backend), Supabase (DB)          |

---

## Prerequisites

- **Node.js** ≥ 20 (tested on 24) and npm ≥ 10
- **Docker** + Docker Compose (runs Postgres and the backend locally)
- **Python** 3.12 (only if you want to run the backend outside Docker)
- **Git**

---

## Quick start

### 1. Clone and configure

```bash
git clone <repo-url> psx-value-investor-platform
cd psx-value-investor-platform
cp infra/.env.example infra/.env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### 2. Run the full stack with Docker

```bash
docker compose -f infra/docker-compose.yml up --build
```

- API:      http://localhost:8000  (docs at `/docs`)
- Health:   http://localhost:8000/api/v1/health
- Postgres: localhost:5432

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

- Web app: http://localhost:3000

### 4. Run the backend locally (without Docker, optional)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Unix: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

---

## Common commands

### Frontend (`frontend/`)

```bash
npm run dev        # start dev server
npm run build      # production build
npm run lint       # ESLint
npm run typecheck  # tsc --noEmit
npm run format     # Prettier write
```

### Backend (`backend/`)

```bash
ruff check .       # lint
black .            # format
mypy app           # type check
pytest             # tests + coverage
alembic upgrade head   # apply migrations
```

---

## Environments

Three environments are used: `development`, `staging`, and `production`.
All configuration is supplied via environment variables (12-factor) and validated
at boot. Never commit real secrets — only `.env.example` templates are tracked.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every change ships via pull request with
green lint, type-check, and tests.

## License

[MIT](LICENSE)

---

> **Disclaimer:** This platform is for informational and educational purposes only
> and does not constitute financial advice.
