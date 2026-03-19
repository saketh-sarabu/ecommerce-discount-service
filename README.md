# Discount Service

Fashion e-commerce discount calculator. Applies brand, category, voucher, and bank offer discounts in a defined stacking order and exposes the result via a REST API.

---

## Overview

- **Stack:** Python 3.12+, FastAPI, Uvicorn, Pydantic v2, pytest + pytest-asyncio
- **Discount stacking order:** brand/category → voucher → bank offer
- **Data layer:** in-memory seed data (`app/db/fake_data.py`) — no database used
- **Docs:** interactive OpenAPI UI at `http://localhost:8000/docs`

---

## Project Structure

```
app/
├── main.py                  # Entry point — wires DiscountService and mounts routers
├── api/
│   ├── router.py            # /v1 prefix, registers sub-routers
│   └── endpoints/
│       ├── cart.py          # POST /v1/cart/calculate
│       └── voucher.py       # POST /v1/voucher/validate
├── services/
│   └── discount_service.py  # All discount calculation and validation logic
├── schemas/
│   ├── cart.py              # CartRequest, CartDiscountResponse
│   └── voucher.py           # ValidateVoucherRequest, ValidateVoucherResponse
├── models/
│   ├── discount.py          # Discount rule Pydantic models (BrandDiscount, VoucherDiscount, BankOffer, etc.)
│   ├── domain.py            # Domain dataclasses (Product, CartItem, PaymentInfo, DiscountedPrice)
│   └── enums.py             # Enums (CustomerTier, DiscountType, BrandTier, CardType)
└── db/
    └── fake_data.py         # In-memory seed products and discount rules
tests/
└── test_discount.py
documentation/
├── API.md                   # Endpoint reference with sample requests and curl examples
└── technical.md             # Architecture, design decisions, and data flow
```

---

## Setup

### a. With uv (recommended)

```bash
# Install uv if you don't have it
pip install uv

# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest tests/ -v
```

### b. With pip

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
pytest tests/ -v
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/cart/calculate` | Calculate final cart price after all eligible discounts |
| `POST` | `/v1/voucher/validate` | Validate a voucher code against customer tier and cart |

Full request/response reference: [`documentation/API.md`](documentation/API.md)

### Quick example

#### Scenario (seed data)

| Item | Base Price | Discounts Applied |
|------|-----------|-------------------|
| PUMA T-shirt (size M) | ₹1000 | 40% brand → 10% category → 10% ICICI bank |

Final price with all three: **₹486**

```bash
curl --location 'http://localhost:8000/v1/cart/calculate' \
     --header 'Content-Type: application/json' \
     --data '{
       "cart_items": ["11111111-1111-4111-8111-111111111111"],
       "customer_tier": "regular",
       "customer_id": "22222222-2222-4222-8222-222222222222",
       "payment": { "method": "CARD", "bank_name": "ICICI", "card_type": "CREDIT" }
     }'
```

```json
{
  "original_price": "1000.00",
  "final_price": "486.00",
  "applied_discounts": {
    "PUMA 40% off": "400.00",
    "T-shirt extra 10%": "60.00",
    "ICICI 10% instant": "54.00"
  },
  "message": "You saved ₹514.00!"
}
```

---

## Assumptions & Design Decisions

- **`CustomerProfile` omitted** — only `customer_tier` is needed for discount logic; wrapping it in a profile dataclass adds no value.
- **Discounts applied sequentially, not stacked** — each discount applies to the price after previous discounts have been deducted. Example: if an item costs ₹1000, a 40% brand discount makes it ₹600, then a 10% category discount applies to ₹600 (not ₹1000), resulting in ₹540. Discounts compound but don't stack independently.
- **Single bank offer per transaction** — the first matching offer is applied and the rest are skipped, consistent with how real checkout flows work.
- **Brand then category, per line item** — the category discount applies to the already brand-discounted item price, not to `base_price`. This matches the spec's "Min 40% off on PUMA, then extra 10% on T-shirts" wording.
- **Voucher exclusions are item-level, not cart-level** — if a voucher excludes a brand or category, the discount is applied only to the eligible items in the cart; excluded items are skipped. For example, if a voucher excludes "footwear" and the cart has 1 T-shirt and 1 pair of shoes, the voucher applies to the T-shirt only.
- **No `current_price` used in calculations** — `base_price` is always the starting point for Phase 1 so that discount amounts are stable regardless of how `current_price` was set.

For architecture details see [`documentation/technical.md`](documentation/technical.md).
For API documentation see [`documentation/API.md`](documentation/API.md).
