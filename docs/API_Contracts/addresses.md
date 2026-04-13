# Addresses API Contract

This document defines the API contract for address management endpoints in the MVP version of the E-Commerce backend.

All endpoints require authentication.

---

# 1. Create Address

## Request

**POST** `/addresses/`

Rate limit: 10/minute

- Requires `Authorization: Bearer <access_token>`.

Request body:

{
  "street": "123 Nile St",
  "city": "Cairo",
  "country": "Egypt",
  "postal_code": "11511",
  "label": "Home",
  "state": "Cairo Governorate",
  "is_default": true
}

## Validation Rules

- `street`, `city`, `country`, `postal_code`: required.
- `label`, `state`: optional.
- `is_default`: optional, defaults to `false`.

---

## Response (201 Created)

Example:

{
  "id": 1,
  "user_id": 5,
  "label": "Home",
  "street": "123 Nile St",
  "city": "Cairo",
  "state": "Cairo Governorate",
  "country": "Egypt",
  "postal_code": "11511",
  "is_default": true,
  "created_at": "2026-04-12T10:00:00"
}

---

## Notes

- If this is the user's first address, it is automatically set as default regardless of `is_default`.
- If `is_default: true`, any previously default address is unset first.
- Address belongs to the authenticated user — cannot create addresses for other users.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `422 Unprocessable Entity` — required fields missing.
- `429 Too Many Requests` — rate limit exceeded.

---

# 2. List Addresses

## Request

**GET** `/addresses/`

Rate limit: 30/minute

- No request body.
- Requires `Authorization: Bearer <access_token>`.

---

## Response (200 OK)

Example:

[
  {
    "id": 1,
    "user_id": 5,
    "label": "Home",
    "street": "123 Nile St",
    "city": "Cairo",
    "state": "Cairo Governorate",
    "country": "Egypt",
    "postal_code": "11511",
    "is_default": true,
    "created_at": "2026-04-12T10:00:00"
  }
]

---

## Notes

- Returns only the authenticated user's addresses.
- An empty list returns `200 OK` with `[]`.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `429 Too Many Requests` — rate limit exceeded.

---

# 3. Get Address

## Request

**GET** `/addresses/{address_id}`

Rate limit: 30/minute

- `address_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.

---

## Response (200 OK)

Returns a single address object (same shape as above).

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — address does not exist or belongs to another user.
- `429 Too Many Requests` — rate limit exceeded.

---

# 4. Update Address

## Request

**PUT** `/addresses/{address_id}`

Rate limit: 10/minute

- `address_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.

Request body (all fields optional):

{
  "street": "456 Pyramids Ave",
  "city": "Giza",
  "country": "Egypt",
  "postal_code": "12556",
  "label": "Work",
  "state": null,
  "is_default": false
}

---

## Response (200 OK)

Returns the updated address object.

---

## Notes

- Only the provided fields are updated (partial update).
- Ownership is enforced: a user can only update their own addresses.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — address does not exist or belongs to another user.
- `429 Too Many Requests` — rate limit exceeded.

---

# 5. Delete Address

## Request

**DELETE** `/addresses/{address_id}`

Rate limit: 10/minute

- `address_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.
- No request body.

---

## Response (204 No Content)

No response body.

---

## Notes

- Ownership is enforced: a user can only delete their own addresses.
- If the address is referenced by an existing order, the order's `address_id` is set to `NULL` (the order is preserved).
- If the deleted address was the default, no new default is set automatically.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — address does not exist or belongs to another user.
- `429 Too Many Requests` — rate limit exceeded.

---

# 6. Set Default Address

## Request

**POST** `/addresses/{address_id}/set-default`

Rate limit: 10/minute

- `address_id` (int, required, path parameter)
- Requires `Authorization: Bearer <access_token>`.
- No request body.

---

## Response (200 OK)

Returns the updated address object with `is_default: true`.

---

## Notes

- Clears the `is_default` flag on all other addresses for the user first.
- Ownership is enforced.

---

## Errors

- `401 Unauthorized` — missing or invalid token.
- `404 Not Found` — address does not exist or belongs to another user.
- `429 Too Many Requests` — rate limit exceeded.