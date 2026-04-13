import pytest


@pytest.mark.asyncio
async def test_create_address_success(client, user_token):
    """POST /addresses/ returns 201 with address fields matching the input."""
    response = await client.post(
        "/addresses/",
        json={"street": "456 Test St", "city": "Alexandria", "country": "Egypt", "postal_code": "21500"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["street"] == "456 Test St"
    assert data["city"] == "Alexandria"
    assert data["country"] == "Egypt"
    assert data["postal_code"] == "21500"


@pytest.mark.asyncio
async def test_create_address_response_schema(client, user_token):
    """Response contains all expected AddressOut fields."""
    response = await client.post(
        "/addresses/",
        json={"street": "1 Schema St", "city": "Cairo", "country": "Egypt", "postal_code": "11511"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert "street" in data
    assert "city" in data
    assert "country" in data
    assert "postal_code" in data
    assert "is_default" in data
    assert "created_at" in data
    assert "label" in data
    assert "state" in data


@pytest.mark.asyncio
async def test_create_address_first_is_auto_default(client, user_token):
    """First address becomes default even when is_default is not specified."""
    response = await client.post(
        "/addresses/",
        json={"street": "1 First St", "city": "Cairo", "country": "Egypt", "postal_code": "11511"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 201
    assert response.json()["is_default"] is True


@pytest.mark.asyncio
async def test_create_address_explicit_default_clears_previous(client, user_token, test_address):
    """Creating a new address with is_default=true clears the previous default."""
    response = await client.post(
        "/addresses/",
        json={"street": "2 New St", "city": "Giza", "country": "Egypt", "postal_code": "12345", "is_default": True},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 201

    old = await client.get(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert old.json()["is_default"] is False


@pytest.mark.asyncio
async def test_create_address_missing_required_field(client, user_token):
    """Missing a required field returns 422."""
    response = await client.post(
        "/addresses/",
        json={"city": "Cairo", "country": "Egypt", "postal_code": "11511"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 422
