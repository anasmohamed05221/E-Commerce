from sqlalchemy.orm import Session, joinedload
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
        """Fetch paginated products with optional category and price filters."""
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

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Fetch a single product by ID with its category eagerly loaded."""
        product_model = db.query(Product).options(joinedload(Product.category)).filter(Product.id==product_id).first()
        return product_model