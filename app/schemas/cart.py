"""Request and response schemas for the cart endpoint."""

from uuid import UUID
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.discount import CardType, CustomerTier


class PaymentInfoSchema(BaseModel):
    method: str = Field(description="Payment method used at checkout.", examples=["CARD"])
    bank_name: Optional[str] = Field(default=None, description="Required when method is CARD.", examples=["ICICI"])
    card_type: Optional[CardType] = Field(default=None, description="CREDIT or DEBIT.", examples=["CREDIT"])


class CartRequest(BaseModel):
    cart_items: List[UUID] = Field(description="Product IDs to include in the order.", examples=[["11111111-1111-4111-8111-111111111111"]])
    customer_id: UUID = Field(description="ID of the customer placing the order.", examples=["22222222-2222-4222-8222-222222222222"])
    customer_tier: CustomerTier = Field(default=CustomerTier.REGULAR, description="Loyalty tier used for voucher eligibility.", examples=["regular"])
    voucher_code: Optional[str] = Field(default=None, description="Voucher code entered at checkout.", examples=["SUPER69"])
    payment: Optional[PaymentInfoSchema] = Field(default=None, description="Payment details required for bank offer matching.")


class CartDiscountResponse(BaseModel):
    original_price: Decimal = Field(description="Sum of base_price × quantity before any discounts.", examples=["1000.00"])
    final_price: Decimal = Field(description="Price after all applicable discounts.", examples=["486.00"])
    applied_discounts: Dict[str, Decimal] = Field(description="Each discount name mapped to the amount saved (₹).", examples=[{"PUMA 40% off": "400.00", "T-shirt extra 10%": "60.00", "ICICI 10% instant": "54.00"}])
    message: str = Field(description="Human-friendly savings summary shown to the customer.", examples=["You saved ₹514.00!"])