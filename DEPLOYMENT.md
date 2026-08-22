# Deployment Guide

## Local Development

### Quick Start
```bash
# Backend (Terminal 1)
uvicorn main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev
```

The client UI is available at `http://localhost:5173`, and the API is accessible at `http://localhost:8000`.

---

## Docker Deployment

### Build and Run with Docker
```bash
# Build multi-stage image
docker build -t sip-analyzer:latest .

# Run containerized service
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///./sip.db sip-analyzer:latest
```

### Docker Compose
```bash
# Start container stack in detached mode
docker compose up -d

# View live service logs
docker compose logs -f

# Teardown stack
docker compose down
```

---

## Cloud Deployment Options

### Option 1: Vercel (Frontend) + Render / Railway (Backend)

**Frontend Deployment (Vercel)**:
1. Connect repository to Vercel.
2. Set root directory to `frontend`.
3. Set environment variable: `VITE_API_URL=https://your-backend-api.onrender.com`.
4. Deploy from `main` branch.

**Backend Deployment (Render / Railway)**:
1. Connect GitHub repository.
2. Set build command: `pip install -r requirements.txt`.
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Set environment variables:
   ```env
   DATABASE_URL=sqlite:///./sip.db
   SECRET_KEY=your-production-secret-key
   ```

### Option 2: AWS ECS / EC2 Deployment

```bash
# SSH into EC2 instance
ssh -i key.pem ubuntu@instance-ip

# Install Docker & Docker Compose
sudo apt-get update -y
sudo apt-get install docker.io docker-compose -y

# Clone repo & run stack
git clone https://github.com/Anubhavkumarkanth/sip-friction-analyzer.git
cd sip-friction-analyzer
docker compose up -d --build
```

---

## Production Security Checklist

- [x] Strict TypeScript contracts across all UI layers
- [x] Input bounds validation on FastAPI Pydantic models
- [x] Environment variable decoupling for secrets via `config.py`
- [x] React ErrorBoundary integration
- [x] GitHub Actions automated CI testing
- [ ] Configure production HTTPS / SSL termination
- [ ] Replace SQLite with managed PostgreSQL for high-concurrency multi-instance deployments
