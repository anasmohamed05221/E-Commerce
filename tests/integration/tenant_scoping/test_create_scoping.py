import pytest
from decimal import Decimal
from sqlalchemy import select
from models.products import Product
from schemas.products import ProductCreate
from services.products import ProductService


async def test_created_product_lands_with_right_tenant_id(session, test_tenant, second_tenant, test_category):
    """Product created via the service must be tagged with the explicit tenant_id arg."""
    assert test_tenant.id != second_tenant.id

    session.info["tenant_id"] = test_tenant.id
    body = ProductCreate(name="Laptop", price=Decimal("999.99"), stock=10, category_id=test_category.id)
    await ProductService.create_product(session, body, tenant_id=test_tenant.id)

    # Oracle: rotate to None to bypass scoping and verify the actual tenant_id in DB
    session.info["tenant_id"] = None
    rows = (await session.scalars(select(Product).where(Product.name == "Laptop"))).all()
    assert len(rows) == 1
    assert rows[0].tenant_id == test_tenant.id

    # Visible to Tenant A
    session.info["tenant_id"] = test_tenant.id
    result_a = (await session.scalars(select(Product))).all()
    assert len(result_a) == 1

    # Not visible to Tenant B
    session.info["tenant_id"] = second_tenant.id
    result_b = (await session.scalars(select(Product))).all()
    assert len(result_b) == 0


async def test_same_product_name_allowed_across_tenants(session, test_tenant, second_tenant, test_category, second_category):
    """Duplicate-check SELECT inside create_product is tenant-scoped — same name valid across tenants."""
    assert test_tenant.id != second_tenant.id

    # Insert Tenant A's "Laptop" directly (bypass service to avoid two consecutive service commits)
    session.info["tenant_id"] = None
    p_a = Product(tenant_id=test_tenant.id, name="Laptop", price=Decimal("999.99"), stock=10, category_id=test_category.id)
    session.add(p_a)
    await session.commit()

    # Service call for Tenant B — duplicate-check SELECT is scoped to B, won't see A's "Laptop"
    session.info["tenant_id"] = second_tenant.id
    body_b = ProductCreate(name="Laptop", price=Decimal("1299.99"), stock=5, category_id=second_category.id)
    await ProductService.create_product(session, body_b, tenant_id=second_tenant.id)

    # Oracle: both rows exist, one per tenant
    session.info["tenant_id"] = None
    rows = (await session.scalars(select(Product).where(Product.name == "Laptop"))).all()
    assert len(rows) == 2
    tenant_ids = {r.tenant_id for r in rows}
    assert test_tenant.id in tenant_ids
    assert second_tenant.id in tenant_ids


async def test_explicit_tenant_id_arg_is_source_of_truth_on_insert(session, test_tenant, second_tenant, test_category):
    """Explicit tenant_id arg controls the INSERT tag regardless of session.info['tenant_id']."""
    assert test_tenant.id != second_tenant.id

    # Session context is A, but explicit tenant_id=B — row must land under B
    session.info["tenant_id"] = test_tenant.id
    body = ProductCreate(name="Crossover", price=Decimal("500.00"), stock=3, category_id=test_category.id)
    await ProductService.create_product(session, body, tenant_id=second_tenant.id)

    # Oracle: row exists and is tagged with B
    session.info["tenant_id"] = None
    rows = (await session.scalars(select(Product).where(Product.name == "Crossover"))).all()
    assert len(rows) == 1
    assert rows[0].tenant_id == second_tenant.id

    # Not visible to Tenant A
    session.info["tenant_id"] = test_tenant.id
    result_a = (await session.scalars(select(Product))).all()
    assert len(result_a) == 0

    # Visible to Tenant B
    session.info["tenant_id"] = second_tenant.id
    result_b = (await session.scalars(select(Product))).all()
    assert len(result_b) == 1
    assert result_b[0].name == "Crossover"