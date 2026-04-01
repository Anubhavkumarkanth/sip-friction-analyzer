# Deployment Guide

## Local Development

### Quick Start
```bash
# Backend
python main.py

# Frontend (new terminal)
cd frontend && npm run dev
```

Access at `http://localhost:5173`

---

## Docker Deployment

### Build and Run
```bash
# Build image
docker build -t sip-analyzer:latest .

# Run container
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///./app.db sip-analyzer:latest
```

### Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## Cloud Deployment

### Option 1: Vercel (Frontend) + Railway (Backend)

**Frontend Deployment (Vercel)**
1. Push code to GitHub
2. Connect repo to Vercel
3. Set environment variable: `VITE_API_URL=https://your-backend-url`
4. Deploy automatically on push

**Backend Deployment (Railway)**
1. Create Railway project
2. Connect GitHub repo
3. Add environment variables:
   ```
   DATABASE_URL=sqlite:///./app.db
   ```
4. Deploy from `main` branch
5. Note the public URL

### Option 2: Heroku (Full Stack)

**Prepare**
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Create runtime.txt
echo "python-3.11.6" > runtime.txt
```

**Deploy**
```bash
heroku login
heroku create your-app-name
git push heroku main
heroku open
```

### Option 3: AWS (EC2 + RDS)

**EC2 Setup**
```bash
# SSH into instance
ssh -i key.pem ec2-user@instance-ip

# Install dependencies
sudo yum update -y
sudo yum install python3.11 nodejs git -y

# Clone repo
git clone <url>
cd "Sip Friction Analyzer"

# Setup backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install
npm run build
cd ..

# Run with PM2
npm install -g pm2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name "sip-analyzer"
pm2 save
```

**RDS Integration**
```python
# Update database.py
DATABASE_URL = "postgresql://user:password@rds-endpoint:5432/sip_analyzer"
```

### Option 4: Google Cloud Run (Serverless)

```bash
# Build Docker image
docker build -t gcr.io/PROJECT_ID/sip-analyzer .

# Push to Container Registry
docker push gcr.io/PROJECT_ID/sip-analyzer

# Deploy to Cloud Run
gcloud run deploy sip-analyzer \
  --image gcr.io/PROJECT_ID/sip-analyzer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Environment Variables

**Production Frontend** (.env.production)
```
VITE_API_URL=https://api.yourdomain.com
VITE_ENABLE_MONTE_CARLO=true
VITE_ENABLE_INVESTOR_PROFILES=false
```

**Production Backend**
```
DATABASE_URL=postgresql://user:password@host:5432/sip_db
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Database Management

### Migrate from SQLite to PostgreSQL
```python
from sqlalchemy import create_engine
from models import Base
import json

# Read SQLite
sqlite_engine = create_engine("sqlite:///./app.db")


# Write to PostgreSQL
pg_engine = create_engine("postgresql://user:pass@host/db")
Base.metadata.create_all(bind=pg_engine)

# Migrate data
with sqlite_engine.connect() as conn:
    # Export and import data
    pass
```

---

## Performance Optimization

### Frontend
```bash
# Build analysis
npm run build -- --stats

# Code splitting
# Update vite.config.js:
rollupOptions: {
  output: {
    manualChunks: {
      'vendor': ['react', 'recharts'],
      'util': ['utils/formatINR.ts']
    }
  }
}
```

### Backend
```python
# Enable caching
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

---

## Monitoring

### Sentry (Error Tracking)
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    "https://key@sentry.io/project",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1
)
```

### Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

---

## Security Checklist

- [ ] Enable HTTPS in production
- [ ] Set `DEBUG=False`
- [ ] Configure CORS properly (not `*`)
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Add authentication to endpoints
- [ ] Validate all user inputs
- [ ] Use security headers
- [ ] Regular dependency updates
- [ ] Database backups automated

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest test_backend.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: npm install -g @railway/cli && railway deploy
```

---

## Cost Estimation (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Pro | $20 |
| Railway | Pay-as-you-go | $5-20 |
| PostgreSQL | Shared PostgreSQL | $12 |
| **Total** | | **$37-52** |

---

## Support

For deployment issues:
1. Check logs: `docker-compose logs backend`
2. Verify environment variables
3. Test API: `curl http://localhost:8000/docs`
4. Open GitHub Issue with:
   - Error message
   - Deployment platform
   - Steps to reproduce

