# Admin Users API Contract

Admin-only endpoints for user management. All endpoints require a valid access token with `role = admin`. Non-admin requests receive `403 Forbidden`.

---

## 1) List All Users

### Request

**GET** `/admin/users/`

**Headers:** `Authorization: Bearer <access_token>`

### Query Parameters (all optional)

| Param | Type | Default | Notes |
|---|---|---|---|
| `limit` | integer | 10 | min 1, max 50 |
| `offset` | integer | 0 | min 0 |
| `role` | string | — | Filter by role: `customer`, `admin` |
| `is_active` | boolean | — | Filter by active state: `true`, `false` |

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "phone_number": "+1234567890",
      "role": "customer",
      "is_active": true,
      "is_verified": true
    }
  ],
  "limit": 10,
  "offset": 0,
  "total": 1
}
```

### Notes

- Returns users from all roles (not scoped to the requester).
- An empty result returns `200 OK` with `items: []`, not `404`.

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `422 Unprocessable Entity` | Invalid query parameter types or values |

---

## 2) Get Single User

### Request

**GET** `/admin/users/{user_id}`

**Headers:** `Authorization: Bearer <access_token>`

### Response (200 OK)

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "role": "customer",
  "is_active": true,
  "is_verified": true
}
```

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | User does not exist |

---

## 3) Deactivate User

### Request

**PATCH** `/admin/users/{user_id}/deactivate`

**Headers:** `Authorization: Bearer <access_token>`

No request body.

### Response (200 OK)

Returns the full user detail (same shape as Get Single User) with `is_active: false`.

### Notes

- Sets `is_active = False` on the user (soft deactivation — record is not deleted).
- Immediately revokes all of the user's refresh tokens, ending all active sessions.
- Admin cannot deactivate themselves.

### Errors

| Status | Reason |
|---|---|
| `400 Bad Request` | Admin targeting their own account |
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | User does not exist |
| `409 Conflict` | User is already inactive |

---

## 4) Reactivate User

### Request

**PATCH** `/admin/users/{user_id}/reactivate`

**Headers:** `Authorization: Bearer <access_token>`

No request body.

### Response (200 OK)

Returns the full user detail (same shape as Get Single User) with `is_active: true`.

### Notes

- Sets `is_active = True`. The user can authenticate again immediately.
- Does not restore revoked tokens — user will need to log in again.

### Errors

| Status | Reason |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | User does not exist |
| `409 Conflict` | User is already active |

---

## 5) Update User Role

### Request

**PATCH** `/admin/users/{user_id}/role`

**Headers:** `Authorization: Bearer <access_token>`

**Body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | string | yes | Target role: `customer` or `admin` |

Example:

```json
{
  "role": "admin"
}
```

### Response (200 OK)

Returns the full user detail (same shape as Get Single User) with the updated `role`.

### Notes

- Admin cannot change their own role (prevents self-demotion / accidental lockout).
- Promoting a customer to admin grants full access to all `/admin/*` endpoints immediately.
- Demoting an admin to customer revokes their admin access immediately on their next request (token still valid but role check will fail).

### Errors

| Status | Reason |
|---|---|
| `400 Bad Request` | Admin targeting their own account |
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated user is not admin |
| `404 Not Found` | User does not exist |
| `409 Conflict` | User already has the requested role |
| `422 Unprocessable Entity` | Invalid role value |

---

## Seed Script

**File:** `scripts/seed_admin.py`

A one-time bootstrap script for creating the first admin at deployment. Not an API endpoint.

Reads from environment variables:

| Variable | Description |
|---|---|
| `SEED_ADMIN_EMAIL` | Email for the first admin account |
| `SEED_ADMIN_PASSWORD` | Password for the first admin account |
| `SEED_ADMIN_FIRST_NAME` | First name |
| `SEED_ADMIN_LAST_NAME` | Last name |

Run once during initial deployment:

```bash
python scripts/seed_admin.py
```

- Creates the user with `role = admin`, `is_active = True`, `is_verified = True`.
- Fails with a clear error if an admin with that email already exists.
