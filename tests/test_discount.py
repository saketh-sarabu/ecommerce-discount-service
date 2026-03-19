"""
Discount stacking tests using fake_data seed.

  PUMA T-shirt base_price = ₹1000
  1. PUMA 40% brand       → saves ₹400  (price: ₹600)
  2. T-shirt 10% category → saves ₹60   (price: ₹540)
  3. ICICI 10% bank       → saves ₹54   (price: ₹486)
"""

from decimal import Decimal

import pytest

from app.db.fake_data import (
    BANK_OFFERS,
    BRAND_DISCOUNTS,
    CATEGORY_DISCOUNTS,
    ICICI_PAYMENT,
    SAMPLE_CART,
    VOUCHERS,
)
from app.models.discount import VoucherDiscount
from app.models.enums import CustomerTier
from app.services.discount_service import DiscountService


@pytest.fixture
def service() -> DiscountService:
    return DiscountService(
        brand_discounts=BRAND_DISCOUNTS,
        category_discounts=CATEGORY_DISCOUNTS,
        vouchers=VOUCHERS,
        bank_offers=BANK_OFFERS,
    )


@pytest.mark.asyncio
async def test_brand_category_bank_stacking(service: DiscountService) -> None:
    """All three discounts applied in order should yield ₹486."""
    result = await service.calculate_cart_discounts(
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
        payment_info=ICICI_PAYMENT,
    )

    assert result.original_price                          == Decimal("1000.00")
    assert result.applied_discounts["PUMA 40% off"]       == Decimal("400.00")
    assert result.applied_discounts["T-shirt extra 10%"]  == Decimal("60.00")
    assert result.applied_discounts["ICICI 10% instant"]  == Decimal("54.00")
    assert result.final_price                             == Decimal("486.00")


@pytest.mark.asyncio
async def test_brand_and_category_no_bank(service: DiscountService) -> None:
    """Without a bank offer the price should stop at ₹540."""
    result = await service.calculate_cart_discounts(
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
    )

    assert result.final_price == Decimal("540.00")
    assert "ICICI 10% instant" not in result.applied_discounts


@pytest.mark.asyncio
async def test_voucher_applied_after_brand_category(service: DiscountService) -> None:
    """SUPER69 (69%) applies to the ₹540 post-brand-category price."""
    result = await service.calculate_cart_discounts(
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
        voucher_code="SUPER69",
    )

    # 69% of 540 = 372.60 → final = 167.40
    assert result.applied_discounts.get("SUPER69") == Decimal("372.60")
    assert result.final_price == Decimal("167.40")


@pytest.mark.asyncio
async def test_validate_valid_voucher(service: DiscountService) -> None:
    valid, reason = await service.validate_discount_code(
        code="SUPER69",
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
    )
    assert valid is True
    assert reason is None


@pytest.mark.asyncio
async def test_validate_unknown_voucher(service: DiscountService) -> None:
    valid, reason = await service.validate_discount_code(
        code="DOESNOTEXIST",
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
    )
    assert valid is False
    assert "does not exist" in reason.lower() # type: ignore


@pytest.mark.asyncio
async def test_validate_tier_requirement(service: DiscountService) -> None:
    """A GOLD-only voucher should be rejected for a REGULAR customer."""
    gold_voucher = VoucherDiscount(
        name="GOLDONLY",
        code="GOLDONLY",
        percent=Decimal("20"),
        min_customer_tier=CustomerTier.GOLD,
    )
    svc = DiscountService(
        brand_discounts=[],
        category_discounts=[],
        vouchers=[gold_voucher],
        bank_offers=[],
    )
    valid, reason = await svc.validate_discount_code(
        code="GOLDONLY",
        cart_items=SAMPLE_CART,
        customer_tier=CustomerTier.REGULAR,
    )
    assert valid is False
    assert "gold" in reason.lower() # type: ignore