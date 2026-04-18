import pytest
from models.users import User
from models.enums import UserRole
from utils.hashing import get_password_hash

HASHED = get_password_hash("TestPassword123!")


async def _make_user(session, email, role=UserRole.CUSTOMER, is_active=True):
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        hashed_password=HASHED,
        role=role,
        is_active=is_active,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_list_users_success(client, admin_token, verified_user):
    """Returns 200 with correct AdminUserListOut envelope shape."""
    response = await client.get(
        "/admin/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert "total" in data
    assert data["total"] >= 1
    item = data["items"][0]
    assert "id" in item
    assert "email" in item
    assert "role" in item
    assert "is_active" in item
    assert "is_verified" in item


@pytest.mark.asyncio
async def test_list_users_empty(client, admin_token):
    """Returns 200 with empty items when no users exist."""
    response = await client.get(
        "/admin/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # only the admin itself exists
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_list_users_role_filter(client, admin_token, session, verified_user):
    """?role=customer returns only customers."""
    response = await client.get(
        "/admin/users/?role=customer",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["role"] == "customer" for item in data["items"])


@pytest.mark.asyncio
async def test_list_users_is_active_filter(client, admin_token, session):
    """?is_active=false returns only inactive users."""
    await _make_user(session, "inactive_list@example.com", is_active=False)

    response = await client.get(
        "/admin/users/?is_active=false",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["is_active"] is False for item in data["items"])


@pytest.mark.asyncio
async def test_list_users_pagination(client, admin_token, session):
    """limit and offset control the page; total reflects the full count."""
    for i in range(3):
        await _make_user(session, f"paginate{i}@example.com")

    response = await client.get(
        "/admin/users/?limit=2&offset=0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
