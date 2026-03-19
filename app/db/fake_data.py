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

from app.models.discount import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
from app.models.domain import CartItem, PaymentInfo, Product
from app.models.enums import BrandTier, CardType, CustomerTier

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

ICICI_PAYMENT = PaymentInfo(method="CARD", bank_name="ICICI", card_type=CardType.CREDIT)

# ── Discount rules ────────────────────────────────────────────────────────────

BRAND_DISCOUNTS: list[BrandDiscount] = [
    BrandDiscount(name="PUMA 40% off", brand="PUMA", percent=Decimal("40")),
    BrandDiscount(name="NIKE 30% off", brand="NIKE", percent=Decimal("30")),
    BrandDiscount(name="ADIDAS 25% off", brand="ADIDAS", percent=Decimal("25")),
    BrandDiscount(name="ZARA 20% off", brand="ZARA", percent=Decimal("20")),
]

CATEGORY_DISCOUNTS: list[CategoryDiscount] = [
    CategoryDiscount(name="T-shirt extra 10%", category="t-shirts", percent=Decimal("10")),
    CategoryDiscount(name="Footwear 15% off", category="footwear", percent=Decimal("15")),
    CategoryDiscount(name="Jeans 20% off", category="jeans", percent=Decimal("20")),
    CategoryDiscount(name="Accessories 5% off", category="accessories", percent=Decimal("5")),
]

VOUCHERS: list[VoucherDiscount] = [
    VoucherDiscount(name="SUPER69", code="SUPER69", percent=Decimal("69"), min_customer_tier=CustomerTier.REGULAR),
    VoucherDiscount(name="LOCALPROMO50", code="LOCALPROMO50", percent=Decimal("50"), min_customer_tier=CustomerTier.REGULAR, excluded_brands=["PUMA", "Nike"]),
    VoucherDiscount(name="NOACCESSORIES60", code="NOACCESSORIES60", percent=Decimal("60"), min_customer_tier=CustomerTier.REGULAR, excluded_categories=["accessories"]),
    VoucherDiscount(name="SILVER20", code="SILVER20", percent=Decimal("20"), min_customer_tier=CustomerTier.SILVER),
    VoucherDiscount(name="GOLD50", code="GOLD50", percent=Decimal("50"), min_customer_tier=CustomerTier.GOLD, excluded_brands=["ZARA"], excluded_categories=["accessories"]),
    VoucherDiscount(name="WELCOME10", code="WELCOME10", percent=Decimal("10"), min_customer_tier=CustomerTier.REGULAR)
]

BANK_OFFERS: list[BankOffer] = [
    BankOffer(name="ICICI 10% instant", bank_name="ICICI", percent=Decimal("10")),
    BankOffer(name="HDFC Credit 15%", bank_name="HDFC", percent=Decimal("15"), card_type=CardType.CREDIT),
    BankOffer(name="SBI Debit 5%", bank_name="SBI", percent=Decimal("5"), card_type=CardType.DEBIT),
    BankOffer(name="AXIS 12% instant", bank_name="AXIS", percent=Decimal("12")),
]