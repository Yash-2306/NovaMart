"""
Chat router — SSE streaming endpoint for the refund agent.

POST /api/chat/stream → text/event-stream
"""



import json
import uuid
import time
import asyncio
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.main import limiter

from app.database import async_session_factory
from app.models import (
    ConversationMessage,
    ConversationSession,
    MessageRole,
    RefundRequest,
    RefundDecision,
)
from app.schemas import ChatRequest
from app.agent.graph import run_agent_streaming

logger = structlog.get_logger()

router = APIRouter(tags=["chat"])



async def _get_or_create_session(session_id: str):
    """Get or create a conversation session. Returns (session, messages)."""
    async with async_session_factory() as db:
        from sqlalchemy import select

        result = await db.execute(
            select(ConversationSession).where(ConversationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            session = ConversationSession(
                id=session_id,
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc),
                message_count=0,
                negotiation_turn_count=0,
                negotiation_conceded=False,
            )
            db.add(session)
            from sqlalchemy.exc import IntegrityError
            try:
                await db.commit()
                return session, []
            except IntegrityError:
                await db.rollback()
                result = await db.execute(
                    select(ConversationSession).where(ConversationSession.id == session_id)
                )
                session = result.scalar_one_or_none()
                # Assume empty history since it was just created concurrently and messages are saved after streaming
                return session, []

        # Load conversation history
        msg_result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at)
        )
        messages = msg_result.scalars().all()
        history = [
            {"role": m.role.value if hasattr(m.role, 'value') else m.role, "content": m.content}
            for m in messages
        ]
        return session, history


async def _persist_conversation(
    session_id: str,
    user_message: str,
    assistant_response: str,
    state: dict,
):
    """Persist conversation messages and refund request to DB."""
    async with async_session_factory() as db:
        from sqlalchemy import select

        now = datetime.now(timezone.utc)

        # Get session
        result = await db.execute(
            select(ConversationSession).where(ConversationSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.last_active = now
            session.message_count = (session.message_count or 0) + 2
            if state.get("customer_id"):
                session.customer_id = state["customer_id"]
            if "negotiation_turn_count" in state:
                session.negotiation_turn_count = state.get("negotiation_turn_count", 0)
            if "negotiation_conceded" in state:
                session.negotiation_conceded = state.get("negotiation_conceded", False)

        # Save user message
        db.add(ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            created_at=now,
        ))

        # Save assistant message
        db.add(ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_response,
            created_at=now,
        ))

        # Save refund request if a decision was made
        decision = state.get("decision")
        if decision and decision not in (None, "None") and state.get("order_id"):
            decision_enum = {
                "approved": RefundDecision.APPROVED,
                "denied": RefundDecision.DENIED,
                "escalated": RefundDecision.ESCALATED,
                "pending_delivery": RefundDecision.PENDING,
                "pending": RefundDecision.PENDING,
                "flagged": RefundDecision.FLAGGED,
            }.get(decision, RefundDecision.PENDING)

            refund = RefundRequest(
                id=state.get("request_id", str(uuid.uuid4())),
                order_id=state["order_id"],
                customer_id=state.get("customer_id") or "unknown",
                request_date=now,
                decision=decision_enum,
                decision_reason=state.get("decision_reason"),
                agent_reasoning={
                    "reasoning_steps": state.get("reasoning_steps", []),
                    "policy_result": state.get("policy_result"),
                    "injection_result": state.get("injection_result"),
                },
                was_injection_attempt=state.get("decision") == "flagged",
                session_id=session_id,
                user_message=user_message,
                created_at=now,
            )
            db.add(refund)

        await db.commit()


@router.post("/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, payload: ChatRequest):
    """
    SSE streaming endpoint for chat with the refund agent.

    Streams step events, token events, and a final done event.
    """
    message = payload.message.strip()

    # Validate empty/whitespace message
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id

    # Get session and history
    session, conversation_history = await _get_or_create_session(session_id)

    # Re-hydrate negotiation and clarification state from the last refund request in this session
    negotiation_turn_count = session.negotiation_turn_count if session else 0
    negotiation_conceded = session.negotiation_conceded if session else False
    previous_clarification = False
    async with async_session_factory() as db:
        from sqlalchemy import select, desc
        last_req_result = await db.execute(
            select(RefundRequest)
            .where(RefundRequest.session_id == session_id)
            .order_by(desc(RefundRequest.created_at))
            .limit(1)
        )
        last_req = last_req_result.scalar_one_or_none()
        if last_req and last_req.agent_reasoning:
            if isinstance(last_req.agent_reasoning, dict):
                # We don't want to carry negotiation state across different intent paths (e.g. they switch to asking about a different order).
                # The state was stored inside agent_reasoning
                steps = last_req.agent_reasoning.get("reasoning_steps", [])
                for step in steps:
                    if step.get("step") == "respond":
                        inp = step.get("input", {})
                        if inp.get("decision") == "clarification":
                            previous_clarification = True
        
        # If the last decision was a denial, this turn is a negotiation turn
        if last_req and last_req.decision == RefundDecision.DENIED and not previous_clarification:
            negotiation_turn_count += 1

    # Load customer_id from the session so the agent remembers the user's selection
    customer_id = getattr(payload, 'customer_id', None) or (session.customer_id if session else None)

    async def event_generator():
        """Generate SSE events."""
        final_state = None
        done_sent = False

        try:
            async for event in run_agent_streaming(
                user_message=message,
                session_id=session_id,
                conversation_history=conversation_history,
                customer_name_hint=payload.customer_name,
                customer_id=customer_id,
                negotiation_turn_count=negotiation_turn_count,
                negotiation_conceded=negotiation_conceded,
                previous_clarification=previous_clarification,
            ):
                event_type = event.get("event", "step")
                data = event.get("data", {})

                # Internal state event — don't send to client
                if event_type == "_state":
                    final_state = data
                    continue
                
                if event_type == "done":
                    done_sent = True

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        except asyncio.CancelledError:
            logger.warning("streaming_cancelled", session_id=session_id)
            # The connection was closed by the client
            return
        except Exception as e:
            logger.error("streaming_error", error=str(e), session_id=session_id)
            error_data = {
                "step": "error",
                "status": "failed",
                "detail": "Our support system is temporarily unavailable. Please try again in a moment.",
            }
            yield f"event: step\ndata: {json.dumps(error_data)}\n\n"

        finally:
            if not done_sent:
                decision = final_state.get("decision") if final_state else None
                req_id = final_state.get("request_id") if final_state else None
                yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'decision': decision, 'request_id': req_id})}\n\n"
            
            # Persist conversation after streaming completes
            if final_state:
                try:
                    await _persist_conversation(
                        session_id=session_id,
                        user_message=final_state.get("clean_message", message),
                        assistant_response=final_state.get("final_response") or "An error occurred.",
                        state=final_state,
                    )
                except Exception as e:
                    logger.error("persist_error", error=str(e), session_id=session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
