import pytest
from sqlalchemy import select
from models.products import Product


async def test_select_returns_only_the_current_tenant_rows(session, test_tenant, second_tenant, test_category, second_category):
    """Scoped SELECT returns only the current tenant's rows."""
    assert test_tenant.id != second_tenant.id

    session.info["tenant_id"] = None
    p1 = Product(tenant_id=test_tenant.id, name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(tenant_id=second_tenant.id, name="TV", price=2000.00, stock=5, category_id=second_category.id)
    session.add(p1)
    session.add(p2)
    await session.commit()

    session.info["tenant_id"] = test_tenant.id
    result_a = (await session.scalars(select(Product))).all()
    assert len(result_a) == 1
    assert result_a[0].id == p1.id
    assert all(r.id != p2.id for r in result_a)

    session.info["tenant_id"] = second_tenant.id
    result_b = (await session.scalars(select(Product))).all()
    assert len(result_b) == 1
    assert result_b[0].id == p2.id
    assert all(r.id != p1.id for r in result_b)

    # Falsifiability anchor: None bypasses the listener — both rows visible
    session.info["tenant_id"] = None
    result_all = (await session.scalars(select(Product))).all()
    assert len(result_all) == 2
    ids = {r.id for r in result_all}
    assert p1.id in ids
    assert p2.id in ids


async def test_select_by_id_of_the_other_tenant_row_returns_none(session, test_tenant, second_tenant, test_category, second_category):
    """Querying by another tenant's row id returns None — literal BOLA prevention."""
    assert test_tenant.id != second_tenant.id

    session.info["tenant_id"] = None
    p1 = Product(tenant_id=test_tenant.id, name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(tenant_id=second_tenant.id, name="TV", price=2000.00, stock=5, category_id=second_category.id)
    session.add(p1)
    session.add(p2)
    await session.commit()

    session.info["tenant_id"] = test_tenant.id
    result = await session.scalar(select(Product).where(Product.id == p2.id))
    assert result is None

    session.info["tenant_id"] = second_tenant.id
    result = await session.scalar(select(Product).where(Product.id == p1.id))
    assert result is None


async def test_cache_key_correctness_across_tenant_switches(session, test_tenant, second_tenant, test_category, second_category):
    """Same compiled statement must produce different result sets per tenant — regression test for lambda cache-poisoning bug."""
    assert test_tenant.id != second_tenant.id

    session.info["tenant_id"] = None
    p1 = Product(tenant_id=test_tenant.id, name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(tenant_id=second_tenant.id, name="TV", price=2000.00, stock=5, category_id=second_category.id)
    session.add(p1)
    session.add(p2)
    await session.commit()

    session.info["tenant_id"] = test_tenant.id
    result = (await session.scalars(select(Product))).all()
    assert len(result) == 1
    assert result[0].id == p1.id

    session.info["tenant_id"] = second_tenant.id
    result = (await session.scalars(select(Product))).all()
    assert len(result) == 1
    assert result[0].id == p2.id

    # Third call — if cache-poisoned with first tenant's id, this returns B's row instead of A's
    session.info["tenant_id"] = test_tenant.id
    result = (await session.scalars(select(Product))).all()
    assert len(result) == 1
    assert result[0].id == p1.id