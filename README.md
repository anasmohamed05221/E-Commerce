<div align="center">

# ⚡ E-Commerce Backend API

**Production-grade e-commerce REST API built from scratch with FastAPI**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

</div>

---

## 📌 What This Is

A fully hand-written backend for an e-commerce platform — **no scaffolding, no boilerplate generators**. Every model, service, route, migration, and test is written intentionally to learn and demonstrate real backend engineering.

> 🚧 **Active Development** — Core commerce features (cart, orders, checkout) are being built now.

---

## 🏗️ Architecture

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
| Dependency Injection | DB sessions, authenticated user context |
| Token Rotation | Refresh tokens revoked on reuse |
| Cache-Aside | Redis → DB fallback for categories |
| Soft Deletes | Users deactivated, not destroyed |
| Historical Pricing | `price_at_time` on order items |

---

## 🔐 Auth System

Full authentication pipeline — not a tutorial copy-paste.

| Feature | Detail |
|---|---|
| Registration | Email + password with validation |
| Email Verification | 6-digit code, time-limited |
| Login | JWT access token (15 min) + refresh token (7 days) |
| Token Rotation | Old refresh token revoked on each refresh |
| Password Change | Confirmation email with approve/deny links |
| Password Reset | Forgot-password flow with time-limited token |
| Logout | Single device or all devices (revoke all tokens) |
| Account Deactivation | Soft delete + full token revocation |
| RBAC | Role field on user (customer, admin) |
| Rate Limiting | Per-endpoint limits (e.g. login: 5/min, register: 3/min) |

Tokens are **hashed in the database** (SHA-256 of JTI). Passwords use **bcrypt**.

---

## 🛒 API Endpoints

### Auth `/auth`
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/` | Register |
| `POST` | `/auth/token` | Login |
| `POST` | `/auth/verify` | Verify email |
| `POST` | `/auth/refresh` | Refresh tokens |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/forgot-password` | Request password reset |
| `POST` | `/auth/reset-password` | Reset password |

### Users `/users` 🔒
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Current user profile |
| `PUT` | `/users/me/password` | Request password change |
| `GET` | `/users/confirm-password-change` | Confirm via email link |
| `GET` | `/users/deny-password-change` | Deny via email link |
| `DELETE` | `/users/deactivate` | Deactivate account |

### Products `/products`
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/products/` | List (paginated, filterable by category/price) |
| `GET` | `/products/{id}` | Detail with category |

### Categories `/categories`
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/categories/` | List all (Redis-cached, 1hr TTL) |

### System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## 🗄️ Data Model

```
users ──┬── refresh_tokens
        ├── orders ── order_items ── products
        └── cart_items ─────────────── products ── inventory_changes
                                         └── categories
```

**8 tables** — users, products, categories, orders, order_items, cart_items, refresh_tokens, inventory_changes — managed through **11 Alembic migrations**.

---

## 🧪 Testing

```
tests/
├── unit/           → hashing, tokens, verification, sanitization
├── integration/    → user CRUD, token rotation, products, categories
├── api/
│   ├── auth/       → register, login, logout, verify, refresh, reset
│   ├── users/      → profile, password change, deactivation
│   ├── products/   → list, detail
│   └── categories/ → list
└── middleware/     → rate limiting
```

- **27 test files** across 4 layers
- SQLite in-memory DB for isolation
- AsyncMock Redis for cache testing
- CI runs on every push via **GitHub Actions**

---

## ⚙️ Tech Stack

| Layer | Tech |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Cache | Redis (async) |
| Auth | JWT (python-jose) + Bcrypt (passlib) |
| Validation | Pydantic v2, email-validator, phonenumbers |
| Rate Limiting | SlowAPI |
| Logging | Structured JSON logs, rotating file handlers, request ID tracing |
| Testing | Pytest + pytest-asyncio |
| CI/CD | GitHub Actions |
| Linting | Ruff |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/anasmohamed05221/E-Commerce.git
cd E-Commerce

# Environment
cp .env.example .env
# Fill in: DATABASE_URL, SECRET_KEY, MAIL_* credentials

# Install
pip install -r requirements.txt

# Migrate
alembic upgrade head

# Run
uvicorn main:app --reload
```

---

## 🗺️ Roadmap

### ✅ Done
- [x] User registration, email verification, JWT auth with token rotation
- [x] Password change (with email confirmation) and reset flows
- [x] Account deactivation with full token revocation
- [x] Product catalog — list with pagination/filtering, detail view
- [x] Categories with Redis caching
- [x] Rate limiting, structured logging, request ID tracing
- [x] RBAC groundwork (role field, middleware-ready)
- [x] 27-file test suite (unit → integration → API → middleware)
- [x] GitHub Actions CI pipeline

### 🔨 Building Now
- [ ] Shopping cart (DB-backed, schemas + service in progress)
- [ ] Order & checkout flow
- [ ] Inventory management (stock tracking model exists)

### 📅 Up Next
- [ ] Admin endpoints (product/category CRUD, order management)
- [ ] Payment gateway simulation
- [ ] Docker containerization
- [ ] Frontend integration (React/Next.js)

---

<div align="center">

**Built by [Anas Mohamed](https://github.com/anasmohamed05221)** — learning backend engineering by building, not by watching.

</div>
