from fastapi import APIRouter, status, Request
from schemas.addresses import AddressCreate, AddressUpdate, AddressOut
from utils.deps import db_dependency, customer_dependency
from services.addresses import AddressService
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/addresses",
    tags=["addresses"]
)


@router.post("/", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_address(request: Request, db: db_dependency, current_user: customer_dependency, data: AddressCreate):
    """Create a new address for the current user."""
    address = await AddressService.create_address(db=db, user_id=current_user.id, data=data)
    logger.info("Address created", extra={"user_id": current_user.id, "address_id": address.id})
    return address


@router.get("/", response_model=list[AddressOut], status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_addresses(request: Request, db: db_dependency, current_user: customer_dependency):
    """Return all addresses belonging to the current user."""
    return await AddressService.get_addresses(db=db, user_id=current_user.id)


@router.get("/{address_id}", response_model=AddressOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_address(request: Request, db: db_dependency, current_user: customer_dependency, address_id: int):
    """Return a single address. Returns 404 if not found or not owned by the user."""
    return await AddressService.get_address(db=db, user_id=current_user.id, address_id=address_id)


@router.patch("/{address_id}", response_model=AddressOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def update_address(request: Request, db: db_dependency, current_user: customer_dependency, address_id: int, data: AddressUpdate):
    """Partially update an address. Returns 404 if not found or not owned by the user."""
    address = await AddressService.update_address(db=db, user_id=current_user.id, address_id=address_id, data=data)
    logger.info("Address updated", extra={"user_id": current_user.id, "address_id": address_id})
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_address(request: Request, db: db_dependency, current_user: customer_dependency, address_id: int):
    """Delete an address. Returns 404 if not found or not owned by the user."""
    await AddressService.delete_address(db=db, user_id=current_user.id, address_id=address_id)
    logger.info("Address deleted", extra={"user_id": current_user.id, "address_id": address_id})


@router.post("/{address_id}/set-default", response_model=AddressOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def set_default_address(request: Request, db: db_dependency, current_user: customer_dependency, address_id: int):
    """Set an address as the current user's default. Returns 404 if not found or not owned by the user."""
    address = await AddressService.set_default(db=db, user_id=current_user.id, address_id=address_id)
    logger.info("Default address set", extra={"user_id": current_user.id, "address_id": address_id})
    return address