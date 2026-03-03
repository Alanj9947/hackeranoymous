# AI Voice Agent Platform

Enterprise SaaS platform for creating, deploying, and managing AI-powered voice agents with intelligent data extraction and automatic export to business tools.

## Architecture

- **Backend**: FastAPI (Python 3.11+) + PostgreSQL + Redis + Celery
- **Frontend**: React 18 + Vite + Tailwind CSS + shadcn/ui
- **AI Server**: FastAPI + Ollama (deployed on dedicated Ubuntu VPS)
- **Telephony**: Twilio Voice API
- **AI**: OpenAI Whisper (STT), GPT-4 (conversation), ElevenLabs/Azure (TTS)

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker compose up --build

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Seed demo data (optional)
docker compose exec backend python -m app.scripts.seed

# 5. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Flower (Celery monitor): http://localhost:5555
```

## Project Structure

```
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security, deps
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── clients/       # External API clients
│   │   ├── worker/        # Celery tasks
│   │   └── scripts/       # Utility scripts
│   ├── alembic/           # DB migrations
│   ├── tests/
│   └── Dockerfile
├── frontend/              # React SPA
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── hooks/
│   └── Dockerfile
├── vps_ai_server/         # Custom AI extraction server
│   ├── app/
│   └── deploy.sh
├── docker-compose.yml
└── .env.example
```

## Environment Variables

See `.env.example` for all required configuration.

## Production Deployment

### 1. Main Platform (Docker Compose)

```bash
# On your server:
git clone <repo-url> voice-agent && cd voice-agent
cp .env.example .env
# Edit .env with production values (strong secrets, real API keys)

# Launch
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost:8000/api/v1/health
```

### 2. VPS AI Server (Ubuntu)

```bash
# On your Ubuntu VPS:
cd vps_ai_server
chmod +x deploy.sh
./deploy.sh

# Edit the API key:
sudo nano /opt/vps-ai-server/.env
sudo systemctl restart vps-ai-server

# Verify
curl http://localhost:8100/health
```

### 3. Connect VPS to Platform

1. Open the frontend → **Settings**
2. Enter your VPS endpoint (e.g., `http://YOUR_VPS_IP:8100`)
3. Enter the API key you set on the VPS
4. Click **Save** and verify the health status shows "healthy"

### 4. Configure Twilio

1. Set `TWILIO_WEBHOOK_BASE_URL` in `.env` to your public URL
2. In Twilio Console, set your phone number's Voice webhook to:
   `https://your-domain.com/api/v1/webhooks/voice`
3. Set the Status Callback URL to:
   `https://your-domain.com/api/v1/webhooks/status`

### Demo Credentials

After running the seed script:
- **Email**: admin@demo.com
- **Password**: demo1234

## License

Proprietary - All rights reserved.
