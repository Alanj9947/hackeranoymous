# VPS AI Server
# FastAPI server running on Ubuntu VPS with Ollama for AI model inference.

## Quick Start

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull the model
ollama pull llama3.1:8b

# 3. Install Python deps
pip install -r requirements.txt

# 4. Copy env file and configure
cp .env.example .env

# 5. Run
uvicorn main:app --host 0.0.0.0 --port 8100
```

## Endpoints

| Method | Path                | Description                    |
|--------|---------------------|--------------------------------|
| GET    | /health             | Health check & model status    |
| POST   | /extract-data       | Extract structured data        |
| POST   | /sentiment-analysis | Analyze transcript sentiment   |
| POST   | /batch-extract      | Batch extraction job           |

## Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```
