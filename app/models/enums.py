"""Enum types for discount and product categorization."""

from enum import Enum


class BrandTier(str, Enum):
    PREMIUM = "premium"
    REGULAR = "regular"
    BUDGET = "budget"


class DiscountType(str, Enum):
    BRAND = "brand"
    CATEGORY = "category"
    VOUCHER = "voucher"
    BANK = "bank"


class CustomerTier(str, Enum):
    REGULAR = "regular"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class CardType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"
