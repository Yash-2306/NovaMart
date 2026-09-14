"""Seed data: 15 customers with fixed UUIDs and carefully crafted orders for all test scenarios."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from app.database import async_session_factory
from app.models import Customer, Order, AccountTier, ProductCategory, OrderStatus

logger = structlog.get_logger()

# ── Fixed UUIDs for determinism ────────────────────────────────────────
# Customers
C01 = "c0000001-0000-0000-0000-000000000001"
C02 = "c0000002-0000-0000-0000-000000000002"
C03 = "c0000003-0000-0000-0000-000000000003"
C04 = "c0000004-0000-0000-0000-000000000004"
C05 = "c0000005-0000-0000-0000-000000000005"
C06 = "c0000006-0000-0000-0000-000000000006"
C07 = "c0000007-0000-0000-0000-000000000007"
C08 = "c0000008-0000-0000-0000-000000000008"
C09 = "c0000009-0000-0000-0000-000000000009"
C10 = "c0000010-0000-0000-0000-000000000010"
C11 = "c0000011-0000-0000-0000-000000000011"
C12 = "c0000012-0000-0000-0000-000000000012"
C13 = "c0000013-0000-0000-0000-000000000013"
C14 = "c0000014-0000-0000-0000-000000000014"
C15 = "c0000015-0000-0000-0000-000000000015"

# Orders
O01 = "o0000001-0000-0000-0000-000000000001"
O02 = "o0000002-0000-0000-0000-000000000002"
O03 = "o0000003-0000-0000-0000-000000000003"
O04 = "o0000004-0000-0000-0000-000000000004"
O05 = "o0000005-0000-0000-0000-000000000005"
O06 = "o0000006-0000-0000-0000-000000000006"
O07 = "o0000007-0000-0000-0000-000000000007"
O08 = "o0000008-0000-0000-0000-000000000008"
O09 = "o0000009-0000-0000-0000-000000000009"
O10 = "o0000010-0000-0000-0000-000000000010"
O11 = "o0000011-0000-0000-0000-000000000011"
O12 = "o0000012-0000-0000-0000-000000000012"
O13 = "o0000013-0000-0000-0000-000000000013"
O14 = "o0000014-0000-0000-0000-000000000014"
O15 = "o0000015-0000-0000-0000-000000000015"
O16 = "o0000016-0000-0000-0000-000000000016"
O17 = "o0000017-0000-0000-0000-000000000017"
O18 = "o0000018-0000-0000-0000-000000000018"
O19 = "o0000019-0000-0000-0000-000000000019"
O20 = "o0000020-0000-0000-0000-000000000020"
O21 = "o0000021-0000-0000-0000-000000000021"
O22 = "o0000022-0000-0000-0000-000000000022"
O23 = "o0000023-0000-0000-0000-000000000023"

# ── Time helpers ───────────────────────────────────────────────────────

def get_seed_data():
    now = datetime.now(timezone.utc)
    def _days_ago(n: int) -> datetime:
        return now - timedelta(days=n)
    def _purchase_before_delivery(delivery: datetime, days_before: int = 5) -> datetime:
        return delivery - timedelta(days=days_before)

    
    # ── Customers ──────────────────────────────────────────────────────────
    
    CUSTOMERS = [
        Customer(
            id=C01, name="Sarah Mitchell", email="sarah.mitchell@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(365),
            delivery_address="123 Oak Street, Apt 4B, New York, NY 10001",
        ),
        Customer(
            id=C02, name="James Okafor", email="james.okafor@email.com",
            account_tier=AccountTier.PREMIUM, created_at=_days_ago(400),
            delivery_address="456 Maple Drive, Austin, TX 78701",
        ),
        Customer(
            id=C03, name="Priya Sharma", email="priya.sharma@email.com",
            account_tier=AccountTier.VIP, created_at=_days_ago(730),
            delivery_address="789 Pine Lane, San Francisco, CA 94110",
        ),
        Customer(
            id=C04, name="Carlos Rivera", email="carlos.rivera@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(200),
            delivery_address="321 Elm Street, Miami, FL 33101",
        ),
        Customer(
            id=C05, name="Emily Chen", email="emily.chen@email.com",
            account_tier=AccountTier.PREMIUM, created_at=_days_ago(500),
            delivery_address="654 Birch Road, Seattle, WA 98101",
        ),
        Customer(
            id=C06, name="Mohammed Al-Farsi", email="mohammed.alfarsi@email.com",
            account_tier=AccountTier.VIP, created_at=_days_ago(900),
            delivery_address="987 Cedar Court, Chicago, IL 60601",
        ),
        Customer(
            id=C07, name="Natasha Volkova", email="natasha.volkova@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(150),
            delivery_address="147 Walnut Ave, Boston, MA 02108",
        ),
        Customer(
            id=C08, name="David Kim", email="david.kim@email.com",
            account_tier=AccountTier.PREMIUM, created_at=_days_ago(300),
            delivery_address="258 Chestnut Blvd, Los Angeles, CA 90001",
        ),
        Customer(
            id=C09, name="Aisha Osei", email="aisha.osei@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(90),
            delivery_address="369 Spruce Way, Denver, CO 80202",
        ),
        Customer(
            id=C10, name="Lucas Hoffman", email="lucas.hoffman@email.com",
            account_tier=AccountTier.VIP, created_at=_days_ago(600),
            delivery_address="741 Redwood Drive, Portland, OR 97204",
        ),
        Customer(
            id=C11, name="Sofia Rossi", email="sofia.rossi@email.com",
            account_tier=AccountTier.PREMIUM, created_at=_days_ago(450),
            delivery_address="852 Cypress Point, Atlanta, GA 30303",
        ),
        Customer(
            id=C12, name="Raj Patel", email="raj.patel@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(180),
            delivery_address="963 Willow Street, Dallas, TX 75201",
        ),
        Customer(
            id=C13, name="Zoe Williams", email="zoe.williams@email.com",
            account_tier=AccountTier.VIP, created_at=_days_ago(350),
            delivery_address="159 Poplar Ave, Phoenix, AZ 85001",
        ),
        Customer(
            id=C14, name="Chen Wei", email="chen.wei@email.com",
            account_tier=AccountTier.PREMIUM, created_at=_days_ago(250),
            delivery_address="753 Hickory Lane, Philadelphia, PA 19102",
        ),
        Customer(
            id=C15, name="Amara Diallo", email="amara.diallo@email.com",
            account_tier=AccountTier.STANDARD, created_at=_days_ago(30),
            delivery_address="842 Sycamore Blvd, Detroit, MI 48201",
        ),
    ]
    
    # ── Orders ─────────────────────────────────────────────────────────────
    # Each order is carefully crafted to test a specific scenario.
    
    _delivered_10d = _days_ago(10)  # Within 30-day window
    _delivered_15d = _days_ago(15)
    _delivered_20d = _days_ago(20)
    _delivered_45d = _days_ago(45)  # Outside 30-day window
    _delivered_exactly_30d = _days_ago(30)  # Boundary: exactly 30 days → APPROVE
    _delivered_exactly_31d = _days_ago(31)  # Boundary: exactly 31 days → DENY
    
    ORDERS = [
        # ── C01: Sarah Mitchell — final sale clothing → DENY ──
        Order(
            id=O01, customer_id=C01,
            product_name="Summer Dress (Final Sale)",
            product_category=ProductCategory.CLOTHING,
            amount=89.99, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_15d),
            is_final_sale=True, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_15d,
        ),
    
        # ── C02: James Okafor — eligible electronics $299 → APPROVE ──
        Order(
            id=O02, customer_id=C02,
            product_name="Wireless Noise-Cancelling Headphones",
            product_category=ProductCategory.ELECTRONICS,
            amount=299.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── C03: Priya Sharma — $650 furniture → ESCALATE (amount > 500) ──
        Order(
            id=O03, customer_id=C03,
            product_name="Ergonomic Standing Desk",
            product_category=ProductCategory.FURNITURE,
            amount=650.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_20d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_20d,
        ),
    
        # ── C04: Carlos Rivera — software/digital → DENY ──
        Order(
            id=O04, customer_id=C04,
            product_name="ProEdit Software License",
            product_category=ProductCategory.SOFTWARE,
            amount=149.99, currency="USD",
            purchase_date=_days_ago(12),
            is_final_sale=False, is_digital=True,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_days_ago(12),
        ),
    
        # ── C05: Emily Chen — delivered 45 days ago → DENY (past window) ──
        Order(
            id=O05, customer_id=C05,
            product_name="Bluetooth Speaker",
            product_category=ProductCategory.ELECTRONICS,
            amount=199.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_45d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_45d,
        ),
    
        # ── C06: Mohammed Al-Farsi — jewelry $1200 VIP → ESCALATE ──
        Order(
            id=O06, customer_id=C06,
            product_name="Diamond Pendant Necklace",
            product_category=ProductCategory.JEWELRY,
            amount=1200.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_15d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_15d,
        ),
    
        # ── C07: Natasha Volkova — food order → DENY ──
        Order(
            id=O07, customer_id=C07,
            product_name="Artisan Cheese Collection",
            product_category=ProductCategory.FOOD,
            amount=45.00, currency="USD",
            purchase_date=_days_ago(5),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_days_ago(5),
        ),
    
        # ── C08: David Kim — valid return $180 clothing → APPROVE ──
        Order(
            id=O08, customer_id=C08,
            product_name="Merino Wool Jacket",
            product_category=ProductCategory.CLOTHING,
            amount=180.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── C09: Aisha Osei — order still shipped → PENDING DELIVERY ──
        Order(
            id=O09, customer_id=C09,
            product_name="Yoga Mat Premium",
            product_category=ProductCategory.CLOTHING,
            amount=65.00, currency="USD",
            purchase_date=_days_ago(3),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.SHIPPED,
            delivered_at=None,
        ),
    
        # ── C10: Lucas Hoffman — cancelled order VIP → DENY ──
        Order(
            id=O10, customer_id=C10,
            product_name="Smart Home Hub",
            product_category=ProductCategory.ELECTRONICS,
            amount=349.00, currency="USD",
            purchase_date=_days_ago(20),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.CANCELLED,
            delivered_at=None,
        ),
    
        # ── C11: Sofia Rossi — two orders ──
        # Order 1: approvable clothing $120
        Order(
            id=O11, customer_id=C11,
            product_name="Cashmere Scarf",
            product_category=ProductCategory.CLOTHING,
            amount=120.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
        # Order 2: final sale electronics
        Order(
            id=O12, customer_id=C11,
            product_name="Clearance Earbuds (Final Sale)",
            product_category=ProductCategory.ELECTRONICS,
            amount=39.99, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=True, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── C12: Raj Patel — electronics $499 → APPROVE (≤500 threshold) ──
        Order(
            id=O13, customer_id=C12,
            product_name="Mechanical Keyboard Deluxe",
            product_category=ProductCategory.ELECTRONICS,
            amount=499.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── C13: Zoe Williams — VIP, $510 → ESCALATE (>500 threshold) ──
        Order(
            id=O14, customer_id=C13,
            product_name="Premium Yoga Set",
            product_category=ProductCategory.CLOTHING,
            amount=510.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── C14: Chen Wei — digital course → DENY ──
        Order(
            id=O15, customer_id=C14,
            product_name="Advanced Python Masterclass",
            product_category=ProductCategory.SOFTWARE,
            amount=89.99, currency="USD",
            purchase_date=_days_ago(7),
            is_final_sale=False, is_digital=True,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_days_ago(7),
        ),
    
        # ── C15: Amara Diallo — eligible $75 return → APPROVE ──
        Order(
            id=O16, customer_id=C15,
            product_name="Cotton T-Shirt Bundle",
            product_category=ProductCategory.CLOTHING,
            amount=75.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # ── BOUNDARY SCENARIO ORDERS ──
    
        # Scenario 11: Amount exactly $500.00 → APPROVE
        Order(
            id=O17, customer_id=C12,
            product_name="Gaming Monitor",
            product_category=ProductCategory.ELECTRONICS,
            amount=500.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # Scenario 12: Amount exactly $500.01 → ESCALATE
        Order(
            id=O18, customer_id=C13,
            product_name="Smart Watch Pro",
            product_category=ProductCategory.ELECTRONICS,
            amount=500.01, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # Scenario 13: Delivered exactly 30 days ago → APPROVE
        Order(
            id=O19, customer_id=C08,
            product_name="Running Shoes",
            product_category=ProductCategory.CLOTHING,
            amount=129.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_exactly_30d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_exactly_30d,
        ),
    
        # Scenario 14: Delivered exactly 31 days ago → DENY
        Order(
            id=O20, customer_id=C05,
            product_name="Desk Lamp LED",
            product_category=ProductCategory.ELECTRONICS,
            amount=79.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_exactly_31d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_exactly_31d,
        ),
    
        # Scenario 15: is_final_sale=true AND VIP → DENY (policy absolute)
        Order(
            id=O21, customer_id=C03,
            product_name="Limited Edition Silk Pillow (Final Sale)",
            product_category=ProductCategory.FURNITURE,
            amount=189.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=True, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    
        # Extra: C09 has a second order in processing
        Order(
            id=O22, customer_id=C09,
            product_name="Resistance Bands Set",
            product_category=ProductCategory.CLOTHING,
            amount=35.00, currency="USD",
            purchase_date=_days_ago(1),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.PROCESSING,
            delivered_at=None,
        ),
    
        # Extra: C06 second order — VIP borderline <$200 → ESCALATE
        Order(
            id=O23, customer_id=C06,
            product_name="Silver Bracelet",
            product_category=ProductCategory.JEWELRY,
            amount=150.00, currency="USD",
            purchase_date=_purchase_before_delivery(_delivered_10d),
            is_final_sale=False, is_digital=False,
            order_status=OrderStatus.DELIVERED,
            delivered_at=_delivered_10d,
        ),
    ]
    
    
    
    return CUSTOMERS, ORDERS

async def seed_database() -> None:
    """Seed the database with test data if empty."""
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(Customer).limit(1))
        if result.scalar_one_or_none() is not None:
            logger.info("database_already_seeded", action="skip")
            return

        customers, orders = get_seed_data()
        logger.info("seeding_database", customers=len(customers), orders=len(orders))

        # Add customers
        for customer in customers:
            session.add(customer)
        await session.flush()

        # Add orders
        for order in orders:
            session.add(order)

        await session.commit()
        logger.info("database_seeded_successfully")
