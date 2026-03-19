"""
Discount calculation logic.

Stacking order:
  1. Brand / category discounts  (applied to base_price, per line item)
  2. Voucher code                (applied to eligible items after step 1)
  3. Bank offer                  (applied to total after step 2)
"""

from decimal import Decimal
from typing import Optional

from app.models.discount import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
from app.models.domain import CartItem, DiscountedPrice, PaymentInfo
from app.models.enums import CustomerTier

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
        self._brands      = {d.brand.lower(): d    for d in brand_discounts    if d.active}
        self._categories  = {d.category.lower(): d for d in category_discounts if d.active}
        self._vouchers    = {v.code.upper(): v     for v in vouchers           if v.active}
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

        price, item_prices = self._apply_brand_category(cart_items, price, applied)

        if voucher_code:
            valid, _ = self._check_voucher(voucher_code, customer_tier)
            if valid:
                voucher = self._vouchers[voucher_code.upper()]
                eligible_subtotal = self._voucher_eligible_subtotal(voucher, cart_items, item_prices)
                if eligible_subtotal > 0:
                    amount = _pct(eligible_subtotal, voucher.percent)
                    price -= amount
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
        """Validate a voucher code against existence and customer tier."""
        return self._check_voucher(code, customer_tier)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _apply_brand_category(
        self,
        cart_items: list[CartItem],
        price: Decimal,
        applied: dict[str, Decimal],
    ) -> tuple[Decimal, list[Decimal]]:
        """Apply brand then category discounts per line item; return updated total and per-item prices."""
        item_prices: list[Decimal] = []

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
                item_price -= amt
                price -= amt

            item_prices.append(item_price)

        return price, item_prices

    def _check_voucher(
        self,
        code: str,
        customer_tier: CustomerTier,
    ) -> tuple[bool, Optional[str]]:
        """Return (is_valid, failure_reason) — checks existence and tier only."""
        voucher = self._vouchers.get(code.upper())
        if not voucher:
            return False, f"Voucher '{code}' does not exist or has expired."

        if _TIER_RANK[customer_tier] < _TIER_RANK[voucher.min_customer_tier]:
            return (
                False,
                f"Requires {voucher.min_customer_tier.value} tier or above. "
                f"Your tier: {customer_tier.value}.",
            )

        return True, None

    def _voucher_eligible_subtotal(
        self,
        voucher: VoucherDiscount,
        cart_items: list[CartItem],
        item_prices: list[Decimal],
    ) -> Decimal:
        """Sum the post-phase-1 prices of items not excluded by the voucher's brand/category rules."""
        excluded_brands      = {b.lower() for b in voucher.excluded_brands}
        excluded_categories  = {c.lower() for c in voucher.excluded_categories}
        return sum(
            (
                price for item, price in zip(cart_items, item_prices)
                if item.product.brand.lower()    not in excluded_brands
                and item.product.category.lower() not in excluded_categories
            ),
            Decimal("0.00"),
        )

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
                amount               = _pct(price, offer.percent)
                price               -= amount
                applied[offer.name]  = amount
                break
        return price
