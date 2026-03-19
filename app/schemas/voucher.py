"""Request and response schemas for the voucher endpoint."""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import CustomerTier


class ValidateVoucherRequest(BaseModel):
    code: str = Field(description="Voucher code to validate.", examples=["SUPER69"])
    customer_id: UUID = Field(description="ID of the customer attempting to redeem.", examples=["22222222-2222-4222-8222-222222222222"])
    customer_tier: CustomerTier = Field(default=CustomerTier.REGULAR, description="Customer's loyalty tier — checked against voucher requirements.", examples=["regular"])
    cart_items: List[UUID] = Field(default_factory=list, description="Product IDs in the cart — used to check brand/category exclusions.", examples=[["11111111-1111-4111-8111-111111111111"]])


class ValidateVoucherResponse(BaseModel):
    valid: bool = Field(description="Whether the voucher can be applied to the current cart.")
    reason: Optional[str] = Field(default=None, description="Populated only when valid=False; explains the rejection.", examples=["Brand 'Zara' is excluded from this voucher."])