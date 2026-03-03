"""
VPS AI Server – FastAPI application providing AI extraction endpoints
backed by Ollama (local LLM inference).
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# ─── Configuration ──────────────────────────────────────────

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "llama3.1:8b"
    api_key: str = "change-me-in-production"
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "info"
    max_concurrent_requests: int = 10
    request_timeout: int = 120

    class Config:
        env_file = ".env"


settings = Settings()

# ─── Logging ────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

# ─── Semaphore for concurrency control ──────────────────────

semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

# ─── Schemas ────────────────────────────────────────────────

class ExtractionRequest(BaseModel):
    transcript: str
    extraction_prompt: str
    fields: Dict[str, str] = Field(default_factory=dict)
    request_id: Optional[str] = ""


class ExtractionResponse(BaseModel):
    request_id: str
    extracted_data: Dict[str, Any]
    confidence_score: float
    model: str
    processing_time_ms: int


class SentimentRequest(BaseModel):
    transcript: str


class SentimentResponse(BaseModel):
    sentiment: str  # positive | negative | neutral | mixed
    confidence: float
    details: Dict[str, Any] = Field(default_factory=dict)
    model: str
    processing_time_ms: int


class BatchExtractionRequest(BaseModel):
    requests: List[ExtractionRequest]


class BatchExtractionResponse(BaseModel):
    batch_id: str
    results: List[ExtractionResponse]
    total_processing_time_ms: int


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    model_loaded: bool
    model_name: str
    uptime_seconds: int
    active_requests: int
    version: str = "1.0.0"


# ─── Helpers ────────────────────────────────────────────────

_start_time = time.monotonic()
_active_requests = 0


async def verify_api_key(authorization: str = Header(default="")):
    """Simple Bearer token auth."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def ollama_generate(prompt: str, system: str = "", temperature: float = 0.1) -> str:
    """Call Ollama /api/generate endpoint."""
    payload = {
        "model": settings.model_name,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 4096,
        },
    }
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        resp = await client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")


async def check_ollama() -> tuple[bool, bool]:
    """Check Ollama connectivity and model availability."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Check connectivity
            tags_resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if tags_resp.status_code != 200:
                return False, False
            models = [m["name"] for m in tags_resp.json().get("models", [])]
            model_loaded = settings.model_name in models or any(
                settings.model_name.split(":")[0] in m for m in models
            )
            return True, model_loaded
    except Exception:
        return False, False


def parse_json_from_llm(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM output, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"raw_text": text, "parse_error": True}


# ─── Lifespan ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    connected, loaded = await check_ollama()
    if connected:
        logger.info("ollama_connected", model_loaded=loaded, model=settings.model_name)
    else:
        logger.warning("ollama_not_reachable", url=settings.ollama_base_url)
    yield
    logger.info("shutting_down")


# ─── App ────────────────────────────────────────────────────

app = FastAPI(
    title="VPS AI Server",
    description="AI extraction server powered by Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routes ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint – no auth required."""
    connected, loaded = await check_ollama()
    return HealthResponse(
        status="healthy" if connected and loaded else "degraded",
        ollama_connected=connected,
        model_loaded=loaded,
        model_name=settings.model_name,
        uptime_seconds=int(time.monotonic() - _start_time),
        active_requests=_active_requests,
    )


@app.post("/extract-data", response_model=ExtractionResponse, dependencies=[Depends(verify_api_key)])
async def extract_data(req: ExtractionRequest):
    """Extract structured data from a call transcript using the local LLM."""
    global _active_requests

    async with semaphore:
        _active_requests += 1
        start = time.monotonic()

        try:
            # Build field instructions
            field_desc = "\n".join(f"- {k}: {v}" for k, v in req.fields.items()) if req.fields else "Extract all relevant fields."

            system_prompt = f"""You are a precise data extraction engine. Extract structured data from call transcripts.
Return ONLY valid JSON with the requested fields. If a field cannot be found, use null.
Also include a "confidence" field (0.0-1.0) indicating your confidence in the extraction.

{req.extraction_prompt}

Fields to extract:
{field_desc}"""

            user_prompt = f"Extract the requested data from this transcript:\n\n{req.transcript}"

            raw = await ollama_generate(user_prompt, system=system_prompt)
            data = parse_json_from_llm(raw)

            confidence = data.pop("confidence", 0.8)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    confidence = 0.5

            elapsed = int((time.monotonic() - start) * 1000)

            return ExtractionResponse(
                request_id=req.request_id or str(uuid.uuid4()),
                extracted_data=data,
                confidence_score=min(max(confidence, 0.0), 1.0),
                model=settings.model_name,
                processing_time_ms=elapsed,
            )
        except httpx.HTTPError as e:
            logger.error("ollama_error", error=str(e))
            raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")
        except Exception as e:
            logger.error("extraction_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            _active_requests -= 1


@app.post("/sentiment-analysis", response_model=SentimentResponse, dependencies=[Depends(verify_api_key)])
async def sentiment_analysis(req: SentimentRequest):
    """Analyze sentiment of a call transcript."""
    global _active_requests

    async with semaphore:
        _active_requests += 1
        start = time.monotonic()

        try:
            system_prompt = """Analyze the sentiment of this call transcript. 
Return ONLY valid JSON with these fields:
- "sentiment": one of "positive", "negative", "neutral", "mixed"
- "confidence": 0.0-1.0
- "customer_satisfaction": 1-10
- "agent_performance": 1-10
- "key_emotions": list of detected emotions
- "summary": brief sentiment summary"""

            raw = await ollama_generate(req.transcript, system=system_prompt)
            data = parse_json_from_llm(raw)

            sentiment = data.get("sentiment", "neutral")
            confidence = float(data.get("confidence", 0.7))
            elapsed = int((time.monotonic() - start) * 1000)

            return SentimentResponse(
                sentiment=sentiment,
                confidence=min(max(confidence, 0.0), 1.0),
                details=data,
                model=settings.model_name,
                processing_time_ms=elapsed,
            )
        except Exception as e:
            logger.error("sentiment_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            _active_requests -= 1


@app.post("/batch-extract", response_model=BatchExtractionResponse, dependencies=[Depends(verify_api_key)])
async def batch_extract(batch: BatchExtractionRequest):
    """Process multiple extractions in a batch."""
    batch_id = str(uuid.uuid4())
    start = time.monotonic()
    results = []

    for item in batch.requests:
        try:
            result = await extract_data(item)
            results.append(result)
        except HTTPException as e:
            results.append(
                ExtractionResponse(
                    request_id=item.request_id or str(uuid.uuid4()),
                    extracted_data={"error": e.detail},
                    confidence_score=0.0,
                    model=settings.model_name,
                    processing_time_ms=0,
                )
            )

    total_ms = int((time.monotonic() - start) * 1000)
    return BatchExtractionResponse(
        batch_id=batch_id,
        results=results,
        total_processing_time_ms=total_ms,
    )


# ─── Entry ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
