# Technical Overview

## System Architecture

The service follows a clean layered architecture. Each layer has a single responsibility and depends only on the layer below it.

```
HTTP Request
     │
     ▼
┌─────────────────────────────┐
│  API Layer (app/api/)       │  Routing, request validation, response mapping
│  cart.py / voucher.py       │
└─────────────┬───────────────┘
              │  domain types
              ▼
┌─────────────────────────────┐
│  Service Layer              │  All discount calculation and validation logic
│  discount_service.py        │
└─────────────────────────────┘
              │  reads rules from
              ▼
┌─────────────────────────────┐
│  Data Layer (app/db/)       │  In-memory seed data (products, rules)
│  fake_data.py               │
└─────────────────────────────┘
```

---

## Module Responsibilities

### `app/main.py`
FastAPI application entry point. Instantiates `DiscountService` with seed rules from `fake_data.py` and mounts the v1 router. The single shared `DiscountService` instance is injected into endpoints via a deferred import in `get_service()`.

### `app/api/router.py`
Registers `cart` and `voucher` sub-routers under the `/v1` prefix.

### `app/api/endpoints/cart.py`
Handles `POST /v1/cart/calculate`. Resolves product UUIDs against the in-memory store, maps the request schema to domain types, delegates to `DiscountService`, and maps the result back to the response schema.

### `app/api/endpoints/voucher.py`
Handles `POST /v1/voucher/validate`. Resolves product UUIDs, delegates validation to `DiscountService`, and returns a structured valid/reason response.

### `app/services/discount_service.py`
Contains all business logic. Stateless except for rule indexes built at construction time (dicts keyed by brand/category/code for O(1) lookups).

### `app/models/discount.py`
Domain dataclasses treated as black boxes per spec (`Product`, `CartItem`, `PaymentInfo`, `DiscountedPrice`). No business logic lives here.

### `app/schemas/`
Pydantic request/response models (`cart.py`, `voucher.py`) and rule configuration models (`discount_rules.py`). All fields carry `description` and `examples` for OpenAPI generation.

### `app/db/fake_data.py`
In-memory seed data — stands in for a database. Defines the scenario: one PUMA T-shirt at ₹1000, a 40% brand discount, 10% category discount, SUPER69 voucher (69%), and ICICI 10% bank offer.

---

## Discount Calculation

### Stacking Order

Discounts are applied in three sequential phases. Each phase operates on the price produced by the previous one.

```
Phase 1 — Brand & Category (per line item, from base_price)
  └─ Brand discount applied first, then category discount on the reduced price.

Phase 2 — Voucher code (applied to the Phase 1 total)

Phase 3 — Bank offer (applied to the Phase 2 total, first matching offer wins)
```

### Example: PUMA T-shirt @ ₹1000, ICICI CREDIT card

| Phase | Discount | Calculation | Saved | Running Price |
|-------|----------|-------------|-------|---------------|
| 1a | PUMA 40% brand | 40% × ₹1000 | ₹400 | ₹600 |
| 1b | T-shirt 10% category | 10% × ₹600 | ₹60 | ₹540 |
| 3 | ICICI 10% bank | 10% × ₹540 | ₹54 | **₹486** |

### Voucher Validation Rules

A voucher is rejected if any of the following are true:
- The code does not exist or is inactive.
- The customer's tier is below `min_customer_tier`.
- Any item in the cart belongs to an excluded brand.
- Any item in the cart belongs to an excluded category.

---

## Key Design Decisions

**Rule indexing at construction time**
`DiscountService.__init__` builds `dict` indexes keyed by brand name, category name, and voucher code (all lowercased/uppercased). Lookups during request handling are O(1).

**`DiscountType` enum on rule schemas**
Each rule schema (`BrandDiscount`, `CategoryDiscount`, etc.) fixes its `discount_type` field as a class-level default. This makes the type self-describing in OpenAPI output and prevents misconfiguration.

**`CustomerTier` rank map**
Tier comparisons use a `_TIER_RANK` dict (`REGULAR=0 … PLATINUM=3`) rather than enum ordering, making the intent explicit and the comparison a single integer comparison.

**In-memory data store**
`fake_data.py` acts as the data layer. Replacing it with a real database requires only updating the rule lists passed to `DiscountService` in `main.py` — the service and endpoints are unaffected.

**No `CustomerProfile` wrapper**
The spec's `CustomerProfile` is not modelled as a dataclass. Only `customer_tier` is needed for discount logic, so it is passed directly. This avoids an unnecessary wrapper with no behaviour.

---

## Data Flow Diagram

```
POST /v1/cart/calculate
        │
        │  CartRequest (Pydantic)
        ▼
  cart.py endpoint
        │  resolves UUIDs → CartItem[]
        │  maps PaymentInfoSchema → PaymentInfo
        ▼
  DiscountService.calculate_cart_discounts()
        │
        ├─ _apply_brand_category(cart_items)
        │       └─ per item: brand rule lookup → category rule lookup
        │
        ├─ _check_voucher(code, cart_items, tier)   [if voucher_code]
        │       └─ existence → tier → exclusion checks
        │
        └─ _apply_bank_offer(payment_info)           [if payment_info]
                └─ first matching offer (bank + card_type)
        │
        ▼
  DiscountedPrice (domain dataclass)
        │
        ▼
  CartDiscountResponse (Pydantic)
```
