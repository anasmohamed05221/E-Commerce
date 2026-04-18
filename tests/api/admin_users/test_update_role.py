import pytest
from models.users import User
from models.enums import UserRole
from utils.hashing import get_password_hash

HASHED = get_password_hash("TestPassword123!")


async def _make_admin(session, email):
    user = User(
        email=email,
        first_name="Test",
        last_name="Admin",
        hashed_password=HASHED,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_update_role_promote_success(client, admin_token, verified_user):
    """Returns 200 with role=admin after promoting a customer."""
    response = await client.patch(
        f"/admin/users/{verified_user.id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_update_role_demote_success(client, admin_token, session):
    """Returns 200 with role=customer after demoting an admin."""
    another_admin = await _make_admin(session, "demote@example.com")

    response = await client.patch(
        f"/admin/users/{another_admin.id}/role",
        json={"role": "customer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "customer"


@pytest.mark.asyncio
async def test_update_role_not_found(client, admin_token):
    """Returns 404 for a non-existent user."""
    response = await client.patch(
        "/admin/users/99999/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_role_self(client, admin_token, verified_admin):
    """Returns 400 when admin targets their own account."""
    response = await client.patch(
        f"/admin/users/{verified_admin.id}/role",
        json={"role": "customer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_role_same_role(client, admin_token, verified_user):
    """Returns 409 when user already has the target role."""
    response = await client.patch(
        f"/admin/users/{verified_user.id}/role",
        json={"role": "customer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
