"""Pydantic v2 schemas for API request/response serialization."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)
    customer_name: str | None = Field(None, description="Optional customer name hint")


# ── Response Schemas ───────────────────────────────────────────────────

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    account_tier: str
    delivery_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    product_name: str
    product_category: str
    amount: float
    currency: str
    purchase_date: datetime
    is_final_sale: bool
    is_digital: bool
    order_status: str
    delivered_at: datetime | None

    class Config:
        from_attributes = True


class CustomerWithOrdersResponse(BaseModel):
    id: str
    name: str
    email: str
    account_tier: str
    created_at: datetime
    orders: list[OrderResponse] = []

    class Config:
        from_attributes = True


class RuleEvaluated(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    value_checked: Any
    triggered: bool
    outcome: str
    weight: float


class PolicyResult(BaseModel):
    decision: str
    reason: str
    rule_applied: str
    confidence: float
    days_since_delivery: int | None
    amount: float
    rules_evaluated: list[RuleEvaluated]
    overrides_checked: list[str]
    partial_refund_requested: bool = False
    policy_version: str = "2.4"


class ReasoningStep(BaseModel):
    step: str
    tool: str | None = None
    input: dict[str, Any] = {}
    output: dict[str, Any] = {}
    timestamp: str
    duration_ms: int


class RefundRequestResponse(BaseModel):
    id: str
    order_id: str
    customer_id: str
    request_date: datetime
    decision: str
    decision_reason: str | None
    agent_reasoning: dict | None
    was_injection_attempt: bool
    is_replay: bool = False
    original_request_id: str | None = None
    session_id: str | None = None
    user_message: str | None = None
    created_at: datetime
    customer_name: str | None = None
    product_name: str | None = None
    amount: float | None = None

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_requests: int
    approved: int
    denied: int
    escalated: int
    flagged: int
    pending: int
    approval_rate: float


class ConversationMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: str
    customer_id: str | None
    created_at: datetime
    last_active: datetime
    message_count: int

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[ConversationMessageResponse]
    refund_requests: list[RefundRequestResponse] = []


class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str
    timestamp: datetime


# ── SSE Event Schemas ──────────────────────────────────────────────────

class SSEStepEvent(BaseModel):
    """An SSE step event sent during agent processing."""
    step: str
    status: str
    detail: str | None = None
    risk_score: float | None = None
    decision: str | None = None
    reason: str | None = None
    rules_evaluated: list[dict] | None = None
    confidence: float | None = None
    sections_retrieved: int | None = None


class SSETokenEvent(BaseModel):
    """An SSE token event for streaming response."""
    token: str


class SSEDoneEvent(BaseModel):
    """An SSE done event when processing is complete."""
    request_id: str | None = None
    decision: str | None = None
    session_id: str
