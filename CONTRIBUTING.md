# Contributing to SIP Friction Analyzer

Thank you for your interest in contributing to SIP Friction Analyzer! We welcome contributions from everyone.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 20+
- Git

### Development Setup

**1. Clone and Navigate**
```bash
git clone https://github.com/Anubhavkumarkanth/sip-friction-analyzer.git
cd sip-friction-analyzer
```

**2. Setup Backend**
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
│   │   └── utils/      # INR formatters & client calculation helpers
│   ├── jest.config.js  # Test configuration
│   └── tsconfig.json   # TypeScript configuration
├── auth.py              # JWT authentication & password hashing
├── config.py            # Pydantic BaseSettings environment configuration
├── database.py          # SQLAlchemy connection & session dependency
├── main.py              # FastAPI application routers & lifespans
├── models.py            # SQLAlchemy database models
└── requirements.txt     # Python backend dependencies
```

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8
  ```bash
  flake8 engine/ models.py main.py
  ```
- **Frontend**: Use ESLint and TypeScript checks
  ```bash
  npm run type-check
  npm run lint
  ```

### Testing

**Backend Tests**
```bash
pytest test_backend.py -v
```

**Frontend Tests**
```bash
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
