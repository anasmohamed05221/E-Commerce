<div align="center">

# E-Commerce Backend APP

**Production-grade e-commerce REST API built from scratch with FastAPI**

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![CI](https://github.com/anasmohamed05221/E-Commerce/actions/workflows/ci.yml/badge.svg)

</div>

---

## What This Is

A hands-on built backend for an e-commerce platform — **no scaffolding, no boilerplate generators**. Every model, service, route, migration, and test is written intentionally to learn and demonstrate real backend engineering.

> **Active Development** — Core MVP is complete (auth, products, cart, orders, admin). Docker + deployment are next.

---

## Architecture

```
Request → Middleware (logging, rate limit, request ID)
       → Router (validation, HTTP contract)
       → Service (business logic)
       → Model (SQLAlchemy ORM → PostgreSQL)
       → Response
```

**3-layer separation** — routers never touch the DB directly, services own the logic, models own the data.

| Pattern | Where |
|---|---|
| Dependency Injection | DB sessions, authenticated user context, role guards |
| Token Rotation | Refresh tokens revoked on reuse |
| Pessimistic Locking | `SELECT FOR UPDATE` on products during checkout and order cancellation |
| Atomic Transactions | Checkout: stock decrement + order creation + inventory log in one transaction |
| Cache-Aside | Redis → DB fallback for categories (1hr TTL) |
| Soft Deletes | Users deactivated, not destroyed |
| Historical Pricing | `price_at_time` on order items (price snapshots at purchase) |
| Inventory Audit Log | Every stock change recorded with reason |

---

## Auth System

Full authentication pipeline — not a tutorial copy-paste.

| Feature | Detail |
|---|---|
| Registration | Email + password with validation |
| Email Verification | 6-digit code, 10-minute expiry |
| Login | JWT access token (15 min) + refresh token (7 days) |
| Token Rotation | Old refresh token revoked on each refresh |
| Password Change | Confirmation email with approve/deny links |
| Password Reset | Forgot-password flow with time-limited token |
| Logout | Single device or all devices (revoke all tokens) |
| Account Deactivation | Soft delete + full token revocation |
| RBAC | `CUSTOMER` and `ADMIN` roles enforced via dependency injection |
| Rate Limiting | Per-endpoint limits (login: 5/min, register: 3/min, etc.) |

Tokens are **hashed in the database** (SHA-256 of JTI). Passwords use **bcrypt**.

---

## API Endpoints

### Auth `/auth`
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `POST` | `/auth/` | 3/min | Register |
| `POST` | `/auth/token` | 5/min | Login — returns access + refresh tokens |
| `POST` | `/auth/verify` | 3/min | Verify email with 6-digit code |
| `POST` | `/auth/refresh` | 10/min | Rotate refresh token |
| `POST` | `/auth/logout` | 10/min | Revoke refresh token |
| `POST` | `/auth/forgot-password` | 3/min | Request password reset email |
| `POST` | `/auth/reset-password` | 5/min | Reset password; revokes all sessions |

### Users `/users` (authenticated)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/users/me` | 30/min | Current user profile |
| `PATCH` | `/users/me` | 10/min | Update profile (name, phone number) |
| `PUT` | `/users/me/password` | 2/min | Request password change via email confirmation |
| `POST` | `/users/confirm-password-change` | — | Confirm password change via token in request body |
| `POST` | `/users/deny-password-change` | — | Deny password change; revoke all sessions |
| `DELETE` | `/users/deactivate` | 3/min | Deactivate account |

### Products `/products` (public)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/products/` | 60/min | Paginated list; filterable by category, min/max price |
| `GET` | `/products/{id}` | 60/min | Product detail with category |

### Categories `/categories` (public)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/categories/` | 60/min | List all (Redis-cached, 1hr TTL) |

### Cart `/cart` (customers only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/cart/` | 60/min | View cart with total price |
| `POST` | `/cart/` | 10/min | Add item (or increment if already in cart) |
| `PATCH` | `/cart/{product_id}` | 10/min | Update item quantity |
| `DELETE` | `/cart/` | 5/min | Clear all items from cart |
| `DELETE` | `/cart/{product_id}` | 10/min | Remove single item |

### Addresses `/addresses` (customers only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `POST` | `/addresses/` | — | Add address; first address auto-set as default |
| `GET` | `/addresses/` | — | List all addresses |
| `GET` | `/addresses/{id}` | — | Get single address |
| `PATCH` | `/addresses/{id}` | — | Partial update address |
| `DELETE` | `/addresses/{id}` | — | Delete address |
| `POST` | `/addresses/{id}/set-default` | — | Set address as default |

### Orders `/orders` (customers only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `POST` | `/orders/` | 5/min | Checkout — requires address + payment method; decrements stock atomically |
| `GET` | `/orders/` | 60/min | List orders (paginated, newest first) |
| `GET` | `/orders/{id}` | 60/min | Order detail with all line items |
| `POST` | `/orders/{id}/cancel` | 10/min | Cancel pending order; restores stock |

### Admin Products `/admin/products` (admins only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `POST` | `/admin/products/` | 30/min | Create product |
| `PATCH` | `/admin/products/{id}` | 30/min | Partial update product |
| `DELETE` | `/admin/products/{id}` | 30/min | Delete product (blocked if order items exist) |

### Admin Orders `/admin/orders` (admins only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/admin/orders/` | 60/min | List all orders (paginated, filterable by status) |
| `PATCH` | `/admin/orders/{id}/status` | 30/min | Advance order status (PENDING→CONFIRMED→SHIPPED→COMPLETED) |
| `POST` | `/admin/orders/{id}/cancel` | 30/min | Cancel PENDING or CONFIRMED order; restores stock |

### Admin Users `/admin/users` (admins only)
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `GET` | `/admin/users/` | 60/min | List all users (paginated, filterable by role/is_active) |
| `GET` | `/admin/users/{id}` | 60/min | Get single user detail |
| `PATCH` | `/admin/users/{id}/deactivate` | 30/min | Deactivate user + revoke all sessions |
| `PATCH` | `/admin/users/{id}/reactivate` | 30/min | Reactivate a deactivated user |
| `PATCH` | `/admin/users/{id}/role` | 30/min | Promote or demote user role |

### System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## Data Model

```
users ──┬── refresh_tokens
        ├── addresses ── orders ── order_items ── products ── inventory_changes
        └── cart_items ──────────────────────────── products
                                                       └── categories
```

**9 tables** — users, products, categories, orders, order_items, cart_items, refresh_tokens, inventory_changes, addresses — managed through **22 Alembic migrations**.

---

## Testing

```
tests/
├── unit/           → hashing, tokens, verification, sanitization, order FSM
├── integration/    → auth, user service, token rotation, products, categories,
│                     cart, checkout, orders, addresses, admin product/order/user service
├── api/
│   ├── auth/       → register, login, logout, verify, refresh, reset
│   ├── users/      → profile, profile editing, password change, deactivation
│   ├── products/   → list, detail, filtering
│   ├── categories/ → list
│   ├── cart/       → add, update, remove, clear, view
│   ├── orders/     → checkout, list, detail, cancel
│   ├── addresses/  → create, list, get, update, delete, set-default (auth, ownership)
│   ├── admin_products/ → create, update, delete (auth, RBAC, validation)
│   ├── admin_orders/  → list, status update, cancel (auth, RBAC, FSM)
│   ├── admin_users/   → list, get, deactivate, reactivate, role update (auth, RBAC, guards)
│   └── checkout/   → stock validation, atomicity, address validation
└── middleware/     → rate limiting, request ID
```

- **412 tests** across 4 layers — real PostgreSQL, AsyncMock Redis, CI on every push
- **Transactional isolation** — tables created once, each test wrapped in a savepoint and rolled back. No DDL per test.
- **Parallel execution** — `pytest -n 8` via pytest-xdist with filelock-guarded DDL. One worker sets up the schema, all others reuse it.
- **Pre-hashed passwords + direct JWT generation** — eliminates bcrypt cost from every test fixture and HTTP login call.
- **Worker-scoped fixture emails** — unique email per xdist worker prevents unique-constraint deadlocks under full parallelism.
- **Result: before optimization, 194 tests in ~70s; after optimization, 412 tests in ~30s**

---

## Tech Stack

| Layer | Tech |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Cache | Redis (async, cache-aside pattern) |
| Auth | JWT (python-jose) + Bcrypt (passlib) |
| Validation | Pydantic v2, email-validator, phonenumbers |
| Rate Limiting | SlowAPI |
| Email | SMTP with 3-retry exponential backoff (tenacity) |
| Logging | Structured JSON logs, rotating file handlers, request ID tracing |
| Testing | Pytest + pytest-asyncio + httpx + pytest-xdist |
| CI/CD | GitHub Actions |
| Linting | Ruff |

---

## Quick Start

```bash
# Prerequisites
- Python 3.13
- PostgreSQL (running locally or via Docker)
- Redis (running locally or via Docker)

# Clone
git clone https://github.com/anasmohamed05221/E-Commerce.git
cd E-Commerce

# Environment
cp .env.example .env
# Fill in: DATABASE_URL, SECRET_KEY, MAIL_* credentials, REDIS_URL

# Install
pip install -r requirements.txt

# Migrate
alembic upgrade head

# Run
uvicorn main:app --reload
```

**Key environment variables:**

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:3000"]
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

---

## Roadmap

### Done
- [x] User registration, email verification, JWT auth with token rotation
- [x] Password change (with email confirmation) and reset flows
- [x] Account deactivation with full token revocation
- [x] Product catalog — paginated list with category/price filtering, detail view
- [x] Categories with Redis caching
- [x] Shopping cart — add, update, remove, view with real-time total
- [x] Order checkout — atomic transaction, pessimistic locking, stock decrement
- [x] Order management — list, detail, cancel with stock restore + inventory log
- [x] Admin product management — create, update, delete (with referential integrity guard)
- [x] Admin order management — list all, status transitions (FSM), cancel with stock restore
- [x] Admin user management — list, view, deactivate, reactivate, role promotion/demotion
- [x] RBAC — CUSTOMER and ADMIN roles enforced at dependency level
- [x] Rate limiting, structured logging, request ID tracing
- [x] Address management — create, list, get, update, delete, set-default with ownership enforcement
- [x] COD payment method selectable at checkout
- [x] SHIPPED status added to order lifecycle (PENDING→CONFIRMED→SHIPPED→COMPLETED)
- [x] Profile editing — PATCH /users/me (name, phone number)
- [x] Clear cart — DELETE /cart (idempotent bulk delete)
- [x] 412 tests (unit, integration, API, middleware) passing with pytest-xdist
- [x] GitHub Actions CI pipeline

### Building Now
- [ ] Docker + docker-compose setup
- [ ] Deploy (Epic 1 close)

### Epic 2 — Payments & Async
- [ ] Stripe payment integration (checkout session + webhook)
- [ ] Celery + Redis task queue
- [ ] Order confirmation emails on payment
- [ ] Inventory update on payment
- [ ] Coupons / promo codes (fixed + percentage discounts)

### Epic 3 — Engagement Features
- [ ] Wishlist (add / remove / list)
- [ ] Reviews & Ratings (purchased-only constraint, auto-update avg rating)

### Epic 4 — Search
- [ ] Typesense integration
- [ ] Product search with filters, typo tolerance, and ranking

### Epic 5 — DevOps Improvements
- [ ] Monitoring and observability
- [ ] Infrastructure improvements and scaling

---

<div align="center">

**Built by [Anas Mohamed](https://github.com/anasmohamed05221)** — learning backend engineering by building, not by watching.

</div>
