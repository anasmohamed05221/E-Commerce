from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
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
    def get_products(
        db: Session,
        limit: int, offset: int,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None
        ) -> tuple[list[Product], int]:
        """Fetch paginated products with optional category and price filters."""
        query = db.query(Product).order_by(Product.id)
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

    @staticmethod
    def create_product(db: Session, request: ProductCreate):
        category = db.query(Category).filter(Category.id==request.category_id).first()
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
            db.commit()
            db.refresh(product)
        except Exception:
            logger.error("Product create commit failed")
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product create commit failed")
        
        product = db.query(Product).options(joinedload(Product.category)).filter(Product.id==product.id).first()
        return product
    


    @staticmethod
    def update_product(db: Session, request: ProductUpdate, product_id: int):
        product = db.query(Product).filter(Product.id==product_id).first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        if request.name is not None:
            product.name = request.name

        if request.price is not None:
            product.price = request.price

        if request.stock is not None:
            product.stock = request.stock

        if request.category_id is not None:
            category = db.query(Category).filter(Category.id==request.category_id).first()
            if category is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid category_id")
            product.category_id = category.id

        if request.description is not None:
            product.description = request.description

        if request.image_url is not None:
            product.image_url = request.image_url

        try:
            db.commit()
            db.refresh(product)
        except Exception:
            logger.error("Product update commit failed")
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product update commit failed")
        
        product = db.query(Product).options(joinedload(Product.category)).filter(Product.id==product.id).first()
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int):
        product = db.query(Product).filter(Product.id==product_id).first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        order_item_conflict = db.query(OrderItem).filter(OrderItem.product_id==product_id).first()
        if order_item_conflict is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can't delete an ordered product")
        
        db.delete(product)

        try:
            db.commit()
        except Exception:
            logger.error("Product delete commit failed")
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Product delete commit failed")