import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from models.tenants import Tenant
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    """Plain client with no default headers — lets middleware tests exercise rejection paths."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db():
    """Patch SessionLocal in tenant_resolver to return a controllable mock session."""
    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    import middleware.tenant_resolver as resolver
    resolver.SessionLocal = MagicMock(return_value=mock_cm)
    return mock_session


@pytest.fixture
def valid_tenant():
    """Mock active tenant."""
    tenant = MagicMock(spec=Tenant)
    tenant.id = uuid.uuid4()
    tenant.is_active = True
    return tenant


@pytest.fixture
def inactive_tenant():
    """Mock inactive tenant."""
    tenant = MagicMock(spec=Tenant)
    tenant.id = uuid.uuid4()
    tenant.is_active = False
    return tenant