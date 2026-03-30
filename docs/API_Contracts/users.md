# Users API Contract

This document defines the API contract for user-related endpoints in the MVP version of the E-Commerce backend.

All endpoints require authentication unless stated otherwise.

---

# 1. Get Current User

## Request

**GET** `/users/me`

Rate limit: 30/minute

- No request body.
- Requires `Authorization: Bearer <access_token>`.

---

## Response (200 OK)

{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+201234567890"
}

---

## Errors

- `401 Unauthorized` — missing or invalid token, or account is inactive.
- `429 Too Many Requests` — rate limit exceeded.

---

# 2. Request Password Change

## Request

**PUT** `/users/me/password`

Rate limit: 2/minute

- Requires `Authorization: Bearer <access_token>`.

Request body:

{
  "current_password": "OldSecret123",
  "new_password": "NewSecret123"
}

## Validation Rules

- `new_password`: min 8 characters, must contain at least one letter and one digit.

---

## Response (200 OK)

{
  "message": "Confirmation email sent. Please check your inbox."
}

---

## Notes

- Does not change the password immediately.
- Sends a confirmation email with two links: confirm or deny.
- The confirmation token expires in 15 minutes.
- The actual password change only takes effect after the user clicks the confirm link.

---

## Errors

- `401 Unauthorized` — incorrect current password, or missing/invalid token.
- `422 Unprocessable Entity` — new password validation failure.
- `429 Too Many Requests` — rate limit exceeded.

---

# 3. Confirm Password Change

## Request

**GET** `/users/confirm-password-change`

Public endpoint (no auth required — accessed via email link).

Query parameter:

- `token` (string, required) — the confirmation token from the email link.

---

## Response (200 OK)

{
  "message": "Password updated successfully. Please login again."
}

---

## Notes

- Applies the pending password hash to the user's account.
- Revokes all active refresh tokens (forces re-login on all devices).

---

## Errors

- `400 Bad Request` — invalid or expired token.

---

# 4. Deny Password Change

## Request

**GET** `/users/deny-password-change`

Public endpoint (no auth required — accessed via email link).

Query parameter:

- `token` (string, required) — the confirmation token from the email link.

---

## Response (200 OK)

{
  "message": "Password change cancelled. All sessions logged out."
}

---

## Notes

- Clears the pending password change.
- Revokes all active refresh tokens (forces re-login on all devices as a security measure).
- Sends a security alert email to the user.

---

## Errors

- `400 Bad Request` — invalid token.

---

# 5. Deactivate Account

## Request

**DELETE** `/users/deactivate`

Rate limit: 3/minute

- Requires `Authorization: Bearer <access_token>`.

Request body:

{
  "password": "Secret123"
}

---

## Response (200 OK)

{
  "message": "Account deactivated"
}

---

## Notes

- Requires the user's current password as confirmation.
- Sets `is_active = false` on the account.
- Revokes all active refresh tokens.
- A deactivated account cannot log in or access protected endpoints.

---

## Errors

- `401 Unauthorized` — incorrect password, or missing/invalid token.
- `429 Too Many Requests` — rate limit exceeded.
