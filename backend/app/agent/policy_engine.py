"""
Deterministic Refund Policy Engine — Pure Python, Zero LLM Calls.

Evaluates refund eligibility by applying rules R01–R12 in strict order.
Returns a comprehensive result with full rules_evaluated chain.
"""

from __future__ import annotations

from datetime import datetime, timezone


def get_policy_explanation(rule_id: str, days: int | None = None, amount: float | None = None) -> str:
    """Return a plain-English customer-facing explanation for each rule."""
    if rule_id == "R01_FINAL_SALE":
        return "This item was purchased as a Final Sale item and is not eligible for returns or refunds."
    if rule_id == "R02_DIGITAL_PRODUCT":
        return "Digital products and software licenses cannot be refunded once delivered."
    if rule_id == "R03_FOOD_PERISHABLE":
        return "Perishable items cannot be returned."
    if rule_id == "R04_CANCELLED_ORDER":
        return "Order was already cancelled; no payment to refund."
    if rule_id == "R05_UNDELIVERED":
        return "Your order is currently in transit. We cannot process a refund until the order has been delivered. Please wait for delivery and contact us again if needed."
    if rule_id == "R06_MISSING_DELIVERY_DATE":
        return "Delivery date cannot be verified. We cannot process a refund without a valid delivery date to confirm the return window."
    if rule_id == "R07_PAST_RETURN_WINDOW":
        days_str = str(days) if days is not None else "over 30"
        return f"Our return window is 30 days from delivery. Your order was delivered {days_str} days ago."
    if rule_id == "R08_HIGH_VALUE":
        amount_str = f"${amount:.2f}" if amount is not None else "over $500"
        return (
            f"Refund requests over $500 cannot be automatically approved via this channel. "
            f"Your request for {amount_str} has been denied."
        )
    if rule_id == "R09_HIGH_VALUE_JEWELRY":
        amount_str = f"${amount:.2f}" if amount is not None else "over $1,000"
        return (
            f"Jewelry items over $1,000 cannot be automatically approved via this channel. "
            f"Your request for {amount_str} has been denied."
        )
    if rule_id == "R10_VIP_BORDERLINE":
        return "As a valued VIP customer, we have made an exception and approved your borderline refund request."
    if rule_id == "R11_LOW_CONFIDENCE":
        return "This request cannot be verified with sufficient confidence and has been denied."
    if rule_id == "R12_ALL_PASS":
        return "Your refund has been approved. Please allow 3–5 business days for the refund to be processed."
    return "Your case requires further review."


def evaluate_refund_policy(order: dict, customer: dict) -> dict:
    """
    Evaluate a refund request against the NovaMart refund policy v2.4.

    Rules are evaluated in strict order R01–R12, stopping at the first
    triggered deny/pending rule.

    Args:
        order: Order dict with keys: id, product_name, product_category, amount,
               is_final_sale, is_digital, order_status, delivered_at, currency
        customer: Customer dict with keys: id, name, email, account_tier

    Returns:
        Full policy evaluation result with decision, reasoning, and rules chain.
    """
    rules_evaluated: list[dict] = []
    overrides_checked: list[str] = []
    confidence = 1.0
    reason = ""
    rule_applied = ""
    days_since_delivery: int | None = None

    amount = float(order.get("amount") or 0)
    category = order.get("product_category", "").lower()
    is_final_sale = order.get("is_final_sale", False)
    is_digital = order.get("is_digital", False)
    order_status = order.get("order_status", "").lower()
    delivered_at = order.get("delivered_at")
    account_tier = customer.get("account_tier", "standard").lower()

    # Parse delivered_at if string
    if isinstance(delivered_at, str) and delivered_at:
        try:
            delivered_at = datetime.fromisoformat(delivered_at)
        except (ValueError, TypeError):
            delivered_at = None

    # Calculate days since delivery
    if delivered_at is not None:
        if not hasattr(delivered_at, 'tzinfo') or delivered_at.tzinfo is None:
            delivered_at = delivered_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - delivered_at
        days_since_delivery = delta.days

    # ── Confidence deductions for close calls ──────────────────────
    # Amount within 10% of $500 threshold
    if 450 <= amount <= 550:
        confidence -= 0.15

    # Days within 2 of 30-day limit
    if days_since_delivery is not None and 28 <= days_since_delivery <= 32:
        confidence -= 0.15

    # Missing delivered_at
    if delivered_at is None and order_status == "delivered":
        confidence -= 0.20

    # ── Rule Evaluation (strict order) ─────────────────────────────

    triggered_decision = None

    # R01: Final Sale
    r01_triggered = is_final_sale is True
    rules_evaluated.append({
        "rule_id": "R01_FINAL_SALE",
        "rule_name": "Final Sale Check",
        "description": "Final sale items are non-refundable",
        "value_checked": is_final_sale,
        "triggered": r01_triggered,
        "outcome": "deny" if r01_triggered else "pass",
        "weight": 1.0,
    })
    if r01_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = "Final sale items are non-refundable."
        rule_applied = "R01_FINAL_SALE"
        # VIP override check — policy says final sale is absolute
        overrides_checked.append(
            f"VIP_OVERRIDE: not applicable — is_final_sale=True (policy absolute, "
            f"customer_tier={account_tier})"
        )

    # R02: Digital Product
    r02_triggered = is_digital is True
    rules_evaluated.append({
        "rule_id": "R02_DIGITAL_PRODUCT",
        "rule_name": "Digital Product Check",
        "description": "Digital products and software licenses are non-refundable once accessed",
        "value_checked": is_digital,
        "triggered": r02_triggered,
        "outcome": "deny" if r02_triggered else "pass",
        "weight": 1.0,
    })
    if r02_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = "Digital products and software licenses are non-refundable once accessed."
        rule_applied = "R02_DIGITAL_PRODUCT"

    # R03: Food/Perishable
    r03_triggered = category == "food"
    rules_evaluated.append({
        "rule_id": "R03_FOOD_PERISHABLE",
        "rule_name": "Perishable Item Check",
        "description": "Perishable items cannot be returned",
        "value_checked": category,
        "triggered": r03_triggered,
        "outcome": "deny" if r03_triggered else "pass",
        "weight": 1.0,
    })
    if r03_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = "Perishable items cannot be returned."
        rule_applied = "R03_FOOD_PERISHABLE"

    # R04: Cancelled Order
    r04_triggered = order_status == "cancelled"
    rules_evaluated.append({
        "rule_id": "R04_CANCELLED_ORDER",
        "rule_name": "Cancelled Order Check",
        "description": "Order was already cancelled; no payment to refund",
        "value_checked": order_status,
        "triggered": r04_triggered,
        "outcome": "deny" if r04_triggered else "pass",
        "weight": 1.0,
    })
    if r04_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = "Order was already cancelled; no payment to refund."
        rule_applied = "R04_CANCELLED_ORDER"

    # R05: Undelivered (shipped/processing)
    r05_triggered = order_status in ("shipped", "processing")
    rules_evaluated.append({
        "rule_id": "R05_UNDELIVERED",
        "rule_name": "Undelivered Order Check",
        "description": "Order is still in transit — cannot process refund yet",
        "value_checked": order_status,
        "triggered": r05_triggered,
        "outcome": "pending" if r05_triggered else "pass",
        "weight": 0.9,
    })
    if r05_triggered and triggered_decision is None:
        triggered_decision = "pending_delivery"
        reason = (
            f"Your order is currently {order_status}. We cannot process a refund "
            f"until the order has been delivered. Please wait for delivery and "
            f"contact us again if needed."
        )
        rule_applied = "R05_UNDELIVERED"

    # R06: Missing delivered_at but status=delivered
    r06_triggered = delivered_at is None and order_status == "delivered"
    rules_evaluated.append({
        "rule_id": "R06_MISSING_DELIVERY_DATE",
        "rule_name": "Missing Delivery Date",
        "description": "Delivery date is missing but status shows delivered — data inconsistency",
        "value_checked": {"delivered_at": str(delivered_at), "order_status": order_status},
        "triggered": r06_triggered,
        "outcome": "deny" if r06_triggered else "pass",
        "weight": 0.8,
    })
    if r06_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = "Delivery date cannot be verified. We cannot process a refund without a valid delivery date."
        rule_applied = "R06_MISSING_DELIVERY_DATE"

    # R07: Past 30-day window
    r07_triggered = days_since_delivery is not None and days_since_delivery > 30
    rules_evaluated.append({
        "rule_id": "R07_PAST_RETURN_WINDOW",
        "rule_name": "Return Window Check",
        "description": "Return window of 30 days has expired",
        "value_checked": days_since_delivery,
        "triggered": r07_triggered,
        "outcome": "deny" if r07_triggered else "pass",
        "weight": 1.0,
    })
    if r07_triggered and triggered_decision is None:
        triggered_decision = "denied"
        reason = (
            f"Return window of 30 days has expired. "
            f"Your order was delivered {days_since_delivery} days ago."
        )
        rule_applied = "R07_PAST_RETURN_WINDOW"

    # R08: High value (> $500) → escalate to senior specialist
    r08_triggered = amount > 500
    rules_evaluated.append({
        "rule_id": "R08_HIGH_VALUE",
        "rule_name": "High Value Escalation",
        "description": "Refund requests over $500 require senior specialist review",
        "value_checked": amount,
        "triggered": r08_triggered,
        "outcome": "escalate" if r08_triggered else "pass",
        "weight": 0.9,
    })
    if r08_triggered and triggered_decision is None:
        triggered_decision = "escalated"
        reason = (
            f"Refund requests over $500 cannot be automatically approved via this channel. "
            f"Your request for ${amount:.2f} has been denied."
        )
        rule_applied = "R08_HIGH_VALUE"

    # R09: High value jewelry (> $1000) → escalate to jewelry specialist
    r09_triggered = category == "jewelry" and amount > 1000
    rules_evaluated.append({
        "rule_id": "R09_HIGH_VALUE_JEWELRY",
        "rule_name": "High Value Jewelry Escalation",
        "description": "Jewelry items over $1,000 require human inspection and approval",
        "value_checked": {"category": category, "amount": amount},
        "triggered": r09_triggered,
        "outcome": "escalate" if r09_triggered else "pass",
        "weight": 1.0,
    })
    if r09_triggered and triggered_decision is None:
        triggered_decision = "escalated"
        reason = (
            f"Jewelry items over $1,000 cannot be automatically approved via this channel. "
            f"Your request for ${amount:.2f} has been denied."
        )
        rule_applied = "R09_HIGH_VALUE_JEWELRY"

    # R10: VIP borderline < $200
    is_borderline = (
        days_since_delivery is not None and 25 <= days_since_delivery <= 32
    ) or (450 <= amount <= 550)
    r10_triggered = account_tier == "vip" and is_borderline and amount < 200
    rules_evaluated.append({
        "rule_id": "R10_VIP_BORDERLINE",
        "rule_name": "VIP Borderline Approval",
        "description": "VIP customer with borderline case under $200 — approve exception",
        "value_checked": {
            "account_tier": account_tier,
            "is_borderline": is_borderline,
            "amount": amount,
        },
        "triggered": r10_triggered,
        "outcome": "approve" if r10_triggered else "pass",
        "weight": 0.7,
    })
    if r10_triggered and triggered_decision is None:
        triggered_decision = "approved"
        reason = f"As a valued VIP customer, we have made an exception and approved your borderline refund request for ${amount:.2f}."
        rule_applied = "R10_VIP_BORDERLINE"
        overrides_checked.append(
            f"VIP_OVERRIDE: applied — borderline case, amount=${amount:.2f} < $200, approved"
        )

    # Check if multiple rules evaluated without clear winner → lower confidence
    triggered_count = sum(1 for r in rules_evaluated if r["triggered"])
    if triggered_count == 0:
        # No deny/escalate rules triggered — additional confidence check
        pass
    elif triggered_count > 1:
        confidence -= 0.10

    # R11: Low confidence fallback
    r11_triggered = confidence < 0.70
    rules_evaluated.append({
        "rule_id": "R11_LOW_CONFIDENCE",
        "rule_name": "Low Confidence Escalation",
        "description": "If confidence score drops below 0.70, escalate to human agent",
        "value_checked": confidence,
        "triggered": r11_triggered,
        "outcome": "escalate" if r11_triggered else "pass",
        "weight": 1.0,
    })
    if r11_triggered and triggered_decision is None:
        triggered_decision = "escalated"
        reason = "This request cannot be verified with sufficient confidence and has been denied."
        rule_applied = "R11_LOW_CONFIDENCE"

    # R12: All checks pass
    r12_triggered = triggered_decision is None
    rules_evaluated.append({
        "rule_id": "R12_ALL_PASS",
        "rule_name": "All Checks Passed",
        "description": "All policy checks passed — refund approved",
        "value_checked": True,
        "triggered": r12_triggered,
        "outcome": "approve" if r12_triggered else "pass",
        "weight": 1.0,
    })
    if r12_triggered:
        triggered_decision = "approved"
        reason = (
            f"Your refund of ${amount:.2f} has been approved. "
            f"Please allow 3–5 business days for the refund to be processed."
        )
        rule_applied = "R12_ALL_PASS"

    # VIP override check for non-final-sale denials
    if account_tier == "vip" and triggered_decision == "denied" and not is_final_sale:
        if amount < 200:
            overrides_checked.append(
                f"VIP_OVERRIDE: considered — tier=vip, amount=${amount:.2f}, "
                f"but denial reason ({rule_applied}) is policy-absolute"
            )

    # Replace reason with human-readable explanation
    if rule_applied:
        reason = get_policy_explanation(rule_applied, days=days_since_delivery, amount=amount)

    # Ensure confidence stays in bounds
    confidence = max(0.0, min(1.0, confidence))

    return {
        "decision": triggered_decision or "approved",
        "reason": reason,
        "rule_applied": rule_applied,
        "confidence": round(confidence, 2),
        "days_since_delivery": days_since_delivery,
        "amount": amount,
        "rules_evaluated": rules_evaluated,
        "overrides_checked": overrides_checked,
        "partial_refund_requested": False,
        "policy_version": "2.4",
    }



