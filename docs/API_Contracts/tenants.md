# Tenants API Contract

This document defines the API contract for tenant registration and management endpoints.

---

# 1. Register Tenant

## Request

**POST** `/tenants/register`

Rate limit: 3/minute

Request body:

{
  "name": "Acme Store",
  "slug": "acme-store",
  "plan": "free"
}

## Validation Rules

- `name`: required, max 100 characters.
- `slug`: required, 3–50 characters, must match `^[a-z0-9][a-z0-9-]{2,49}$` — lowercase letters, digits, hyphens only, no leading hyphen.
- `plan`: optional, default `"free"`. Valid values: `"free"` | `"pro"` | `"enterprise"`.

---

## Response (201 Created)

{
  "id": "<uuid7>",
  "name": "Acme Store",
  "slug": "acme-store",
  "plan": "free",
  "is_active": true,
  "created_at": "<iso8601>",
  "api_key": "vnx_xKp...47chars",
  "message": "Tenant created successfully. The owner account was automatically registered as the tenant administrator and can log in to the store using the same credentials."
}

---

## Notes

- The `api_key` is shown **exactly once** in this response. It is never stored in plaintext — only a SHA256 hash is persisted. If lost, use the key rotation endpoint (Story 2.5) to issue a new one. The client is responsible for displaying an appropriate warning to the user.
- The `api_key` is always prefixed with `vnx_` for identification and secret-scanning compatibility.
- The `id` is a UUID7 — time-ordered, safe against business leakage, and compatible with distributed systems.
- The `slug` is immutable after registration and will appear in per-tenant webhook URLs.

---

## Errors

- `409 Conflict` — slug is already taken by another tenant.
- `422 Unprocessable Entity` — slug fails regex, name exceeds 100 characters, or invalid plan value.
- `429 Too Many Requests` — rate limit exceeded.