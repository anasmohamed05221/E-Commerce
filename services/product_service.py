from sqlalchemy.orm import Session
from decimal import Decimal
from models.products import Product
from typing import Optional


class ProductService:
    @staticmethod
    def get_products(
        db: Session,
        limit: int, offset: int,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None
        ) -> tuple[list[Product], int]:
        query = db.query(Product)
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        total = query.count()

        items = query.offset(offset).limit(limit).all()

        return items, total