"""
Admin routes for logs, customers, stats, sessions, and replay.

All routes require the X-Admin-Key header for authentication.
The default demo key is "novamart-admin-2024" (set via ADMIN_API_KEY env var).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Query, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc

from app.database import async_session_factory
from app.models import (
    RefundRequest,
    RefundDecision,
    Customer,
    Order,
    ConversationSession,
    ConversationMessage,
)
from app.agent.graph import run_agent_streaming
from app.config import get_settings

logger = structlog.get_logger()


async def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Verify X-Admin-Key header matches the configured admin API key."""
    settings = get_settings()
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Provide the admin API key via the X-Admin-Key header.",
        )


router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.get("/logs")
async def get_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    decision: Optional[str] = Query(None),
):
    """Get refund request logs with optional decision filter."""
    async with async_session_factory() as db:
        query = select(RefundRequest).order_by(desc(RefundRequest.created_at))

        if decision:
            decision_enum = {
                "approved": RefundDecision.APPROVED,
                "denied": RefundDecision.DENIED,
                "escalated": RefundDecision.ESCALATED,
                "pending": RefundDecision.PENDING,
                "flagged": RefundDecision.FLAGGED,
            }.get(decision.lower())
            if decision_enum:
                query = query.where(RefundRequest.decision == decision_enum)

        # Get total count
        count_query = select(func.count()).select_from(RefundRequest)
        if decision:
            decision_enum_for_count = {
                "approved": RefundDecision.APPROVED,
                "denied": RefundDecision.DENIED,
                "escalated": RefundDecision.ESCALATED,
                "pending": RefundDecision.PENDING,
                "flagged": RefundDecision.FLAGGED,
            }.get(decision.lower())
            if decision_enum_for_count:
                count_query = count_query.where(RefundRequest.decision == decision_enum_for_count)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        requests = result.scalars().all()

        # Enrich with customer and order data
        logs = []
        for req in requests:
            # Fetch customer name
            customer_name = None
            if req.customer_id:
                cust_result = await db.execute(
                    select(Customer.name).where(Customer.id == req.customer_id)
                )
                customer_name = cust_result.scalar_one_or_none()

            # Fetch order details
            product_name = None
            amount = None
            if req.order_id:
                order_result = await db.execute(
                    select(Order.product_name, Order.amount).where(Order.id == req.order_id)
                )
                order_row = order_result.first()
                if order_row:
                    product_name = order_row[0]
                    amount = order_row[1]

            logs.append({
                "id": req.id,
                "order_id": req.order_id,
                "customer_id": req.customer_id,
                "customer_name": customer_name,
                "product_name": product_name,
                "amount": amount,
                "request_date": req.request_date.isoformat() if req.request_date else None,
                "decision": req.decision.value if hasattr(req.decision, 'value') else str(req.decision),
                "decision_reason": req.decision_reason,
                "agent_reasoning": req.agent_reasoning,
                "was_injection_attempt": req.was_injection_attempt,
                "is_replay": req.is_replay,
                "original_request_id": req.original_request_id,
                "session_id": req.session_id,
                "user_message": req.user_message,
                "created_at": req.created_at.isoformat() if req.created_at else None,
            })

        return {"logs": logs, "total": total, "limit": limit, "offset": offset}


@router.get("/customers")
async def get_customers():
    """Get all customers with their orders."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Customer).order_by(Customer.name)
        )
        customers = result.scalars().all()

        customer_list = []
        for c in customers:
            # Fetch orders for each customer
            orders_result = await db.execute(
                select(Order).where(Order.customer_id == c.id)
            )
            orders = orders_result.scalars().all()

            customer_list.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "account_tier": c.account_tier.value if hasattr(c.account_tier, 'value') else str(c.account_tier),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "orders": [
                    {
                        "id": o.id,
                        "product_name": o.product_name,
                        "product_category": o.product_category.value if hasattr(o.product_category, 'value') else str(o.product_category),
                        "amount": o.amount,
                        "currency": o.currency,
                        "purchase_date": o.purchase_date.isoformat() if o.purchase_date else None,
                        "is_final_sale": o.is_final_sale,
                        "is_digital": o.is_digital,
                        "order_status": o.order_status.value if hasattr(o.order_status, 'value') else str(o.order_status),
                        "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
                    }
                    for o in orders
                ],
            })

        return {"customers": customer_list}


@router.get("/stats")
async def get_stats():
    """Get aggregate refund request statistics."""
    async with async_session_factory() as db:
        total_result = await db.execute(
            select(func.count()).select_from(RefundRequest)
        )
        total = total_result.scalar() or 0

        # Count by decision
        stats = {}
        for decision in RefundDecision:
            count_result = await db.execute(
                select(func.count())
                .select_from(RefundRequest)
                .where(RefundRequest.decision == decision)
            )
            stats[decision.value] = count_result.scalar() or 0

        approval_rate = (
            (stats.get("approved", 0) / total * 100) if total > 0 else 0.0
        )

        return {
            "total_requests": total,
            "approved": stats.get("approved", 0),
            "denied": stats.get("denied", 0),
            "escalated": stats.get("escalated", 0),
            "flagged": stats.get("flagged", 0),
            "pending": stats.get("pending", 0),
            "approval_rate": round(approval_rate, 1),
        }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get full conversation history for a session."""
    async with async_session_factory() as db:
        # Get session
        result = await db.execute(
            select(ConversationSession).where(ConversationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"error": "Session not found", "session_id": session_id}

        # Get messages
        msg_result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at)
        )
        messages = msg_result.scalars().all()

        # Get refund requests for this session
        refund_result = await db.execute(
            select(RefundRequest)
            .where(RefundRequest.session_id == session_id)
            .order_by(RefundRequest.created_at)
        )
        refund_requests = refund_result.scalars().all()

        return {
            "session": {
                "id": session.id,
                "customer_id": session.customer_id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_active": session.last_active.isoformat() if session.last_active else None,
                "message_count": session.message_count,
            },
            "messages": [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "role": m.role.value if hasattr(m.role, 'value') else str(m.role),
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
            "refund_requests": [
                {
                    "id": r.id,
                    "order_id": r.order_id,
                    "decision": r.decision.value if hasattr(r.decision, 'value') else str(r.decision),
                    "decision_reason": r.decision_reason,
                    "agent_reasoning": r.agent_reasoning,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in refund_requests
            ],
        }


@router.get("/customers")
async def get_customers():
    """List all customers and their associated orders."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Customer).order_by(Customer.created_at.desc())
        )
        customers = result.scalars().all()
        
        return {
            "customers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "account_tier": c.account_tier.value if hasattr(c.account_tier, 'value') else str(c.account_tier),
                    "delivery_address": c.delivery_address,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "orders": [
                        {
                            "id": o.id,
                            "product_name": o.product_name,
                            "product_category": o.product_category.value if hasattr(o.product_category, 'value') else str(o.product_category),
                            "amount": o.amount,
                            "currency": o.currency,
                            "purchase_date": o.purchase_date.isoformat() if o.purchase_date else None,
                            "is_final_sale": o.is_final_sale,
                            "is_digital": o.is_digital,
                            "order_status": o.order_status.value if hasattr(o.order_status, 'value') else str(o.order_status),
                            "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
                        }
                        for o in c.orders
                    ]
                }
                for c in customers
            ]
        }


@router.get("/sessions")
async def get_sessions():
    """List all conversation sessions."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(ConversationSession).order_by(desc(ConversationSession.last_active))
        )
        sessions = result.scalars().all()

        session_list = []
        for s in sessions:
            # Get customer name if linked
            customer_name = None
            if s.customer_id:
                cust_result = await db.execute(
                    select(Customer.name).where(Customer.id == s.customer_id)
                )
                customer_name = cust_result.scalar_one_or_none()

            session_list.append({
                "id": s.id,
                "customer_id": s.customer_id,
                "customer_name": customer_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_active": s.last_active.isoformat() if s.last_active else None,
                "message_count": s.message_count,
            })

        return {"sessions": session_list}


@router.post("/replay/{request_id}")
async def replay_request(request_id: str):
    """
    Re-run the original user message through the agent fresh.
    Returns an SSE stream with the new reasoning chain.
    """
    async with async_session_factory() as db:
        # Find the original request
        result = await db.execute(
            select(RefundRequest).where(RefundRequest.id == request_id)
        )
        original = result.scalar_one_or_none()

        if not original:
            return {"error": "Request not found", "request_id": request_id}

        user_message = original.user_message
        if not user_message:
            return {"error": "Original message not found — cannot replay"}

        session_id = f"replay-{str(uuid.uuid4())[:8]}"

    async def event_generator():
        final_state = None

        try:
            async for event in run_agent_streaming(
                user_message=user_message,
                session_id=session_id,
                conversation_history=[],
                customer_name_hint=None,
                customer_id=original.customer_id,
            ):
                event_type = event.get("event", "step")
                data = event.get("data", {})

                if event_type == "_state":
                    final_state = data
                    continue

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        except Exception as e:
            logger.error("replay_error", error=str(e), request_id=request_id)
            yield f"event: step\ndata: {json.dumps({'step': 'error', 'status': 'failed', 'detail': str(e)})}\n\n"

        # Persist replay result
        if final_state:
            try:
                async with async_session_factory() as db2:
                    from app.models import RefundDecision as RD
                    decision_val = final_state.get("decision", "pending")
                    decision_enum = {
                        "approved": RD.APPROVED,
                        "denied": RD.DENIED,
                        "escalated": RD.ESCALATED,
                        "pending_delivery": RD.PENDING,
                        "pending": RD.PENDING,
                        "flagged": RD.FLAGGED,
                    }.get(decision_val, RD.PENDING)

                    replay_req = RefundRequest(
                        id=final_state.get("request_id", str(uuid.uuid4())),
                        order_id=original.order_id,
                        customer_id=original.customer_id,
                        request_date=datetime.now(timezone.utc),
                        decision=decision_enum,
                        decision_reason=final_state.get("decision_reason"),
                        agent_reasoning={
                            "reasoning_steps": final_state.get("reasoning_steps", []),
                            "policy_result": final_state.get("policy_result"),
                            "injection_result": final_state.get("injection_result"),
                            "original_request_id": request_id,
                        },
                        was_injection_attempt=final_state.get("decision") == "flagged",
                        is_replay=True,
                        original_request_id=request_id,
                        session_id=session_id,
                        user_message=user_message,
                        created_at=datetime.now(timezone.utc),
                    )
                    db2.add(replay_req)
                    await db2.commit()
            except Exception as e:
                logger.error("replay_persist_error", error=str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/policy")
async def get_policy():
    """Get the current NovaMart Refund Policy."""
    return {
        "version": "2.4",
        "last_updated": "2024-03-01",
        "rules": [
            {"id": "R01_FINAL_SALE", "description": "Final sale items are non-refundable."},
            {"id": "R02_DIGITAL_PRODUCT", "description": "Digital products cannot be refunded once delivered."},
            {"id": "R03_FOOD_PERISHABLE", "description": "Perishable items cannot be returned."},
            {"id": "R04_CANCELLED_ORDER", "description": "Order was already cancelled; no payment to refund."},
            {"id": "R05_UNDELIVERED", "description": "Order is currently in transit. We cannot process a refund until delivered."},
            {"id": "R06_MISSING_DELIVERY_DATE", "description": "Delivery date is missing despite order showing as delivered."},
            {"id": "R07_PAST_RETURN_WINDOW", "description": "Our return window is 30 days from delivery."},
            {"id": "R08_HIGH_VALUE", "description": "Refund requests over $500 require review by a senior specialist."},
            {"id": "R09_HIGH_VALUE_JEWELRY", "description": "Jewelry items over $1000 require human inspection and approval."},
            {"id": "R10_VIP_BORDERLINE", "description": "As a VIP customer, your borderline case has been escalated for priority review."},
            {"id": "R11_LOW_CONFIDENCE", "description": "Multiple factors in your case are close to policy thresholds. Escalating."},
            {"id": "R12_ALL_PASS", "description": "Your refund has been approved."},
        ]
    }

@router.get('/customer/{customer_id}')
async def get_customer_details(customer_id: str):
    """Get detailed profile of a specific customer."""
    from sqlalchemy import select
    from app.models import Customer, Order, RefundRequest
    async with async_session_factory() as db:
        # Get customer
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail='Customer not found')
            
        # Get orders
        orders_result = await db.execute(select(Order).where(Order.customer_id == customer_id).order_by(Order.purchase_date.desc()))
        orders = orders_result.scalars().all()
        
        # Get refund history
        refunds_result = await db.execute(select(RefundRequest).where(RefundRequest.customer_id == customer_id).order_by(RefundRequest.created_at.desc()))
        refunds = refunds_result.scalars().all()
        
        return {
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'account_tier': customer.account_tier.value if hasattr(customer.account_tier, 'value') else str(customer.account_tier),
                'delivery_address': customer.delivery_address,
                'total_spent': sum(float(o.amount) for o in orders),
                'joined_at': customer.created_at.isoformat() if customer.created_at else None,
            },
            'orders': [
                {
                    'id': o.id,
                    'product_name': o.product_name,
                    'amount': float(o.amount) if o.amount else 0,
                    'purchase_date': o.purchase_date.isoformat() if o.purchase_date else None,
                    'order_status': o.order_status.value if hasattr(o.order_status, 'value') else str(o.order_status),
                    'delivered_at': o.delivered_at.isoformat() if o.delivered_at else None,
                }
                for o in orders
            ],
            'refunds': [
                {
                    'id': r.id,
                    'order_id': r.order_id,
                    'decision': r.decision.value if hasattr(r.decision, 'value') else str(r.decision),
                    'decision_reason': r.decision_reason,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                }
                for r in refunds
            ]
        }
