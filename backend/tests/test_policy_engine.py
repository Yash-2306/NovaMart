import pytest
from datetime import datetime, timezone, timedelta
from app.agent.policy_engine import evaluate_refund_policy

def _base_customer(tier="standard"):
    return {"id": "c-test", "name": "Test User", "email": "test@test.com", "account_tier": tier}

def _base_order(**kwargs):
    defaults = {
        "id": "o-test", "customer_id": "c-test",
        "product_name": "Test Item", "product_category": "electronics",
        "amount": 100.0, "currency": "USD",
        "is_final_sale": False, "is_digital": False,
        "order_status": "delivered",
        "delivered_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    }
    defaults.update(kwargs)
    return defaults

# R01
def test_final_sale_denied():
    result = evaluate_refund_policy(_base_order(is_final_sale=True), _base_customer())
    assert result["decision"] == "denied"
    assert result["rule_applied"] == "R01_FINAL_SALE"

# R02
def test_digital_product_denied():
    result = evaluate_refund_policy(_base_order(is_digital=True), _base_customer())
    assert result["decision"] == "denied"
    assert result["rule_applied"] == "R02_DIGITAL_PRODUCT"

# R07 boundary: exactly 30 days → APPROVE
def test_exactly_30_days_approve():
    delivered = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    result = evaluate_refund_policy(_base_order(delivered_at=delivered), _base_customer())
    assert result["decision"] == "approved"

# R07 boundary: exactly 31 days → DENY
def test_exactly_31_days_deny():
    delivered = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    result = evaluate_refund_policy(_base_order(delivered_at=delivered), _base_customer())
    assert result["decision"] == "denied"
    assert result["rule_applied"] == "R07_PAST_RETURN_WINDOW"

# R08 boundary: exactly $500.00 → APPROVE
def test_exactly_500_approve():
    result = evaluate_refund_policy(_base_order(amount=500.00), _base_customer())
    assert result["decision"] == "approved"

# R08 boundary: $500.01 → ESCALATED
def test_500_01_escalated():
    result = evaluate_refund_policy(_base_order(amount=500.01), _base_customer())
    assert result["decision"] == "escalated"
    assert result["rule_applied"] == "R08_HIGH_VALUE"

# R01 overrides VIP
def test_final_sale_vip_still_denied():
    result = evaluate_refund_policy(_base_order(is_final_sale=True), _base_customer(tier="vip"))
    assert result["decision"] == "denied"

# Additional missing rules for completeness
def test_food_perishable_denied():
    result = evaluate_refund_policy(_base_order(product_category="food"), _base_customer())
    assert result["decision"] == "denied"
    assert result["rule_applied"] == "R03_FOOD_PERISHABLE"

def test_status_cancelled_denied():
    result = evaluate_refund_policy(_base_order(order_status="cancelled"), _base_customer())
    assert result["decision"] == "denied"

def test_status_shipped_pending():
    result = evaluate_refund_policy(_base_order(order_status="shipped"), _base_customer())
    assert result["decision"] == "pending_delivery"

def test_jewelry_over_1000_escalated():
    result = evaluate_refund_policy(_base_order(amount=1200.00, product_category="jewelry"), _base_customer("vip"))
    assert result["decision"] == "escalated"
