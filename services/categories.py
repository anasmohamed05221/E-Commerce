from sqlalchemy.orm import Session
from models.categories import Category

class CategoryService:
    @staticmethod
    def get_categories(db: Session) -> list[Category]:
        categories = db.query(Category).order_by(Category.name.asc()).all()
        return categories