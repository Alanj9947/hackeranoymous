# HackerAnonymous AI Voice Agent Platform - Deployment Guide

## 🚀 PRODUCTION READY - PHASE 7 COMPLETE

**Last Updated**: 2026-03-04  
**Status**: ✅ All 8 Phases Complete (17,702 lines)  
**Latest Commit**: 5f2db44 (PHASE 7 TASKS 7.7 & 7.8 - NLP/Sentiment & Recommendations Engine)

---

## Project Summary

A comprehensive AI-powered voice agent platform built with:
- **Backend**: FastAPI (async, multi-tenant, 26 services, 114+ endpoints)
- **Frontend**: React (26 components, real-time updates)
- **Database**: PostgreSQL with Alembic migrations
- **Integrations**: Twilio, OpenAI GPT-4, Whisper, ElevenLabs, Salesforce, HubSpot, Jira, Zendesk

---

## Pre-Deployment Checklist

### Environment Requirements
- [ ] Python 3.10+
- [ ] Node.js 18+
- [ ] PostgreSQL 13+
- [ ] Redis (optional, for caching)
- [ ] Git

### Required API Keys
- [ ] Twilio Account SID & Auth Token
- [ ] OpenAI API Key (GPT-4 + Whisper)
- [ ] ElevenLabs API Key (TTS)
- [ ] Salesforce API credentials (optional)
- [ ] HubSpot API key (optional)
- [ ] Jira API token (optional)
- [ ] Zendesk API key (optional)

---

## Step 1: Environment Setup

### Clone Repository
```bash
git clone https://github.com/Alanj9947/hackeranoymous.git
cd hackeranoymous
```

### Backend Setup
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create .env file
cp backend/.env.example backend/.env

# Update .env with your values:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hackeranoymous
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
ELEVENLABS_API_KEY=...
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Update .env with backend URL
REACT_APP_API_URL=http://localhost:8000
```

---

## Step 2: Database Initialization

### Create Database
```bash
createdb hackeranoymous
```

### Run Migrations
```bash
cd backend
alembic upgrade head
```

### Verify Schema
```bash
psql hackeranoymous -c "\dt"
```

---

## Step 3: Start Services

### Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend (Terminal 2)
```bash
cd frontend
npm start
```

### Redis (Optional - Terminal 3)
```bash
redis-server
```

---

## Step 4: Verify Deployment

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-04T12:00:00Z",
  "uptime_seconds": 123
}
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend
- Open http://localhost:3000 in browser
- Login with test credentials

---

## Production Deployment

### Docker Deployment

#### Build Images
```bash
# Backend
docker build -f backend/Dockerfile -t hackeranoymous-backend:latest backend/

# Frontend
docker build -f frontend/Dockerfile -t hackeranoymous-frontend:latest frontend/
```

#### Docker Compose
```bash
docker-compose up -d
```

### Cloud Deployment (AWS Example)

#### Step 1: Push to ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com

docker tag hackeranoymous-backend:latest [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com/hackeranoymous-backend:latest
docker push [ACCOUNT].dkr.ecr.us-east-1.amazonaws.com/hackeranoymous-backend:latest
```

#### Step 2: ECS Task Definition
Create task definition with:
- Backend service (port 8000)
- Frontend service (port 3000)
- PostgreSQL RDS
- Application Load Balancer

#### Step 3: Deploy
```bash
aws ecs update-service --cluster hackeranoymous --service backend --force-new-deployment
```

---

## Configuration

### Backend Settings (`backend/.env`)

```dotenv
# App
ENVIRONMENT=production
DEBUG=false
APP_NAME=HackerAnonymous

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
ELEVENLABS_API_KEY=...

# Optional Integrations
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
HUBSPOT_API_KEY=...
JIRA_API_URL=...
JIRA_API_TOKEN=...
ZENDESK_SUBDOMAIN=...
ZENDESK_API_TOKEN=...

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
ALLOWED_HOSTS=localhost,yourdomain.com
```

### Frontend Settings (`frontend/.env`)

```dotenv
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
```

---

## API Endpoints Overview

### Authentication (4 endpoints)
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/verify` - Verify token
- `POST /api/v1/auth/logout` - Logout

### Agents (6 endpoints)
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/{id}` - Get agent
- `PUT /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent
- `GET /api/v1/agents/{id}/performance` - Agent stats

### Calls (8 endpoints)
- `GET /api/v1/calls` - List calls
- `POST /api/v1/calls` - Make call
- `GET /api/v1/calls/{id}` - Get call
- `GET /api/v1/calls/{id}/recording` - Download recording
- `GET /api/v1/calls/{id}/transcript` - Get transcript
- `POST /api/v1/calls/{id}/export` - Export call
- `GET /api/v1/calls/analytics/daily` - Daily analytics
- `GET /api/v1/calls/search` - Search calls

### Analytics (8 endpoints)
- `GET /api/v1/analytics/dashboard` - Dashboard metrics
- `GET /api/v1/analytics/calls` - Call analytics
- `GET /api/v1/analytics/agents` - Agent analytics
- `GET /api/v1/analytics/trends` - Trending data
- `GET /api/v1/analytics/health` - System health
- `GET /api/v1/analytics/reports/{id}` - Get report
- `POST /api/v1/analytics/reports` - Create report
- `GET /api/v1/analytics/export` - Export analytics

### CRM Integration (7 endpoints)
- `POST /api/v1/crm/configure` - Configure CRM
- `POST /api/v1/crm/disconnect` - Disconnect CRM
- `GET /api/v1/crm/status` - Get CRM status
- `GET /api/v1/crm/contacts` - List contacts
- `POST /api/v1/crm/contacts` - Create contact
- `GET /api/v1/crm/activity` - Get activities
- `POST /api/v1/crm/sync` - Sync data

### Ticketing (9 endpoints)
- `POST /api/v1/ticketing/configure` - Configure ticketing
- `GET /api/v1/ticketing/status` - Get status
- `GET /api/v1/ticketing/tickets` - List tickets
- `POST /api/v1/ticketing/tickets` - Create ticket
- `GET /api/v1/ticketing/tickets/{id}` - Get ticket
- `PUT /api/v1/ticketing/tickets/{id}` - Update ticket
- `POST /api/v1/ticketing/tickets/{id}/comment` - Add comment
- `POST /api/v1/ticketing/sync` - Sync tickets
- `PUT /api/v1/ticketing/tickets/{id}/status` - Update status

### Knowledge Base (6 endpoints)
- `POST /api/v1/knowledge-base/search` - Search docs
- `POST /api/v1/knowledge-base/documents` - Create doc
- `GET /api/v1/knowledge-base/documents` - List docs
- `GET /api/v1/knowledge-base/documents/{id}` - Get doc
- `PUT /api/v1/knowledge-base/documents/{id}` - Update doc
- `DELETE /api/v1/knowledge-base/documents/{id}` - Delete doc

### SMS Integration (8 endpoints)
- `POST /api/v1/sms/configure` - Configure SMS
- `GET /api/v1/sms/status` - Get status
- `POST /api/v1/sms/send` - Send SMS
- `GET /api/v1/sms/conversations` - List conversations
- `GET /api/v1/sms/conversations/{id}` - Get conversation
- `POST /api/v1/sms/conversations/{id}/send` - Send message
- `GET /api/v1/sms/contacts` - List contacts
- `GET /api/v1/sms/search` - Search messages

### Forecasting (6 endpoints)
- `POST /api/v1/forecasting/forecast` - Generate forecast
- `GET /api/v1/forecasting/anomalies` - Detect anomalies
- `POST /api/v1/forecasting/scenarios` - Create scenario
- `POST /api/v1/forecasting/what-if` - What-if analysis
- `GET /api/v1/forecasting/model-evaluation` - Model stats
- `GET /api/v1/forecasting/trends` - Get trends

### Workflows (9 endpoints)
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow
- `GET /api/v1/workflows/{id}/history` - Get history
- `GET /api/v1/workflows/templates` - List templates
- `PUT /api/v1/workflows/{id}/status` - Enable/disable

### NLP/Sentiment (6 endpoints)
- `POST /api/v1/nlp/sentiment` - Analyze sentiment
- `POST /api/v1/nlp/sentiment-batch` - Batch analysis
- `GET /api/v1/nlp/sentiment-trend` - Get trends
- `POST /api/v1/nlp/intent` - Extract intent
- `POST /api/v1/nlp/language-detect` - Detect language

### Recommendations (6 endpoints)
- `POST /api/v1/recommendations/analyze-agent/{id}` - Analyze agent
- `POST /api/v1/recommendations/analyze-team` - Analyze team
- `GET /api/v1/recommendations/agent/{id}` - Get recommendations
- `POST /api/v1/recommendations/{id}/accept` - Accept recommendation
- `POST /api/v1/recommendations/{id}/reject` - Reject recommendation
- `GET /api/v1/recommendations/agent/{id}/impact` - Get impact score

**Total: 114+ REST endpoints + 2 WebSocket endpoints**

---

## Monitoring & Logging

### Application Logs
```bash
# Tail backend logs
docker logs -f hackeranoymous-backend

# Tail frontend logs
docker logs -f hackeranoymous-frontend
```

### Database Monitoring
```bash
# Monitor connections
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Check slow queries
psql -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Sentry Integration
All errors automatically captured and sent to Sentry dashboard:
https://sentry.io/organizations/your-org/issues/

---

## Backup & Recovery

### Database Backup
```bash
pg_dump hackeranoymous > backup-$(date +%Y%m%d).sql
```

### Database Restore
```bash
psql hackeranoymous < backup-20260304.sql
```

### Automated Backups
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * pg_dump hackeranoymous > /backups/backup-$(date +\%Y\%m\%d).sql
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Test connection string
psql postgresql://user:password@localhost:5432/hackeranoymous
```

### API Key Issues
```bash
# Validate API keys
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" https://api.openai.com/v1/models
```

### Memory Issues
```bash
# Monitor memory usage
docker stats hackeranoymous-backend

# Increase Docker memory limit
# Edit docker-compose.yml:
# services:
#   backend:
#     mem_limit: 2g
```

---

## Performance Optimization

### Database Indexes
All critical indexes are created during migrations:
- `calls_company_id_idx` - Fast company filtering
- `conversations_agent_id_idx` - Agent lookups
- `documents_company_id_idx` - Knowledge base search

### Caching Strategy
- Redis caching layer (optional)
- API response caching (configurable TTL)
- Frontend client-side caching (React Query)

### Load Balancing
For multiple backend instances:
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location /api {
        proxy_pass http://backend;
    }
}
```

---

## Security Best Practices

### SSL/TLS Certificate
```bash
# Using Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Update nginx config
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

### Rate Limiting
Configured per endpoint:
- Authentication: 5 requests/minute
- API endpoints: 100 requests/minute
- File uploads: 10 MB max

### CORS Configuration
Only allow trusted origins in `CORS_ORIGINS`:
```
https://yourdomain.com,https://app.yourdomain.com
```

### Database Security
- Use strong passwords
- Enable SSL connections
- Restrict IP access
- Regular backups

---

## Support & Documentation

- **API Docs**: http://yourapi.com/docs
- **GitHub Issues**: https://github.com/Alanj9947/hackeranoymous/issues
- **Documentation**: See README.md in repository

---

**Deployment Status**: ✅ Ready for Production  
**Last Updated**: 2026-03-04  
**Version**: 1.0.0 (PHASE 7 Complete)
