from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sa_update, func
from models.addresses import Address
from schemas.addresses import AddressCreate, AddressUpdate
from utils.logger import get_logger

logger = get_logger(__name__)


class AddressService:

    @staticmethod
    async def _clear_default(db: AsyncSession, user_id: int) -> None:
        """Clear the is_default flag on all addresses for a user.

        Does not commit — caller owns the transaction.
        """
        await db.execute(sa_update(Address).where(Address.user_id == user_id, Address.is_default == True).values(is_default=False))

    @staticmethod
    async def create_address(db: AsyncSession, user_id: int, data: AddressCreate) -> Address:
        """Create a new address for the user.

        If this is the user's first address, or if is_default is True,
        clears the existing default first and sets this one as default.
        """
        existing_count = await db.scalar(select(func.count()).where(Address.user_id == user_id).select_from(Address))
        is_default = data.is_default or existing_count == 0

        if is_default:
            await AddressService._clear_default(db, user_id)

        address = Address(
            user_id=user_id,
            label=data.label,
            street=data.street,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            is_default=is_default,
        )
        db.add(address)
        try:
            await db.commit()
        except Exception:
            logger.error("Address creation commit failed", extra={"user_id": user_id}, exc_info=True)
            await db.rollback()
            raise
        await db.refresh(address)
        return address

    @staticmethod
    async def get_addresses(db: AsyncSession, user_id: int) -> list[Address]:
        """Return all addresses belonging to the user."""
        return (await db.scalars(select(Address).where(Address.user_id == user_id))).all()

    @staticmethod
    async def get_address(db: AsyncSession, user_id: int, address_id: int) -> Address:
        """Return a single address, enforcing ownership.

        Raises:
            HTTPException 404: If the address does not exist or belongs to another user.
        """
        address = await db.scalar(select(Address).where(Address.id == address_id, Address.user_id == user_id))
        if address is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
        return address

    @staticmethod
    async def update_address(db: AsyncSession, user_id: int, address_id: int, data: AddressUpdate) -> Address:
        """Partially update an address. Only provided fields are applied.

        If is_default is set to True, clears the existing default first.

        Raises:
            HTTPException 404: If the address does not exist or belongs to another user.
        """
        address = await AddressService.get_address(db, user_id, address_id)

        if data.is_default is True:
            await AddressService._clear_default(db, user_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(address, field, value)

        try:
            await db.commit()
        except Exception:
            logger.error("Address update commit failed", extra={"user_id": user_id, "address_id": address_id}, exc_info=True)
            await db.rollback()
            raise
        await db.refresh(address)
        return address

    @staticmethod
    async def delete_address(db: AsyncSession, user_id: int, address_id: int) -> None:
        """Delete an address, enforcing ownership.

        Raises:
            HTTPException 404: If the address does not exist or belongs to another user.
        """
        address = await AddressService.get_address(db, user_id, address_id)
        await db.delete(address)
        try:
            await db.commit()
        except Exception:
            logger.error("Address deletion commit failed", extra={"user_id": user_id, "address_id": address_id}, exc_info=True)
            await db.rollback()
            raise

    @staticmethod
    async def set_default(db: AsyncSession, user_id: int, address_id: int) -> Address:
        """Set an address as the user's default, clearing any existing default.

        Raises:
            HTTPException 404: If the address does not exist or belongs to another user.
        """
        address = await AddressService.get_address(db, user_id, address_id)
        await AddressService._clear_default(db, user_id)
        address.is_default = True
        try:
            await db.commit()
        except Exception:
            logger.error("Set default address commit failed", extra={"user_id": user_id, "address_id": address_id}, exc_info=True)
            await db.rollback()
            raise
        await db.refresh(address)
        return address