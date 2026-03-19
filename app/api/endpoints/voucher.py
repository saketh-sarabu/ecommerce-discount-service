"""Voucher validation endpoint."""

from fastapi import APIRouter, HTTPException

from app.db.fake_data import PRODUCTS
from app.models.domain import CartItem
from app.schemas.voucher import ValidateVoucherRequest, ValidateVoucherResponse

router = APIRouter()


def get_service():
    """Return the shared DiscountService instance."""
    from app.main import discount_service
    return discount_service


@router.post(
    "/validate",
    response_model=ValidateVoucherResponse,
    summary="Validate a voucher code",
    response_description="Whether the code is redeemable and the reason if not.",
)
async def validate_voucher(body: ValidateVoucherRequest) -> ValidateVoucherResponse:
    """
    POST /v1/voucher/validate
    curl --location 'http://localhost:8000/v1/voucher/validate' \
         --header 'Content-Type: application/json' \
         --data '{"code":"SUPER69","customer_id":"22222222-2222-4222-8222-222222222222","customer_tier":"regular","cart_items":["11111111-1111-4111-8111-111111111111"]}'

    Check whether a voucher code can be applied given the customer tier and cart contents.

    Args:
        body: Voucher code, customer ID, customer tier, and list of product IDs in the cart.

    Returns:
        ValidateVoucherResponse with valid flag and optional rejection reason.

    Raises:
        404: A product ID in cart_items was not found.
        422: Request body failed validation.
        500: Internal server error.
    """
    cart_items = []
    for pid in body.cart_items:
        product = PRODUCTS.get(str(pid))
        if not product:
            raise HTTPException(status_code=404, detail=f"Product '{pid}' not found.")
        cart_items.append(CartItem(product=product, quantity=1, size="M"))

    valid, reason = await get_service().validate_discount_code(
        code=body.code,
        cart_items=cart_items,
        customer_tier=body.customer_tier,
    )
    return ValidateVoucherResponse(valid=valid, reason=reason)