# SIP Friction Analyzer

SIP Friction Analyzer is a full-stack web application for visualising how changes in a systematic investment plan (SIP) can affect long-term portfolio value. It compares an ideal contribution schedule with a schedule affected by pauses, skipped contributions, reductions, increases, and annual step-ups.

## Features

- Compares ideal and event-adjusted SIP growth month by month.
- Calculates contribution compliance rate (CCR), compounding loss, and a discipline score.
- Runs Monte Carlo simulations for a range of possible outcomes.
- Includes an interactive React dashboard, fund explorer, and fund-comparison views.
- Provides REST endpoints with FastAPI and persists simulation results in SQLite.

## Technology

- Frontend: React, Vite, Recharts, Axios
- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- Storage: SQLite

## Run locally

Prerequisites: Python 3.9 or later, Node.js 20 or later, and npm.

1. Start the API from the repository root.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`; interactive API documentation is at `/docs`.

2. In a second terminal, start the frontend.

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open the URL printed by Vite (normally `http://localhost:5173`).

## API overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | API health response |
| `POST` | `/simulate` | Runs a deterministic SIP simulation |
| `POST` | `/monte-carlo` | Runs a stochastic SIP simulation |
| `GET` | `/funds` | Lists locally seeded sample funds |
| `GET` | `/search-funds` | Searches and sorts the sample fund data |
| `POST` | `/token` | Returns an access token for valid credentials |

## Project structure

```text
├── engine/              # SIP calculations and friction metrics
├── frontend/            # React + Vite client application
├── main.py              # FastAPI routes
├── models.py            # SQLAlchemy database models
├── database.py          # Database configuration
├── auth.py              # Authentication helpers
└── test_backend.py      # Backend API tests
```

## Metrics

- **CCR** = actual contributions / expected contributions.
- **Compounding loss** = ideal portfolio value − actual portfolio value.
- **Discipline score** combines contribution consistency and the relative compounding loss on a 0–100 scale.

## Important note

This project is an educational simulator. It uses illustrative assumptions and locally seeded sample fund data; it is not investment advice and should not be used as the basis for financial decisions.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest test_backend.py -v
```

## License

Released under the [MIT License](LICENSE).
