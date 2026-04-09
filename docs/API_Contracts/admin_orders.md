# Admin Orders API Contract

Admin-only endpoints for order management. All endpoints require a valid access token with `role = admin`. Non-admin requests receive `403 Forbidden`.

---

## 1) List All Orders

### Request

**GET** `/admin/orders/`

**Headers:** `Authorization: Bearer <access_token>`

### Query Parameters (all optional)

| Param | Type | Default | Notes |
|---|---|---|---|
| `limit` | integer | 10 | min 1, max 50 |
| `offset` | integer | 0 | min 0 |
| `status` | string | — | Filter by order status: `pending`, `confirmed`, `completed`, `cancelled` |

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "user_id": 5,
      "total_amount": 1050.00,
      "status": "pending",
      "created_at": "2026-04-09T10:00:00"
    }
  ],
  "limit": 10,
  "offset": 0,
  "total": 1
}
```

### Notes

- Returns orders from all users (not scoped to the requester).
- Orders are returned newest first (`created_at DESC`).
- `user_id` is included in each item (admin projection).
- An empty result returns `200 OK` with `items: []`, not `404`.

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `422 Unprocessable Entity` | Invalid query parameter types or values |

---

## 2) Update Order Status

### Request

**PATCH** `/admin/orders/{order_id}/status`

**Headers:** `Authorization: Bearer <access_token>`

**Body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | string | yes | Target status: `confirmed` or `completed` |

Example:

```json
{
  "status": "confirmed"
}
```

### Response (200 OK)

Returns the full order detail with items and nested products:

```json
{
  "id": 1,
  "user_id": 5,
  "total_amount": 1050.00,
  "status": "confirmed",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 3,
        "name": "Laptop",
        "price": 1000.00,
        "image_url": "..."
      },
      "price_at_time": 1000.00,
      "quantity": 1,
      "subtotal": 1000.00
    }
  ],
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:05:00"
}
```

### Allowed Transitions (Forward-Only FSM)

| From | To |
|---|---|
| `pending` | `confirmed` |
| `confirmed` | `completed` |

Cancellation is handled by the separate cancel endpoint — not by this endpoint.

`completed` and `cancelled` are terminal states with no valid transitions.

### Notes

- The order row is locked (`SELECT FOR UPDATE`) before validation to prevent race conditions.
- `user_id` is included in the response (admin projection).

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | Order does not exist |
| `409 Conflict` | Same status, invalid transition, or terminal state |
| `422 Unprocessable Entity` | Invalid body (missing field, invalid status value) |

---

## 3) Cancel Order

### Request

**POST** `/admin/orders/{order_id}/cancel`

**Headers:** `Authorization: Bearer <access_token>`

No request body.

### Response (200 OK)

Returns the full order detail (same shape as Update Order Status response) with `status` set to `"cancelled"`.

### Notes

- Admin can cancel orders in `PENDING` or `CONFIRMED` status (broader policy than customer cancel, which is `PENDING` only).
- On successful cancellation:
  - Order status is set to `cancelled`.
  - Stock is restored for each order item.
  - An `InventoryChange` record is logged per item with `reason="cancellation"`.
  - Product rows are locked in deterministic order (by `product_id`) to prevent deadlocks.
  - The entire operation is atomic — if any step fails, the whole transaction rolls back.
- No ownership check — admin can cancel any user's order.

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | Order does not exist |
| `409 Conflict` | Order is already `completed` or `cancelled` |