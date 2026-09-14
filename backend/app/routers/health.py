"""Health check endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Response, status
from sqlalchemy import text, select, func

from app.config import get_settings
from app.database import async_session_factory
from app.models import Customer
from app.agent.tools import get_policy_context

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(response: Response):
    """Health check endpoint for Docker healthcheck and monitoring."""
    settings = get_settings()

    # Check database connectivity and seed status
    db_status = "healthy"
    customers_seeded = 0
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            # Check customers seeded
            count_result = await session.execute(select(func.count()).select_from(Customer))
            customers_seeded = count_result.scalar() or 0
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error("health_check_db_failed", error=str(e))

    # Check LLM config
    llm_status = "healthy"
    if settings.groq_api_key == "your_groq_api_key_here" or not settings.groq_api_key:
        llm_status = "unconfigured"
        logger.error("health_check_llm_failed", error="GROQ_API_KEY not configured")
        
    # Check RAG
    rag_status = "healthy"
    from app.agent.rag import _searcher, _chunks
    if _searcher is None or not _chunks:
        rag_status = "unconfigured"

    is_healthy = db_status == "healthy" and rag_status == "healthy"
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": db_status,
        "llm": llm_status,
        "rag": rag_status,
        "customers_seeded": customers_seeded,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
