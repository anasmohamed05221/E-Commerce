import pytest
from contextlib import asynccontextmanager
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import ASGITransport, AsyncClient
from fastapi import Request
from models.products import Product
from models.tenants import Tenant
from utils.deps import get_db
from main import app
import middleware.tenant_resolver as tenant_resolver_module


async def test_none_tenant_bypass_is_true_no_op(session, test_tenant, second_tenant, test_category, second_category):
    """Listener early-returns on None tenant_id — unscoped session returns all tenants' rows."""
    assert test_tenant.id != second_tenant.id

    session.info["tenant_id"] = None
    p1 = Product(tenant_id=test_tenant.id, name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(tenant_id=second_tenant.id, name="TV", price=2000.00, stock=5, category_id=second_category.id)
    session.add(p1)
    session.add(p2)
    await session.commit()

    session.expire_all()
    result = (await session.scalars(select(Product))).all()
    assert len(result) == 2
    ids = {r.id for r in result}
    assert p1.id in ids
    assert p2.id in ids


async def test_register_tenant_uses_none_tenant_id_on_bypass(connection, session, worker_id):
    """POST /tenants/register bypasses middleware — every db.info['tenant_id'] observed during the request is None."""

    # Production-faithful get_db: reads tenant from request.state (None on bypass paths)
    async def real_get_db(request: Request):
        tenant = getattr(request.state, "tenant", None)
        async with AsyncSession(bind=connection, expire_on_commit=False) as db:
            db.info["tenant_id"] = tenant.id if tenant else None
            yield db

    # Middleware SessionLocal shares the test connection (bypass path never calls it, but wired for correctness)
    @asynccontextmanager
    async def test_session_local():
        async with AsyncSession(bind=connection, expire_on_commit=False) as db:
            yield db

    observed_tenant_ids = []

    def spy(execute_state):
        observed_tenant_ids.append(execute_state.session.info.get("tenant_id"))

    event.listen(Session, "do_orm_execute", spy)

    original_session_local = tenant_resolver_module.SessionLocal
    tenant_resolver_module.SessionLocal = test_session_local
    app.dependency_overrides[get_db] = real_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/tenants/register", json={
                "name": f"Bypass Store {worker_id}",
                "slug": f"bypass-store-{worker_id}",
                "email": f"bypass_owner_{worker_id}@test.com",
                "password": "StrongPass123!",
                "plan": "free"
            })

        assert response.status_code == 201

        # Spy must have fired at least once — if no SELECT ran, the test proves nothing
        assert len(observed_tenant_ids) > 0, "No do_orm_execute events observed — spy never fired"

        # Every observed tenant_id must be None — bypass path must never carry a tenant context
        assert all(tid is None for tid in observed_tenant_ids), (
            f"Expected all None but got: {observed_tenant_ids}"
        )

        # Oracle: new tenant row exists
        session.info["tenant_id"] = None
        session.expire_all()
        new_tenant = await session.scalar(
            select(Tenant).where(Tenant.slug == f"bypass-store-{worker_id}")
        )
        assert new_tenant is not None
        assert new_tenant.slug == f"bypass-store-{worker_id}"

    finally:
        event.remove(Session, "do_orm_execute", spy)
        tenant_resolver_module.SessionLocal = original_session_local
        app.dependency_overrides.pop(get_db, None)