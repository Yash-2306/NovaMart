"""
Agent tools for database lookups and policy evaluation.

These are async functions used by the agent to fetch
customer/order data and evaluate policies.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select, or_

from app.database import async_session_factory
from app.models import Customer, Order
from app.agent.policy_engine import evaluate_refund_policy as _evaluate_policy
from app.agent.rag import retrieve_policy_context as _retrieve_context

logger = structlog.get_logger()


def _customer_to_dict(customer: Customer) -> dict[str, Any]:
    """Convert a Customer ORM object to a dict."""
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "account_tier": customer.account_tier.value if hasattr(customer.account_tier, 'value') else str(customer.account_tier),
        "delivery_address": customer.delivery_address,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


def _order_to_dict(order: Order) -> dict[str, Any]:
    """Convert an Order ORM object to a dict."""
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "product_name": order.product_name,
        "product_category": order.product_category.value if hasattr(order.product_category, 'value') else str(order.product_category),
        "amount": order.amount,
        "currency": order.currency,
        "purchase_date": order.purchase_date.isoformat() if order.purchase_date else None,
        "is_final_sale": order.is_final_sale,
        "is_digital": order.is_digital,
        "order_status": order.order_status.value if hasattr(order.order_status, 'value') else str(order.order_status),
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
    }


async def get_customer_by_id(customer_id: str) -> dict[str, Any]:
    """Fetch a customer by their UUID."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer is None:
            return {"error": "Customer not found", "customer_id": customer_id}
        return _customer_to_dict(customer)


async def search_customer(query: str) -> list[dict[str, Any]]:
    """Search customers by name or email (case-insensitive partial match)."""
    async with async_session_factory() as session:
        search_term = f"%{query}%"
        result = await session.execute(
            select(Customer).where(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.email.ilike(search_term),
                )
            )
        )
        customers = result.scalars().all()
        return [_customer_to_dict(c) for c in customers]


async def get_order_by_id(order_id: str) -> dict[str, Any]:
    """Fetch an order by its UUID, including customer info."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            return {"error": "Order not found", "order_id": order_id}

        order_dict = _order_to_dict(order)

        # Also fetch customer info
        cust_result = await session.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        if customer:
            order_dict["customer"] = _customer_to_dict(customer)

        return order_dict


async def get_order_by_id_for_customer(order_id: str, customer_id: str) -> dict[str, Any]:
    """
    Fetch an order by UUID, validated to belong to the given customer.

    This enforces ownership at the tool boundary rather than relying on
    callers to perform the check after fetching. If the order exists but
    belongs to a different customer, an error dict is returned with
    error="order_ownership_violation" so the caller can log and handle it
    without revealing that the order exists at all.
    """
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            return {"error": "Order not found", "order_id": order_id}

        if str(order.customer_id) != str(customer_id):
            return {
                "error": "order_ownership_violation",
                "order_id": order_id,
                "detail": "Order does not belong to the identified customer",
            }

        return _order_to_dict(order)


async def get_orders_for_customer(customer_id: str) -> list[dict[str, Any]]:
    """Get all orders for a customer."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order).where(Order.customer_id == customer_id)
        )
        orders = result.scalars().all()
        return [_order_to_dict(o) for o in orders]


async def run_policy_evaluation(order: dict, customer: dict) -> dict:
    """
    Run the deterministic policy engine.
    Wrapper around policy_engine.evaluate_refund_policy.
    """
    return _evaluate_policy(order, customer)


def get_policy_context(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieve relevant policy sections via RAG.
    Wrapper around rag.retrieve_policy_context.
    """
    return _retrieve_context(query, top_k=top_k)

from functools import lru_cache

@lru_cache(maxsize=1)
def _get_groq_client() -> "AsyncGroq":
    from app.config import get_settings
    from groq import AsyncGroq
    settings = get_settings()
    return AsyncGroq(api_key=settings.groq_api_key)

async def classify_return_reason(reason: str) -> dict:
    """Classify customer's return reason using fast LLM."""
    from app.config import get_settings
    settings = get_settings()
    client = _get_groq_client()
    
    response = await client.chat.completions.create(
        model=settings.groq_fast_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the customer's return reason into exactly one category. "
                    "Reply with ONLY one word — no explanation:\n"
                    "- defective (item was broken, damaged, not working, faulty)\n"
                    "- wrong_item (wrong product, wrong size, wrong color shipped)\n"
                    "- buyer_remorse (changed mind, doesn't fit lifestyle, didn't like it)\n"
                    "- no_reason (no reason given or reason is unclear)"
                )
            },
            {"role": "user", "content": reason}
        ],
        temperature=0,
        max_tokens=5,
    )
    
    category = response.choices[0].message.content.strip().lower()
    if category not in ("defective", "wrong_item", "buyer_remorse", "no_reason"):
        category = "no_reason"
    
    return {
        "category": category,
        "should_escalate_override": category in ("defective", "wrong_item"),
        "explanation": {
            "defective": "Item may have a manufacturing defect — warrants escalation regardless of return window",
            "wrong_item": "Wrong item shipped — escalate for investigation",
            "buyer_remorse": "Customer changed their mind — standard policy applies",
            "no_reason": "No specific reason given — standard policy applies",
        }.get(category, "")
    }