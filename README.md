# E-Commerce API (FastAPI)

Building a high-performance, scalable E-Commerce backend using Python and FastAPI. This project demonstrates strictly typed architecture, secure authentication, and modern DevOps practices.

> **🚧 Project Status: Active Development**
> Currently building core e-commerce features. Authentication and base architecture are complete.

## 🛠 Tech Stack
- **Framework:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL + SQLAlchemy + Alembic
- **Auth:** OAuth2 with JWT (Access + Refresh Token rotation)
- **Security:** Passlib (Brypt), SlowAPI (Rate Limiting)
- **Containerization:** Docker (In Progress)

## 🗺️ Roadmap & Features

### ✅ Completed (Phase 1: Foundation)
- [x] **Users & Auth:** Full registration flow, JWT login, Email Verification.
- [x] **Security:** Refresh Tokens, Role-Based Access Control (RBAC).
- [x] **Observability:** Custom Logging Middleware, Request ID tracing.
- [x] **Architecture:** Service-Repository pattern setup.

### 🚧 In Progress (Phase 2: Core Business Logic)
- [ ] **Product Catalog:** Categories, Inventory management.
- [ ] **Shopping Cart:** Redis-based temporary carts.
- [ ] **Orders & Checkout:** Payment gateway logic simulation.

### 📅 Planned (Phase 3: Reliability & Ops)
- [ ] **Testing:** Pytest suite for unit/integration tests.
- [ ] **CI/CD:** GitHub Actions for automated linting/testing.
- [ ] **Frontend:** React/Next.js integration.

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/anasmohamed05221/E-Commerce.git
   ```

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Update DB credentials in .env
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run with Uvicorn**
   ```bash
   uvicorn main:app --reload
   ```
