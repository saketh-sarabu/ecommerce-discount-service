"""Application entry point — wires dependencies and mounts routers."""

from fastapi import FastAPI

from app.api.router import router
from app.db.fake_data import BANK_OFFERS, BRAND_DISCOUNTS, CATEGORY_DISCOUNTS, VOUCHERS
from app.services.discount_service import DiscountService

app = FastAPI(
    title="Discount Service",
    description="Fashion e-commerce discount calculator.",
    version="1.0.0",
)

# Single shared instance — swap fake_data lists for DB-backed repos in production.
discount_service = DiscountService(
    brand_discounts=BRAND_DISCOUNTS,
    category_discounts=CATEGORY_DISCOUNTS,
    vouchers=VOUCHERS,
    bank_offers=BANK_OFFERS,
)

app.include_router(router)