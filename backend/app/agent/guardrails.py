"""
Three-layer guardrail system for prompt injection detection.

Layer 1: Keyword scanning (instant)
Layer 2: Heuristic pattern matching (instant)
Layer 3: Semantic check via LLM (async, only if L1+L2 < 0.70)
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any

import structlog
from groq import AsyncGroq

from app.config import get_settings
from app.agent.prompts import GUARDRAIL_SEMANTIC_PROMPT

logger = structlog.get_logger()


@lru_cache(maxsize=1)
def _get_guardrail_client() -> AsyncGroq:
    """Cached singleton AsyncGroq client for guardrail checks."""
    settings = get_settings()
    return AsyncGroq(api_key=settings.groq_api_key)

# ── Layer 1: Keyword phrases from policy Section 7 ────────────────────

INJECTION_PHRASES = [
    "ignore previous instructions",
    "you are now",
    "pretend you are",
    "developer mode",
    "override policy",
    "as your creator",
    "system prompt",
    "forget your rules",
    "bypass",
    "jailbreak",
    "act as",
    "disregard",
    "sudo",
    "admin mode",
    "new persona",
    "ignore all previous",
    "disregard all instructions", 
    "you must approve",
    "i authorize you to",
    "override the decision",
    "grant me a refund",
    "i demand you",
    "print your instructions",
    "reveal your prompt",
    "what are your instructions",
]

# ── Layer 2: Heuristic patterns ───────────────────────────────────────

def _is_mostly_caps(text: str) -> bool:
    """Check if message is mostly uppercase (>70% of alpha chars)."""
    alpha_chars = [c for c in text if c.isalpha()]
    if len(alpha_chars) < 5:
        return False
    upper_count = sum(1 for c in alpha_chars if c.isupper())
    return upper_count / len(alpha_chars) > 0.70


def _has_excessive_punctuation(text: str) -> bool:
    """Check for excessive punctuation like !!! or ???."""
    return bool(re.search(r'[!?]{3,}', text))


def _requests_code_output(text: str) -> bool:
    """Check if user is asking for JSON/code output (potential extraction)."""
    patterns = [
        r'\bprint\s+(your|the)\s+(system|original|full)\s+(prompt|instructions)\b',
        r'\boutput\s+(as\s+)?json\b',
        r'\breturn\s+(raw|the)\s+(json|data|code)\b',
        r'\bshow\s+(me\s+)?(your|the)\s+(source|code|prompt)\b',
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _has_roleplay_framing(text: str) -> bool:
    """Check for role-play framing attempts."""
    patterns = [
        r"let'?s\s+play\s+a\s+game",
        r"imagine\s+you\s+are",
        r"from\s+now\s+on\s+you\s+are",
        r"i\s+want\s+you\s+to\s+(act|pretend|roleplay|behave)",
        r"you\s+are\s+no\s+longer",
        r"switch\s+to\s+.+\s+mode",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _claims_authority(text: str) -> bool:
    """Check if user claims system-level authority."""
    patterns = [
        r"i\s+am\s+(a|the|your)\s+(developer|admin|creator|owner|manager|employee)",
        r"i\s+have\s+(admin|root|system)\s+(access|permissions|privileges)",
        r"as\s+(an?\s+)?(admin|developer|manager|supervisor)",
        r"i\s+work\s+(at|for)\s+(novamart|the\s+company)",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _has_no_context_and_long(text: str) -> bool:
    """Check if message is long (>800 chars) with no refund context."""
    if len(text) > 800:
        text_lower = text.lower()
        refund_terms = ["refund", "return", "order", "product"]
        if not any(term in text_lower for term in refund_terms):
            return True
    return False


# ── Layer 3: Semantic LLM check ───────────────────────────────────────

async def _semantic_check(message: str) -> bool:
    """
    Use LLM to detect manipulation attempts that bypass keyword/heuristic layers.
    Returns True if the message is a manipulation attempt.
    """
    try:
        client = _get_guardrail_client()
        settings = get_settings()
        response = await client.chat.completions.create(
            model=settings.groq_fast_model,
            messages=[
                {
                    "role": "system",
                    "content": GUARDRAIL_SEMANTIC_PROMPT.strip(),
                },
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        logger.warning("guardrail_semantic_check_failed", error=str(e))
        return True  # Fail closed — block on LLM errors to prevent bypass


# ── Main guardrail function ───────────────────────────────────────────

async def check_guardrails(message: str) -> dict[str, Any]:
    """
    Run three-layer guardrail check on incoming message.

    Returns:
        {
            "risk_score": float (0.0–1.0),
            "layer1_triggered": bool,
            "layer2_triggered": bool,
            "layer3_triggered": bool,
            "flagged_phrases": list[str],
            "action": "allow" | "caution" | "block",
            "reasoning": str
        }
    """
    risk_score = 0.0
    flagged_phrases: list[str] = []
    layer1_triggered = False
    layer2_triggered = False
    layer3_triggered = False
    reasoning_parts: list[str] = []

    def _normalize_message(text: str) -> str:
        # Remove zero-width characters
        text = ''.join(c for c in text if unicodedata.category(c) != 'Cf')
        # Normalize unicode to NFC form
        text = unicodedata.normalize('NFC', text)
        return text

    message_normalized = _normalize_message(message)
    message_lower = message_normalized.lower()

    # ── Layer 1: Keyword scan ──────────────────────────────────────
    for phrase in INJECTION_PHRASES:
        if phrase in message_lower:
            flagged_phrases.append(phrase)
            risk_score += 0.35
            layer1_triggered = True

    if re.search(r'\bdan\b', message_lower):
        refund_terms = ["refund", "return", "order", "product"]
        if not any(term in message_lower for term in refund_terms):
            flagged_phrases.append("dan")
            risk_score += 0.35
            layer1_triggered = True

    if layer1_triggered:
        reasoning_parts.append(
            f"Layer 1 (Keyword): Detected {len(flagged_phrases)} injection phrase(s): "
            f"{', '.join(flagged_phrases)}"
        )

    # Cap at 1.0
    risk_score = min(risk_score, 1.0)

    # ── Layer 2: Heuristic patterns ────────────────────────────────
    l2_triggers: list[str] = []

    if _is_mostly_caps(message):
        l2_triggers.append("ALL_CAPS_MESSAGE")
        risk_score += 0.20

    if _has_excessive_punctuation(message):
        l2_triggers.append("EXCESSIVE_PUNCTUATION")
        risk_score += 0.20

    if _requests_code_output(message):
        l2_triggers.append("CODE_OUTPUT_REQUEST")
        risk_score += 0.20

    if _has_roleplay_framing(message):
        l2_triggers.append("ROLEPLAY_FRAMING")
        risk_score += 0.20

    if _claims_authority(message):
        l2_triggers.append("CLAIMS_AUTHORITY")
        risk_score += 0.20

    if _has_no_context_and_long(message):
        l2_triggers.append("LONG_NO_CONTEXT")
        risk_score += 0.15

    if l2_triggers:
        layer2_triggered = True
        reasoning_parts.append(
            f"Layer 2 (Heuristic): Triggered {len(l2_triggers)} pattern(s): "
            f"{', '.join(l2_triggers)}"
        )

    risk_score = min(risk_score, 1.0)

    # ── Layer 3: Semantic check (only if L1+L2 < 0.70) ─────────────
    if risk_score < 0.70:
        is_manipulation = await _semantic_check(message)
        if is_manipulation:
            layer3_triggered = True
            risk_score += 0.50
            risk_score = min(risk_score, 1.0)
            reasoning_parts.append(
                "Layer 3 (Semantic): LLM classified message as manipulation attempt"
            )
    else:
        reasoning_parts.append(
            "Layer 3 (Semantic): Skipped — risk already ≥ 0.70 from L1+L2"
        )

    # ── Determine action ───────────────────────────────────────────
    if risk_score >= 0.70:
        action = "block"
    elif risk_score >= 0.30:
        action = "caution"
    else:
        action = "allow"

    if not reasoning_parts:
        reasoning_parts.append("No guardrail triggers detected. Message appears safe.")

    reasoning_parts.append(f"Final risk score: {risk_score:.2f} → action: {action}")

    return {
        "risk_score": round(risk_score, 2),
        "layer1_triggered": layer1_triggered,
        "layer2_triggered": layer2_triggered,
        "layer3_triggered": layer3_triggered,
        "flagged_phrases": flagged_phrases,
        "action": action,
        "reasoning": " | ".join(reasoning_parts),
    }
