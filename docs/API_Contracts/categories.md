# Categories API Contract

This document defines the API contract for category-related endpoints in the MVP version of the E-Commerce backend.

---

# 1. List Categories

## Request

**GET** `/categories/`

Rate limit: 60/minute

- No auth required.
- No query parameters.

---

## Response (200 OK)

Example:

[
  {
    "id": 1,
    "name": "Electronics",
    "description": "Tech gear and gadgets"
  },
  {
    "id": 2,
    "name": "Clothing",
    "description": null
  }
]

---

## Response Fields

- `id`: unique category identifier.
- `name`: category name.
- `description`: optional category description, may be null.

---

## Notes

- Returns all categories in the system.
- No pagination — categories are a small, stable dataset.

---

## Errors

- `429 Too Many Requests` — rate limit exceeded.
