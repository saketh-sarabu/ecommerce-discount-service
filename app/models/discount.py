"""Domain dataclasses — treated as black boxes per spec."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class BrandTier(str, Enum):
    PREMIUM = "premium"
    REGULAR = "regular"
    BUDGET  = "budget"


class DiscountType(str, Enum):
    BRAND    = "brand"
    CATEGORY = "category"
    VOUCHER  = "voucher"
    BANK     = "bank"


class CustomerTier(str, Enum):
    REGULAR  = "regular"
    SILVER   = "silver"
    GOLD     = "gold"
    PLATINUM = "platinum"


@dataclass
class Product:
    id: str
    brand: str
    brand_tier: BrandTier
    category: str
    base_price: Decimal
    current_price: Decimal  # after brand/category discount


@dataclass
class CartItem:
    product: Product
    quantity: int
    size: str


@dataclass
class PaymentInfo:
    method: str               # CARD, UPI, etc.
    bank_name: Optional[str]
    card_type: Optional[str]  # CREDIT, DEBIT


@dataclass
class DiscountedPrice:
    original_price: Decimal
    final_price: Decimal
    applied_discounts: Dict[str, Decimal]  # discount_name -> amount saved
    message: str