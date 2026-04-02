# Admin Products API Contract

Admin-only endpoints for product management. All endpoints require a valid access token with `role = admin`. Non-admin requests receive `403 Forbidden`.

---

## 1) Create Product

### Request

**POST** `/admin/products/`

**Headers:** `Authorization: Bearer <access_token>`

**Body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | |
| `price` | decimal | yes | must be >= 0 |
| `stock` | integer | yes | must be >= 0 |
| `category_id` | integer | yes | must reference existing category |
| `description` | string | no | |
| `image_url` | string | no | |

Example:

```json
{
  "name": "T-shirt",
  "description": "Soft cotton t-shirt",
  "price": 250.00,
  "stock": 50,
  "image_url": "https://example.com/img/tshirt.jpg",
  "category_id": 3
}
```

### Response (201 Created)

Returns the full product detail:

```json
{
  "id": 12,
  "name": "T-shirt",
  "description": "Soft cotton t-shirt",
  "price": 250.00,
  "stock": 50,
  "image_url": "https://example.com/img/tshirt.jpg",
  "rating": null,
  "category": {
    "id": 3,
    "name": "Clothes",
    "description": null
  },
  "created_at": "2026-04-01T10:00:00",
  "updated_at": "2026-04-01T10:00:00"
}
```

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | `category_id` does not exist |
| `422 Unprocessable Entity` | Validation failure (missing required fields, invalid types, negative price/stock) |

---

## 2) Partial Update Product

### Request

**PATCH** `/admin/products/{product_id}`

**Headers:** `Authorization: Bearer <access_token>`

All body fields are optional. Only provided fields are updated.

| Field | Type | Notes |
|---|---|---|
| `name` | string | |
| `price` | decimal | must be >= 0 |
| `stock` | integer | must be >= 0 |
| `category_id` | integer | must reference existing category |
| `description` | string | |
| `image_url` | string | |

Example (update price and stock only):

```json
{
  "price": 199.99,
  "stock": 30
}
```

### Response (200 OK)

Returns the updated full product detail (same shape as create response).

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | Product not found, or new `category_id` does not exist |
| `422 Unprocessable Entity` | Validation failure |

---

## 3) Delete Product

### Request

**DELETE** `/admin/products/{product_id}`

**Headers:** `Authorization: Bearer <access_token>`

No request body.

### Response (204 No Content)

No body.

### Side effects

- All cart items referencing this product are automatically removed (DB-level FK cascade).

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | Product not found |
| `409 Conflict` | Product is referenced by one or more orders and cannot be deleted |

---

## Notes

- `rating` is a computed field (from reviews, Epic 3). It is never accepted as input in create or update.
- PATCH semantics: fields omitted from the request body are left unchanged.
- Hard delete is used. Soft delete is not implemented in MVP.
