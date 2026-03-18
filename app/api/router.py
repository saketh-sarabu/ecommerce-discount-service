"""V1 API router — registers all endpoint sub-routers."""

from fastapi import APIRouter

from app.api.endpoints import cart, voucher

router = APIRouter(prefix="/v1")

router.include_router(cart.router,    prefix="/cart",    tags=["Cart"])
router.include_router(voucher.router, prefix="/voucher", tags=["Voucher"])