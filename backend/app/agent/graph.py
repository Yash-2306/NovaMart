"""
Groq Tool-Calling Agent Loop for refund processing.

Replaces the previous deterministic graph pipeline with a dynamic agent
that uses Groq's tool-calling capabilities.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import structlog
import asyncio
from groq import AsyncGroq, APIConnectionError, RateLimitError, APIStatusError

from app.config import get_settings
from app.agent.guardrails import check_guardrails
from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools import (
    get_customer_by_id,
    get_orders_for_customer,
    get_order_by_id,
    run_policy_evaluation,
    search_customer,
    get_policy_context,
    classify_return_reason,
)

logger = structlog.get_logger()

from functools import lru_cache

@lru_cache(maxsize=1)
def _get_groq_client() -> AsyncGroq:
    settings = get_settings()
    return AsyncGroq(api_key=settings.groq_api_key)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_customer",
            "description": "Search for a customer in the NovaMart database by their name or email address. Returns a list of matching customer profiles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's name or email to search for"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders_for_customer",
            "description": "Retrieve all orders placed by a specific customer using their customer ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's UUID"
                    }
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_refund_policy",
            "description": "Run the deterministic NovaMart refund policy engine (rules R01-R12) against a specific order and customer. Returns the refund decision (approved/denied/escalated/pending), the rule that was triggered, and the confidence score. ALWAYS call this before generating a final refund decision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string"
                    },
                    "customer_id": {
                        "type": "string"
                    }
                },
                "required": ["order_id", "customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy_docs",
            "description": "Search the NovaMart refund policy document for relevant sections. Use this to find policy text that supports or explains a refund decision to the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "what policy information you need"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "classify_return_reason",
            "description": "Classify the customer's stated reason for returning an item. Returns one of: 'defective', 'wrong_item', 'buyer_remorse', 'no_reason'. If defective or wrong_item, this should influence escalation even if other policy rules would deny.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The customer's stated return reason"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grant_concession",
            "description": "Offer a concession (e.g., $50 Store Credit) to a VIP or Premium customer who is unhappy with a denied refund. Only use this if the policy was denied, the customer pushes back, and you have verified their tier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "concession_type": {
                        "type": "string",
                        "description": "The type of concession, e.g. '$50 Store Credit'"
                    }
                },
                "required": ["concession_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "offer_refund_method",
            "description": "Offer the customer a choice of refund methods (e.g. ['store_credit', 'original_payment']). Call this when a refund is APPROVED, or for Premium users receiving compensation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "methods": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of methods to offer, e.g. ['store_credit', 'original_payment']"
                    }
                },
                "required": ["methods"]
            }
        }
    }
]

async def _execute_tool(tool_name: str, tool_args: dict, state: dict) -> dict:
    if tool_name == "search_customer":
        return {"customers": await search_customer(tool_args.get("query", ""))}
    elif tool_name == "get_orders_for_customer":
        customer_id = tool_args.get("customer_id", "")
        # Validate customer exists to prevent LLM from hallucinating UUIDs
        customer = await get_customer_by_id(customer_id)
        if "error" in customer:
            return {"error": "Invalid customer_id. You MUST call search_customer first to find the correct customer_id."}
        return {"orders": await get_orders_for_customer(customer_id)}
    elif tool_name == "evaluate_refund_policy":
        order_id = tool_args.get("order_id", "")
        customer_id = tool_args.get("customer_id", "")
        
        order_dict = await get_order_by_id(order_id)
        if "error" in order_dict:
            return {"error": f"Order {order_id} not found"}
        
        # Fetch customer directly — don't rely on the order's embedded customer
        customer_dict = await get_customer_by_id(customer_id)
        if "error" in customer_dict:
            return {"error": f"Customer {customer_id} not found"}
            
        result = await run_policy_evaluation(order_dict, customer_dict)
        state["policy_result"] = result
        if state.get("decision") != "escalated":
            state["decision"] = result["decision"]
            state["decision_reason"] = result["reason"]
        state["order_id"] = order_id
        state["customer_id"] = customer_id
        return result
    elif tool_name == "search_policy_docs":
        sections = get_policy_context(tool_args.get("query", ""), top_k=2)
        return {"sections": sections}
    elif tool_name == "classify_return_reason":
        res = await classify_return_reason(tool_args.get("reason", ""))
        if res.get("should_escalate_override"):
            state["decision"] = "escalated"
            state["decision_reason"] = "Customer reported item is defective or wrong item shipped. Escalating to human agent."
        return res
    elif tool_name == "grant_concession":
        state["negotiation_conceded"] = True
        return {"status": "success", "message": f"Concession '{tool_args.get('concession_type')}' has been officially granted."}
    elif tool_name == "offer_refund_method":
        return {"status": "success", "methods": tool_args.get("methods", [])}
    else:
        return {"error": f"Unknown tool: {tool_name}"}

async def run_agent_streaming(
    user_message: str,
    session_id: str,
    conversation_history: list[dict] | None = None,
    customer_name_hint: str | None = None,
    customer_id: str | None = None,
    negotiation_turn_count: int = 0,
    negotiation_conceded: bool = False,
    previous_clarification: bool = False,
) -> AsyncGenerator[dict, None]:
    
    start_time = time.time()
    
    state = {
        "messages": conversation_history or [],
        "session_id": session_id,
        "customer_id": customer_id,
        "order_id": None,
        "policy_result": None,
        "decision": None,
        "decision_reason": None,
        "negotiation_turn_count": negotiation_turn_count,
        "negotiation_conceded": negotiation_conceded,
        "reasoning_steps": [],
        "injection_result": None,
        "final_response": None,
        "clean_message": user_message.strip(),
    }
    
    # 1. Guardrail Check
    yield {"event": "step", "data": {"step": "guardrail_check", "status": "running"}}
    
    # Check if the user message is a protocol message (_select_customer: or _select_order:)
    is_protocol = False
    clean_message = user_message.strip()
    if clean_message.startswith("_select_customer:"):
        customer_id = clean_message.split(":", 1)[1].strip()
        state["customer_id"] = customer_id
        clean_message = f"I have selected my customer account. My customer ID is {customer_id}. [SYSTEM: DO NOT call search_customer again. Proceed to the next step.]"
        state["clean_message"] = clean_message
        is_protocol = True
    elif clean_message.startswith("_select_order:"):
        state["order_id"] = clean_message.split(":", 1)[1].strip()
        clean_message = f"I have selected the order. The order ID is {state['order_id']}. [SYSTEM: DO NOT call get_orders_for_customer again. Proceed to ask for the reason.]"
        state["clean_message"] = clean_message
        is_protocol = True
    elif clean_message.startswith("_select_refund_method:"):
        method = clean_message.split(":", 1)[1].strip()
        clean_message = f"I have selected {method} as my preferred refund method. Please confirm my refund is processed and DO NOT call offer_refund_method or evaluate_refund_policy again."
        state["clean_message"] = clean_message
        state["decision"] = "approved"
        is_protocol = True

    injection_result = await check_guardrails(clean_message)
    state["injection_result"] = injection_result
    
    yield {
        "event": "step",
        "data": {
            "step": "guardrail_check",
            "status": injection_result["action"],
            "risk_score": injection_result["risk_score"],
            "reasoning": injection_result["reasoning"]
        }
    }
    
    if injection_result["action"] == "block":
        state["decision"] = "flagged"
        state["decision_reason"] = injection_result["reasoning"]
        safe_response = "I'm here to help with refund and return inquiries for NovaMart. Could you please provide your name or email address so I can look into your order?"
        state["final_response"] = safe_response
        for i in range(0, len(safe_response), 4):
            yield {"event": "token", "data": {"token": safe_response[i:i+4]}}
        yield {"event": "done", "data": {"session_id": session_id, "decision": "flagged"}}
        yield {"event": "_state", "data": state}
        return

    client = _get_groq_client()
    settings = get_settings()
    
    # 2. Build Initial Messages
    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
    
    # Inject negotiation state to system prompt secretly
    system_ctx = (
        f"--- SYSTEM CONTEXT ---\n"
        f"Negotiation Turn Count: {negotiation_turn_count}\n"
        f"Concession Already Granted: {negotiation_conceded}\n"
    )
    if customer_name_hint:
        system_ctx += f"Customer Name Hint: {customer_name_hint}\n"
    messages.append({"role": "system", "content": system_ctx})
    
    for m in (conversation_history or []):
        messages.append({"role": m["role"], "content": m["content"]})
    
    messages.append({"role": "user", "content": clean_message})
    
    # 3. Agent Loop
    MAX_TOOL_ITERATIONS = 8
    
    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1024,
            )
        except Exception as e:
            logger.error("groq_api_error", error=str(e))
            yield {"event": "step", "data": {"step": "error", "status": "failed", "detail": "API Error"}}
            state["final_response"] = "I'm having trouble connecting right now. Please try again in a moment."
            break
            
        message_obj = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        
        # The manual regex block for unclosed XML tags was removed here because we upgraded to the reliable 70B model that uses native tool calling.
        
        if finish_reason == "tool_calls" and message_obj.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message_obj.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message_obj.tool_calls
                ],
            })
            
            requires_selection = False
            fallback = ""
            
            for tool_call in message_obj.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                
                yield {"event": "step", "data": {"step": "tool_call", "tool": tool_name, "args": tool_args, "status": "running"}}
                
                # Execute tool
                tool_start = time.time()
                result = await _execute_tool(tool_name, tool_args, state)
                duration_ms = int((time.time() - tool_start) * 1000)
                
                # Stream policy result specially if it was evaluate_refund_policy
                if tool_name == "evaluate_refund_policy" and "error" not in result:
                    yield {"event": "step", "data": {
                        "step": "policy_result",
                        "status": "complete",
                        "decision": result.get("decision"),
                        "reason": result.get("reason"),
                        "rules_evaluated": result.get("rules_evaluated"),
                        "confidence": result.get("confidence")
                    }}
                else:
                    yield {"event": "step", "data": {"step": "tool_result", "tool": tool_name, "status": "complete", "summary": f"Tool {tool_name} returned."}}
                    
                # Emit selection events if multiple candidates were found to force user verification
                if tool_name == "search_customer" and "customers" in result and len(result["customers"]) > 0:
                    yield {"event": "customer_selection", "data": {"prompt": "Please select your account to continue:", "candidates": result["customers"]}}
                    state["decision"] = "awaiting_selection"
                    fallback = "Please select your account from the options below to verify your identity."
                    requires_selection = True
                elif tool_name == "get_orders_for_customer" and "orders" in result and len(result["orders"]) > 0:
                    yield {"event": "order_selection", "data": {"prompt": "Please select the order you want to return:", "orders": result["orders"]}}
                    state["decision"] = "awaiting_selection"
                    fallback = "Please select the order you'd like to return from the options below."
                    requires_selection = True
                elif tool_name == "offer_refund_method" and "methods" in result and len(result["methods"]) > 0:
                    yield {"event": "refund_method_selection", "data": {"prompt": "Please select your preferred refund method:", "methods": result["methods"]}}
                    state["decision"] = "awaiting_selection"
                    fallback = "Please select your preferred refund method from the options below."
                    requires_selection = True
                
                # Record in reasoning_steps for DB
                state["reasoning_steps"].append({
                    "step": "tool_call",
                    "tool": tool_name,
                    "input": tool_args,
                    "output": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                
            if requires_selection:
                state["final_response"] = fallback
                # Yield text tokens for the UI bubble
                for i in range(0, len(fallback), 4):
                    yield {"event": "token", "data": {"token": fallback[i:i+4]}}
                break
        else:
            # We already have the final response text in message_obj.content from the non-streaming call!
            # Stream it directly to the user to simulate real-time typing and avoid a second LLM request.
            full_response = message_obj.content or "I am here to help."
            state["final_response"] = full_response
            
            # Yield in small chunks to simulate streaming
            chunk_size = 4
            for i in range(0, len(full_response), chunk_size):
                yield {"event": "token", "data": {"token": full_response[i:i+chunk_size]}}
                
            break
    else:
        # Loop finished without stop
        logger.warning("agent_loop_max_iterations_reached", session_id=session_id)
        fallback = "I'm having trouble processing this right now. Please try again later."
        state["final_response"] = fallback
        yield {"event": "token", "data": {"token": fallback}}
        
    state["request_id"] = str(uuid.uuid4())
    
    policy_res = state.get("policy_result") or {}
    yield {"event": "done", "data": {
        "session_id": session_id,
        "decision": state.get("decision"),
        "request_id": state.get("request_id"),
        "confidence": policy_res.get("confidence"),
        "rule_applied": policy_res.get("rule_applied")
    }}
    
    yield {"event": "_state", "data": state}