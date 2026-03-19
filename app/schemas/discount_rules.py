"""Pydantic models for discount rule definitions (stored/validated config)."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.discount import CardType, CustomerTier, DiscountType


class DiscountRule(BaseModel):
    """Base fields shared by every discount rule."""
    name: str = Field(description="Label shown on the order summary.", examples=["PUMA 40% off"])
    discount_type: DiscountType = Field(description="Determines which calculation phase this rule belongs to.")
    percent: Decimal = Field(gt=0, le=100, description="Percentage deducted from the price at that phase.", examples=[10, 40])
    active: bool = Field(default=True, description="Inactive rules are ignored without deletion.")


class BrandDiscount(DiscountRule):
    """Applies across all categories for a single brand."""
    brand: str = Field(description="Brand name to match (case-insensitive).", examples=["PUMA"])
    discount_type: DiscountType = DiscountType.BRAND


class CategoryDiscount(DiscountRule):
    """Applies to all products within a category."""
    category: str = Field(description="Category name to match (case-insensitive).", examples=["t-shirts"])
    discount_type: DiscountType = DiscountType.CATEGORY


class VoucherDiscount(DiscountRule):
    """Coupon code redeemable at checkout."""
    code: str = Field(description="The code customers enter at checkout.", examples=["SUPER69"])
    excluded_brands: List[str] = Field(default_factory=list, description="Brands excluded from this voucher.", examples=[["Zara", "H&M"]])
    excluded_categories: List[str] = Field(default_factory=list, description="Categories excluded from this voucher.", examples=[["footwear"]])
    min_customer_tier: CustomerTier = Field(default=CustomerTier.REGULAR, description="Minimum loyalty tier required to redeem.", examples=["silver"])
    discount_type: DiscountType = DiscountType.VOUCHER


class BankOffer(DiscountRule):
    """Instant discount tied to a specific bank (and optionally card type)."""
    bank_name: str = Field(description="Bank to match against payment info (case-insensitive).", examples=["ICICI"])
    card_type: Optional[CardType] = Field(default=None, description="Restrict to CREDIT or DEBIT. Null means both are eligible.", examples=["CREDIT"])
    discount_type: DiscountType = DiscountType.BANK