# Cart API Contract

This document defines the API contract for cart-related endpoints in the MVP version of the E-Commerce backend.

All endpoints require authentication.

---

# 1. View Cart

## Request

**GET** `/cart/`

Rate limit: 60/minute

- No request body.
- Requires `Authorization: Bearer <access_token>`.

---

## Response (200 OK)

Example:

{
  "cart_items": [
    {
      "id": 1,
      "product": {
        "id": 3,
        "name": "Laptop",
        "price": 1000.00,
        "image_url": "..."
      },
      "quantity": 2
    }
  ],
  "total_price": 2000.00
}

---

## Response Fields

- `cart_items`: list of items currently in the cart.
- `cart_items[].product`: embedded product snapshot (id, name, current price, image).
- `cart_items[].quantity`: quantity of that product in the cart.
- `total_price`: sum of (price × quantity) across all items.

---

## Notes

- Returns only the authenticated user's cart.
- An empty cart returns `200 OK` with `cart_items: []` and `total_price: 0`.
- `price` in the product reflects the current product price, not a snapshot.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `429 Too Many Requests` — rate limit exceeded.

---

# 2. Add Item to Cart

## Request

**POST** `/cart/`

Rate limit: 10/minute

- Requires `Authorization: Bearer <access_token>`.

Request body:

{
  "product_id": 3,
  "quantity": 2
}

## Validation Rules

- `quantity`: must be between 1 and 100.

---

## Response (201 Created)

Example:

{
  "id": 1,
  "product": {
    "id": 3,
    "name": "Laptop",
    "price": 1000.00,
    "image_url": "..."
  },
  "quantity": 2
}

---

## Notes

- If the product already exists in the cart, the quantity is incremented (not duplicated).
- Returns `404` if the product does not exist.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — product does not exist.
- `422 Unprocessable Entity` — quantity out of range.
- `429 Too Many Requests` — rate limit exceeded.

---

# 3. Update Cart Item Quantity

## Request

**PATCH** `/cart/{product_id}`

Rate limit: 10/minute

- `product_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.

Request body:

{
  "quantity": 5
}

## Validation Rules

- `quantity`: must be between 1 and 100.

---

## Response (200 OK)

Example:

{
  "id": 1,
  "product": {
    "id": 3,
    "name": "Laptop",
    "price": 1000.00,
    "image_url": "..."
  },
  "quantity": 5
}

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — item not in cart.
- `422 Unprocessable Entity` — quantity out of range.
- `429 Too Many Requests` — rate limit exceeded.

---

# 4. Remove Item from Cart

## Request

**DELETE** `/cart/{product_id}`

Rate limit: 10/minute

- `product_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.
- No request body.

---

## Response (204 No Content)

No response body.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — item not in cart.
- `429 Too Many Requests` — rate limit exceeded.
