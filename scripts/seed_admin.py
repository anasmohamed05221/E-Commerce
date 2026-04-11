import os
import sys
from core.database import SessionLocal
from models.users import User
from models.enums import UserRole
from utils.hashing import get_password_hash


if __name__ == "__main__":
    email = os.environ.get("SEED_ADMIN_EMAIL")
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    first_name = os.environ.get("SEED_ADMIN_FIRST_NAME")
    last_name = os.environ.get("SEED_ADMIN_LAST_NAME")

    if not email or not password or not first_name or not last_name:
        print("Seeded admin info not complete.")
        sys.exit(1)

    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("User already exist.")
            sys.exit(0)

        admin = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        try:
            db.commit()
            print("Admin created successfully.")
        except Exception as e:
            db.rollback()
            print(f"Failed to create admin: {e}")
            sys.exit(1)
        
    finally:
        db.close()