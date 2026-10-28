"""
FastAPI application entry point.

- Lifespan: seeds DB, initializes RAG
- Mounts routers under /api
- Configures CORS, structured logging, global exception handling
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

from app.config import get_settings, setup_logging
from app.database import init_db, close_db
from app.seed import seed_database
from app.agent.rag import initialize_rag
from app.routers import chat, admin, health

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    setup_logging(settings)

    logger.info("application_starting", environment=settings.environment)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    # Seed database if empty
    await seed_database()

    # Initialize RAG index
    initialize_rag()
    logger.info("rag_index_initialized")

    logger.info("application_ready", port=8000)

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()


# ── App Creation ───────────────────────────────────────────────────────

app = FastAPI(
    title="NovaMart AI Refund Agent",
    description="AI-powered customer support agent for processing e-commerce refunds",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware ─────────────────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    structlog.contextvars.clear_contextvars()
    return response

# ── CORS ───────────────────────────────────────────────────────────────

# Read allowed origins from environment so that Vercel/Netlify preview URLs
# and any custom domain can be whitelisted at deploy time.
# CORS_ORIGINS env var: comma-separated list of allowed origins.
# Defaults include localhost (Docker/local) and wildcard for *.vercel.app.
_default_origins = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost:5173",
]
_env_origins = os.getenv("CORS_ORIGINS", "")
_extra_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
_allowed_origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────

app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(admin.router, prefix="/api/admin")


# ── Global Exception Handler ──────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler returning structured JSON."""
    request_id = str(uuid.uuid4())
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        path=str(request.url),
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again.",
            "request_id": request_id,
        },
    )
