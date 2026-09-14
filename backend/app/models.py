"""SQLAlchemy ORM models for the NovaMart database."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────

class AccountTier(str, enum.Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"


class ProductCategory(str, enum.Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FURNITURE = "furniture"
    FOOD = "food"
    SOFTWARE = "software"
    JEWELRY = "jewelry"


class OrderStatus(str, enum.Enum):
    DELIVERED = "delivered"
    SHIPPED = "shipped"
    PROCESSING = "processing"
    CANCELLED = "cancelled"


class RefundDecision(str, enum.Enum):
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    PENDING = "pending"
    FLAGGED = "flagged"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


# ── Utility ────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ── Models ─────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    account_tier: Mapped[AccountTier] = mapped_column(
        Enum(AccountTier), nullable=False, default=AccountTier.STANDARD
    )
    delivery_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(back_populates="customer", lazy="selectin")
    refund_requests: Mapped[list["RefundRequest"]] = relationship(
        back_populates="customer", lazy="selectin"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    purchase_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_final_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_digital: Mapped[bool] = mapped_column(Boolean, default=False)
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.DELIVERED
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="orders", lazy="selectin")
    refund_requests: Mapped[list["RefundRequest"]] = relationship(
        back_populates="order", lazy="selectin"
    )


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False
    )
    request_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    decision: Mapped[RefundDecision] = mapped_column(
        Enum(RefundDecision), nullable=False, default=RefundDecision.PENDING
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    was_injection_attempt: Mapped[bool] = mapped_column(Boolean, default=False)
    is_replay: Mapped[bool] = mapped_column(Boolean, default=False)
    original_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="refund_requests", lazy="selectin")
    customer: Mapped["Customer"] = relationship(
        back_populates="refund_requests", lazy="selectin"
    )


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    negotiation_turn_count: Mapped[int] = mapped_column(Integer, default=0)
    negotiation_conceded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="session", lazy="selectin", order_by="ConversationMessage.created_at"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("conversation_sessions.id"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    session: Mapped["ConversationSession"] = relationship(
        back_populates="messages", lazy="selectin"
    )
