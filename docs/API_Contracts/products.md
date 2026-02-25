# Products API Contract

This document defines the API contract for product-related endpoints in the MVP version of the E-Commerce backend.

---

# 1) List Products

## Request

**GET** `/products`

## Query Parameters (all optional)

- `limit` (int, default `20`, min `1`, max `100`)
- `offset` (int, default `0`, min `0`)
- `category_id` (int, optional)
- `min_price` (number/decimal, optional, min `0`)
- `max_price` (number/decimal, optional, min `0`)
- `q` (string, optional — search by name, future enhancement)
- `sort` (string, optional — e.g., `price`, `created_at`, future enhancement)
- `order` (string, optional — `asc` or `desc`, future enhancement)

## Validation Rules

- `limit` must be between 1 and 100.
- `offset` must be ≥ 0.
- `min_price` and `max_price` must be ≥ 0.
- If both `min_price` and `max_price` are provided, then `min_price <= max_price`.

---

## Response (200 OK)

Example:

{
  "items": [
    {
      "id": 1,
      "name": "T-shirt",
      "price": 250.00,
      "stock": 12,
      "image_url": "...",
      "rating": 4.7,
      "category_id": 3
      
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 57
}

---

## Response Fields

- `items`: list of product objects.
- `limit`: number of items requested.
- `offset`: number of items skipped.
- `total`: total number of matching products after filters (used for pagination UI).

---

## Notes

- `price` is returned as a numeric value.
- `rating` may be null if the product has no rating yet.
- `created_at` is an ISO 8601 datetime string.
- `total` reflects the count after filters are applied.

---

## Errors

- `422 Unprocessable Entity`
  - Invalid query parameter types.
  - Validation rule violations (e.g., limit out of range, invalid price range).


---


# 2) Product Details

## Request

**GET** `/products/{product_id}`

- `product_id` (int, required)

---

## Response (200 OK)

Example:

{
  "id": 1,
  "name": "T-shirt",
  "description": "Soft cotton t-shirt",
  "price": 250.00,
  "stock": 12,
  "image_url": "...",
  "rating": 4.3,
  "category": {
    "id": 3,
    "name": "Clothes"
  }
}

---

## Notes

- `price` reflects the current product price.
- `stock` reflects current available inventory.
- `category` is embedded for convenience.

---

## Errors

- `404 Not Found`
  - Returned when the product does not exist.
  - Should follow the project's standard error response format.

