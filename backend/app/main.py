"""
FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.redis import close_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    setup_logging()

    # Init Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

    yield

    # Shutdown
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Voice Agent Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.ENVIRONMENT == "production":
        allowed = [h.strip() for h in settings.ALLOWED_HOSTS.split(",")]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)

    # ── Routes ─────────────────────────────────────────────
    from app.api.routes import (
        auth,
        agents,
        calls,
        extraction,
        exports,
        custom_server,
        webhooks,
        health,
        conversation,
        phone_numbers,
        twilio_webhooks,
        analytics,
        analytics_ws,
        predictions,
        coaching,
        alerts,
        reports,
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(calls.router, prefix="/api/v1")
    app.include_router(extraction.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")
    app.include_router(custom_server.router, prefix="/api/v1")
    app.include_router(conversation.router, prefix="/api/v1")
    app.include_router(phone_numbers.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(alerts.router)  # alerts endpoints
    app.include_router(reports.router)  # reports endpoints
    app.include_router(analytics_ws.router)  # analytics WebSocket endpoint
    app.include_router(predictions.router)  # predictions endpoints
    app.include_router(coaching.router)  # coaching endpoints
    app.include_router(webhooks.router)  # legacy Twilio webhooks
    app.include_router(twilio_webhooks.router)  # enhanced inbound call handling

    # ── WebSocket for phone media streaming ──────────────────────
    from app.services.phone_media_stream import phone_media_stream_ws

    app.add_api_websocket_route("/ws/media-stream/{call_id}", phone_media_stream_ws)

    return app


app = create_app()
