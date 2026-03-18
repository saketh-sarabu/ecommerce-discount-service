# API Documentation

Base URL: `http://localhost:8000`

---

## Routers

| Router | Prefix | Description |
|--------|--------|-------------|
| Cart | `/v1/cart` | Calculate final cart price after all eligible discounts |
| Voucher | `/v1/voucher` | Validate voucher codes against customer tier and cart |

---

## POST /v1/cart/calculate

Calculate the final cart price by applying all eligible discounts in stacking order: brand/category → voucher → bank offer.

### Request Body

```json
{
  "cart_items": ["11111111-1111-4111-8111-111111111111"],
  "customer_id": "22222222-2222-4222-8222-222222222222",
  "customer_tier": "regular",
  "voucher_code": "SUPER69",
  "payment": {
    "method": "CARD",
    "bank_name": "ICICI",
    "card_type": "CREDIT"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cart_items` | `UUID[]` | Yes | Product IDs to include in the order |
| `customer_id` | `UUID` | Yes | ID of the customer placing the order |
| `customer_tier` | `string` | No (default: `regular`) | Loyalty tier: `regular`, `silver`, `gold`, `platinum` |
| `voucher_code` | `string` | No | Voucher code entered at checkout |
| `payment` | `object` | No | Payment details for bank offer matching |
| `payment.method` | `string` | Yes (if payment) | `CARD`, `UPI`, etc. |
| `payment.bank_name` | `string` | No | Required when method is `CARD` |
| `payment.card_type` | `string` | No | `CREDIT` or `DEBIT` |

### Sample curl

```bash
curl --location 'http://localhost:8000/v1/cart/calculate' \
     --header 'Content-Type: application/json' \
     --data '{
       "cart_items": ["11111111-1111-4111-8111-111111111111"],
       "customer_id": "22222222-2222-4222-8222-222222222222",
       "customer_tier": "regular",
       "payment": {
         "method": "CARD",
         "bank_name": "ICICI",
         "card_type": "CREDIT"
       }
     }'
```

### Response — `200 OK`

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

| Field | Type | Description |
|-------|------|-------------|
| `original_price` | `Decimal` | Sum of `base_price × quantity` before any discounts |
| `final_price` | `Decimal` | Price after all applicable discounts |
| `applied_discounts` | `object` | Each discount name mapped to the amount saved (₹) |
| `message` | `string` | Human-friendly savings summary |

### Errors

| Code | Description |
|------|-------------|
| `404` | A product ID in `cart_items` was not found |
| `422` | Request body failed validation |
| `500` | Internal server error |

---

## POST /v1/voucher/validate

Check whether a voucher code can be applied given the customer's loyalty tier and cart contents (used for brand/category exclusion checks).

### Request Body

```json
{
  "code": "SUPER69",
  "customer_id": "22222222-2222-4222-8222-222222222222",
  "customer_tier": "regular",
  "cart_items": ["11111111-1111-4111-8111-111111111111"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | `string` | Yes | Voucher code to validate |
| `customer_id` | `UUID` | Yes | ID of the customer attempting to redeem |
| `customer_tier` | `string` | No (default: `regular`) | Loyalty tier: `regular`, `silver`, `gold`, `platinum` |
| `cart_items` | `UUID[]` | No | Product IDs — used to check brand/category exclusions |

### Sample curl

```bash
curl --location 'http://localhost:8000/v1/voucher/validate' \
     --header 'Content-Type: application/json' \
     --data '{
       "code": "SUPER69",
       "customer_id": "22222222-2222-4222-8222-222222222222",
       "customer_tier": "regular",
       "cart_items": ["11111111-1111-4111-8111-111111111111"]
     }'
```

### Response — `200 OK`

**Valid voucher:**
```json
{
  "valid": true,
  "reason": null
}
```

**Invalid voucher:**
```json
{
  "valid": false,
  "reason": "Requires gold tier or above. Your tier: regular."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `valid` | `bool` | Whether the voucher can be applied |
| `reason` | `string \| null` | Populated only when `valid=false`; explains the rejection |

### Errors

| Code | Description |
|------|-------------|
| `404` | A product ID in `cart_items` was not found |
| `422` | Request body failed validation |
| `500` | Internal server error |
