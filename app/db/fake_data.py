"""
In-memory store — stands in for a real database.

Scenario:
  PUMA T-shirt  base_price=₹1000, current_price=₹600 (40% brand discount baked in)
  ① PUMA brand   40% off
  ② T-shirt cat  10% off
  ③ ICICI bank   10% instant
  ④ SUPER69      69% voucher
"""

from decimal import Decimal

from app.models.discount import BrandTier, CartItem, CustomerTier, PaymentInfo, Product
from app.schemas.discount_rules import (
    BankOffer,
    BrandDiscount,
    CategoryDiscount,
    VoucherDiscount,
)

# ── Products ──────────────────────────────────────────────────────────────────

PRODUCTS: dict[str, Product] = {
    "11111111-1111-4111-8111-111111111111": Product(
        id="11111111-1111-4111-8111-111111111111",
        brand="PUMA",
        brand_tier=BrandTier.PREMIUM,
        category="t-shirts",
        base_price=Decimal("1000.00"),
        current_price=Decimal("600.00"),
    ),
}

# ── Sample cart / customer / payment (used by tests and seed routes) ──────────

SAMPLE_CART: list[CartItem] = [
    CartItem(product=PRODUCTS["11111111-1111-4111-8111-111111111111"], quantity=1, size="M"),
]

ICICI_PAYMENT = PaymentInfo(method="CARD", bank_name="ICICI", card_type="CREDIT")

# ── Discount rules ────────────────────────────────────────────────────────────

BRAND_DISCOUNTS: list[BrandDiscount] = [
    BrandDiscount(name="PUMA 40% off", brand="PUMA", percent=Decimal("40")),
]

CATEGORY_DISCOUNTS: list[CategoryDiscount] = [
    CategoryDiscount(name="T-shirt extra 10%", category="t-shirts", percent=Decimal("10")),
]

VOUCHERS: list[VoucherDiscount] = [
    VoucherDiscount(
        name="SUPER69",
        code="SUPER69",
        percent=Decimal("69"),
        min_customer_tier=CustomerTier.REGULAR,
    ),
]

BANK_OFFERS: list[BankOffer] = [
    BankOffer(name="ICICI 10% instant", bank_name="ICICI", percent=Decimal("10")),
]