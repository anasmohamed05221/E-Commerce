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

- The `api_key` is shown **exactly once** in this response. It is never stored in plaintext — only a SHA256 hash is persisted. If lost, use the key rotation endpoint to issue a new one. The client is responsible for displaying an appropriate warning to the user.
- The `api_key` is always prefixed with `vnx_` for identification and secret-scanning compatibility.
- The `id` is a UUID7 — time-ordered, safe against business leakage, and compatible with distributed systems.
- The `slug` is immutable after registration and will appear in per-tenant webhook URLs.

---

## Errors

- `409 Conflict` — slug is already taken by another tenant.
- `422 Unprocessable Entity` — slug fails regex, name exceeds 100 characters, or invalid plan value.
- `429 Too Many Requests` — rate limit exceeded.

---

# 2. Rotate API Key

## Request

**POST** `/tenants/me/rotate-api-key`

Auth: `X-Tenant-API-Key` header or `Authorization: Bearer <jwt>`

Rate limit: 3/minute per tenant (keyed on `tenant_id`, not IP)

No request body.

## Response (200 OK)

```json
{
  "api_key": "vnx_...new key...",
  "message": "New API key issued. Save it now — it will not be shown again."
}
```

## Notes

- Rotation is atomic — old key revoked and new key written in a single transaction. No window where neither key is valid.
- The old key is immediately invalid after this call. Both `tenant:apikey:{old_hash}` and `tenant:id:{tenant_id}` Redis cache entries are deleted after commit.
- Rate limit is per-tenant to prevent key-cycling denial-of-service attacks through proxied IPs.

## Errors

- `401 Unauthorized` — no valid tenant resolved from the request.
- `429 Too Many Requests` — rate limit exceeded.

---

# 3. Revoke API Key

## Request

**DELETE** `/tenants/me/api-key`

Auth: `X-Tenant-API-Key` header or `Authorization: Bearer <jwt>`

No request body.

## Response (200 OK)

```json
{
  "message": "API key revoked. Use your credentials to log in and rotate a new key."
}
```

## Notes

- Sets `api_key_hash = null` on the tenant row. The tenant account remains **active**.
- Any subsequent request using an API key header returns 401 — no hash is stored to match against.
- The tenant can still authenticate via JWT and call the rotate endpoint to obtain a new key.
- This is NOT account deactivation. To deactivate the account entirely, use `POST /tenants/deactivate` (Story 2.6).
- Redis cache entries for the revoked key are invalidated immediately after DB commit.

## Errors

- `401 Unauthorized` — no valid tenant resolved from the request.