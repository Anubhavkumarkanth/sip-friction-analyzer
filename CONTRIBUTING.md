# Contributing to SIP Friction Analyzer

Thank you for your interest in contributing to SIP Friction Analyzer! We welcome contributions from everyone.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 20+
- PostgreSQL 14+
- Git

### Development Setup

**1. Clone and Navigate**
```bash
git clone https://github.com/Anubhavkumarkanth/sip-friction-analyzer.git
cd sip-friction-analyzer
```

**2. Setup Backend**

Create the database and `.env` first, as described under *Setup* in the [README](README.md). The
app will not start without a reachable PostgreSQL.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Backend runs at http://localhost:8000
```

**3. Setup Frontend**
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

**4. Interactive API Documentation**
- Navigate to `http://localhost:8000/docs` for Swagger UI
- Explore and test API endpoints interactively

## Project Structure

```text
├── engine/              # Simulation algorithms & financial metrics
│   ├── simulation.py   # SIP calculations & Monte Carlo engine
│   └── friction.py     # Metrics (CCR, CLD, Discipline Score)
├── frontend/            # React + TypeScript client
│   ├── src/
│   │   ├── components/ # UI, layout, and error boundary components
│   │   ├── hooks/      # Custom React hooks (useDebounce)
│   │   ├── pages/      # Dashboard, Monte Carlo, Explorer, Compare
│   │   ├── services/   # Typed Axios API client
│   │   ├── types/      # Shared TypeScript interfaces
│   │   └── utils/      # INR formatting, API error formatting
│   ├── jest.config.js  # Test configuration
│   └── tsconfig.json   # TypeScript configuration
├── docs/                # Index evaluation (EXPLAIN ANALYZE) notes
├── scripts/             # benchmark_history_index.py: reproduces the index measurement
├── auth.py              # JWT authentication & password hashing
├── config.py            # Pydantic BaseSettings environment configuration
├── conftest.py          # Test setup: database tests only run against a *_test database
├── database.py          # SQLAlchemy connection & session dependency
├── main.py              # FastAPI application routers & lifespans
├── models.py            # SQLAlchemy database models
├── test_backend.py      # API tests (need PostgreSQL)
├── test_engine.py       # Engine and metric tests (no database)
├── ruff.toml            # Python lint settings
└── requirements.txt     # Python backend dependencies
```

## Development Guidelines

### Code Style
- **Python**: unused imports, undefined names and basic style are checked with ruff
  ```bash
  pip install ruff
  ruff check .
  ```
- **Frontend**: Use ESLint and TypeScript checks
  ```bash
  cd frontend
  npm run type-check
  npm run lint
  ```

### Testing

**Backend Tests**

The API tests write and delete rows, so they run only against a database whose name ends in
`_test`. Create one and set `TEST_DATABASE_URL`; without it the database tests are skipped.
```bash
export TEST_DATABASE_URL=postgresql+psycopg2://sip_app:<YOUR_PASSWORD>@localhost:5432/sip_test
pytest -v
```

**Frontend Tests**
```bash
cd frontend
npm test
```

### Git Workflow & Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

1. `feat:` New feature
2. `fix:` Bug fix
3. `docs:` Documentation
4. `refactor:` Code refactoring
5. `test:` Adding/updating tests
6. `chore:` Tooling and configuration updates

---

**Thank you for contributing!** 🎉
