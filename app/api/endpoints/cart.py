"""Cart discount endpoint."""

from fastapi import APIRouter, HTTPException

from app.db.fake_data import PRODUCTS
from app.models.domain import CartItem, PaymentInfo
from app.schemas.cart import CartDiscountResponse, CartRequest
from app.services.discount_service import DiscountService

router = APIRouter()


def get_service() -> DiscountService:
    """Return the shared DiscountService instance."""
    from app.main import discount_service
    return discount_service


@router.post(
    "/calculate",
    response_model=CartDiscountResponse,
    summary="Calculate cart discounts",
    response_description="Final price and breakdown of every applied discount.",
)
async def calculate_cart_discounts(body: CartRequest) -> CartDiscountResponse:
    """
    POST /v1/cart/calculate
    curl --location 'http://localhost:8000/v1/cart/calculate' \
         --header 'Content-Type: application/json' \
         --data '{"cart_items":["11111111-1111-4111-8111-111111111111"],"customer_tier":"regular","payment":{"method":"CARD","bank_name":"ICICI","card_type":"CREDIT"}}'

    Resolve product IDs, apply all eligible discounts in order, and return the final price.

    Args:
        body: Cart contents, customer tier, optional voucher code, and optional payment info.

    Returns:
        CartDiscountResponse with original price, final price, per-discount savings, and a summary message.

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

    payment = None
    if body.payment:
        payment = PaymentInfo(
            method=body.payment.method,
            bank_name=body.payment.bank_name,
            card_type=body.payment.card_type,
        )

    result = await get_service().calculate_cart_discounts(
        cart_items=cart_items,
        customer_tier=body.customer_tier,
        payment_info=payment,
        voucher_code=body.voucher_code,
    )

    return CartDiscountResponse(
        original_price=result.original_price,
        final_price=result.final_price,
        applied_discounts=result.applied_discounts,
        message=result.message,
    )