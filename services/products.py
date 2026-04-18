from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from decimal import Decimal
from models.products import Product
from models.categories import Category
from models.order_items import OrderItem
from schemas.products import ProductCreate, ProductUpdate
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ProductService:
    @staticmethod
    async def get_products(
        db: AsyncSession,
        limit: int, offset: int,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None
        ) -> tuple[list[Product], int]:
        """Fetch paginated products with optional category and price filters."""
        query = select(Product).order_by(Product.id)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)

        total = await db.scalar(select(func.count()).select_from(query.subquery()))

        items = (await db.scalars(query.offset(offset).limit(limit))).all()

        return items, total

    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
        """Fetch a single product by ID with its category eagerly loaded."""
        product_model = await db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id==product_id))
        return product_model

    @staticmethod
    async def create_product(db: AsyncSession, request: ProductCreate):
        category = await db.scalar(select(Category).where(Category.id==request.category_id))
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid category_id")
        
        product = Product(category_id=request.category_id, 
                        name=request.name, 
                        description=request.description, 
                        price=request.price, 
                        image_url=request.image_url,
                        stock=request.stock
                        )
        db.add(product)

        try:
            await db.commit()
            await db.refresh(product)
        except Exception:
            logger.error("Product create commit failed")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product create commit failed")
        
        product = await db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id==product.id))
        return product
    


    @staticmethod
    async def update_product(db: AsyncSession, request: ProductUpdate, product_id: int):
        product = await db.scalar(select(Product).where(Product.id==product_id))
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        if request.name is not None:
            product.name = request.name

        if request.price is not None:
            product.price = request.price

        if request.stock is not None:
            product.stock = request.stock

        if request.category_id is not None:
            category = await db.scalar(select(Category).where(Category.id==request.category_id))
            if category is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid category_id")
            product.category_id = category.id

        if request.description is not None:
            product.description = request.description

        if request.image_url is not None:
            product.image_url = request.image_url

        try:
            await db.commit()
            await db.refresh(product)
        except Exception:
            logger.error("Product update commit failed")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product update commit failed")
        
        product = await db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id==product.id))
        return product

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int):
        product = await db.scalar(select(Product).where(Product.id==product_id))
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        order_item_conflict = await db.scalar(select(OrderItem).where(OrderItem.product_id==product_id))
        if order_item_conflict is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can't delete an ordered product")
        
        await db.delete(product)

        try:
            await db.commit()
        except Exception:
            logger.error("Product delete commit failed")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product delete commit failed")