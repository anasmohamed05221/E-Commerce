import pytest


@pytest.mark.asyncio
async def test_cancel_order_success(client, user_token, order_factory):
    """Returns 200 with status set to cancelled."""
    order = order_factory()

    response = await client.post(
        f"/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_not_found(client, user_token):
    """Returns 404 for a non-existent order."""
    response = await client.post("/orders/99999/cancel", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_order_not_pending(client, user_token, order_factory):
    """Returns 409 when the order is already cancelled."""
    order = order_factory()

    await client.post(f"/orders/{order.id}/cancel", headers={"Authorization": f"Bearer {user_token}"})
    response = await client.post(f"/orders/{order.id}/cancel", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 409
