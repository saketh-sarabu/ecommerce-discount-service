"""
Discount calculation logic.

Stacking order:
  1. Brand / category discounts  (applied to base_price, per line item)
  2. Voucher code                (applied to price after step 1)
  3. Bank offer                  (applied to price after step 2)
"""

from decimal import Decimal
from typing import Optional

from app.models.discount import (
    CartItem,
    CustomerTier,
    DiscountedPrice,
    PaymentInfo,
)
from app.schemas.discount_rules import (
    BankOffer,
    BrandDiscount,
    CategoryDiscount,
    VoucherDiscount,
)
from app.schemas.cart import CartRequest  # noqa: F401 (kept for caller reference)

_TIER_RANK: dict[CustomerTier, int] = {
    CustomerTier.REGULAR:  0,
    CustomerTier.SILVER:   1,
    CustomerTier.GOLD:     2,
    CustomerTier.PLATINUM: 3,
}


def _pct(price: Decimal, percent: Decimal) -> Decimal:
    """Return the discount amount for a percentage."""
    return (price * percent / Decimal("100")).quantize(Decimal("0.01"))


class DiscountService:
    def __init__(
        self,
        brand_discounts: list[BrandDiscount],
        category_discounts: list[CategoryDiscount],
        vouchers: list[VoucherDiscount],
        bank_offers: list[BankOffer],
    ) -> None:
        self._brands     = {d.brand.lower(): d    for d in brand_discounts    if d.active}
        self._categories = {d.category.lower(): d for d in category_discounts if d.active}
        self._vouchers   = {v.code.upper(): v     for v in vouchers           if v.active}
        self._bank_offers = bank_offers

    async def calculate_cart_discounts(
        self,
        cart_items: list[CartItem],
        customer_tier: CustomerTier,
        payment_info: Optional[PaymentInfo] = None,
        voucher_code: Optional[str] = None,
    ) -> DiscountedPrice:
        """Calculate the final cart price after all eligible discounts."""
        applied: dict[str, Decimal] = {}

        original_price = sum((i.product.base_price * i.quantity for i in cart_items), Decimal("0.00"))
        price = original_price

        price = self._apply_brand_category(cart_items, price, applied)

        if voucher_code:
            valid, _ = self._check_voucher(voucher_code, cart_items, customer_tier)
            if valid:
                voucher        = self._vouchers[voucher_code.upper()]
                amount         = _pct(price, voucher.percent)
                price         -= amount
                applied[voucher.name] = amount

        if payment_info:
            price = self._apply_bank_offer(payment_info, price, applied)

        price = max(price, Decimal("0.00"))
        total_saved = original_price - price
        message = f"You saved ₹{total_saved:,.2f}!" if total_saved > 0 else "No discounts applied."

        return DiscountedPrice(
            original_price=original_price,
            final_price=price,
            applied_discounts=applied,
            message=message,
        )

    async def validate_discount_code(
        self,
        code: str,
        cart_items: list[CartItem],
        customer_tier: CustomerTier,
    ) -> tuple[bool, Optional[str]]:
        """Validate a voucher code against the cart and customer tier."""
        return self._check_voucher(code, cart_items, customer_tier)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _apply_brand_category(
        self,
        cart_items: list[CartItem],
        price: Decimal,
        applied: dict[str, Decimal],
    ) -> Decimal:
        """Apply brand then category discounts per line item."""
        for item in cart_items:
            item_price = item.product.base_price * item.quantity

            if rule := self._brands.get(item.product.brand.lower()):
                amt = _pct(item_price, rule.percent)
                applied[rule.name] = applied.get(rule.name, Decimal("0.00")) + amt
                item_price -= amt
                price -= amt

            if rule := self._categories.get(item.product.category.lower()):
                amt = _pct(item_price, rule.percent)
                applied[rule.name] = applied.get(rule.name, Decimal("0.00")) + amt
                price -= amt

        return price

    def _check_voucher(
        self,
        code: str,
        cart_items: list[CartItem],
        customer_tier: CustomerTier,
    ) -> tuple[bool, Optional[str]]:
        """Return (is_valid, failure_reason)."""
        voucher = self._vouchers.get(code.upper())
        if not voucher:
            return False, f"Voucher '{code}' does not exist or has expired."

        if _TIER_RANK[customer_tier] < _TIER_RANK[voucher.min_customer_tier]:
            return (
                False,
                f"Requires {voucher.min_customer_tier.value} tier or above. "
                f"Your tier: {customer_tier.value}.",
            )

        for item in cart_items:
            if item.product.brand.lower() in [b.lower() for b in voucher.excluded_brands]:
                return False, f"Brand '{item.product.brand}' is excluded from this voucher."
            if item.product.category.lower() in [c.lower() for c in voucher.excluded_categories]:
                return False, f"Category '{item.product.category}' is excluded from this voucher."

        return True, None

    def _apply_bank_offer(
        self,
        payment_info: PaymentInfo,
        price: Decimal,
        applied: dict[str, Decimal],
    ) -> Decimal:
        """Apply the first matching bank offer (one per transaction)."""
        for offer in self._bank_offers:
            if not offer.active:
                continue
            bank_match = offer.bank_name.lower() == (payment_info.bank_name or "").lower()
            card_match = offer.card_type is None or offer.card_type == payment_info.card_type
            if bank_match and card_match:
                amount              = _pct(price, offer.percent)
                price              -= amount
                applied[offer.name] = amount
                break
        return price