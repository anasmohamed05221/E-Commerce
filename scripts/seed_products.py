import sys
from core.database import SessionLocal
from models.products import Product
from models.categories import Category

SEED_MARKER = "[SEED]"

CATEGORIES = [
    {"name": f"{SEED_MARKER} Electronics", "description": "Phones, laptops, and accessories"},
    {"name": f"{SEED_MARKER} Clothing",    "description": "Men and women apparel"},
    {"name": f"{SEED_MARKER} Books",       "description": "Fiction, non-fiction, and technical books"},
    {"name": f"{SEED_MARKER} Home",        "description": "Furniture, kitchen, and decor"},
    {"name": f"{SEED_MARKER} Sports",      "description": "Equipment and activewear"},
]

PRODUCTS_PER_CATEGORY = [
    [
        {"name": "Wireless Headphones Pro",    "description": "Noise-cancelling over-ear headphones", "price": "299.99", "stock": 40,  "rating": 4.7},
        {"name": "USB-C Hub 7-in-1",           "description": "Multiport adapter for laptops",         "price": "49.99",  "stock": 80,  "rating": 4.5},
        {"name": "Mechanical Keyboard TKL",    "description": "Tenkeyless with brown switches",        "price": "129.99", "stock": 30,  "rating": 4.6},
        {"name": "4K Webcam",                  "description": "60fps webcam with autofocus",           "price": "89.99",  "stock": 25,  "rating": 4.4},
        {"name": "Portable SSD 1TB",           "description": "USB 3.2 Gen 2 external SSD",           "price": "109.99", "stock": 50,  "rating": 4.8},
        {"name": "Smartwatch Series X",        "description": "Health tracking and notifications",     "price": "199.99", "stock": 35,  "rating": 4.3},
        {"name": "Gaming Mouse 16000 DPI",     "description": "Ergonomic with RGB lighting",           "price": "59.99",  "stock": 60,  "rating": 4.5},
        {"name": "Monitor 27 inch 144Hz",      "description": "IPS panel with G-Sync support",        "price": "349.99", "stock": 15,  "rating": 4.7},
        {"name": "Laptop Stand Adjustable",    "description": "Aluminum foldable stand",              "price": "39.99",  "stock": 100, "rating": 4.4},
        {"name": "Wireless Charger 15W",       "description": "Fast charging pad for Qi devices",     "price": "24.99",  "stock": 90,  "rating": 4.2},
    ],
    [
        {"name": "Classic White T-Shirt",      "description": "100% cotton unisex fit",               "price": "19.99",  "stock": 200, "rating": 4.3},
        {"name": "Slim Fit Chinos",            "description": "Stretch fabric in navy blue",          "price": "49.99",  "stock": 80,  "rating": 4.4},
        {"name": "Hooded Sweatshirt",          "description": "Fleece-lined pullover hoodie",         "price": "39.99",  "stock": 120, "rating": 4.5},
        {"name": "Running Shorts",             "description": "Lightweight with inner liner",         "price": "24.99",  "stock": 150, "rating": 4.2},
        {"name": "Denim Jacket",               "description": "Classic washed denim, regular fit",   "price": "69.99",  "stock": 60,  "rating": 4.6},
        {"name": "Polo Shirt",                 "description": "Pique cotton with embroidered logo",   "price": "34.99",  "stock": 90,  "rating": 4.3},
        {"name": "Jogger Pants",               "description": "Tapered fit with elastic waistband",   "price": "44.99",  "stock": 70,  "rating": 4.4},
        {"name": "Bomber Jacket",              "description": "Satin finish with ribbed cuffs",       "price": "89.99",  "stock": 40,  "rating": 4.5},
        {"name": "Linen Shirt",                "description": "Breathable summer shirt",              "price": "29.99",  "stock": 110, "rating": 4.1},
        {"name": "Compression Tights",         "description": "Sport performance leggings",           "price": "34.99",  "stock": 95,  "rating": 4.3},
    ],
    [
        {"name": "Clean Code",                 "description": "Robert C. Martin",                     "price": "34.99",  "stock": 50,  "rating": 4.8},
        {"name": "The Pragmatic Programmer",   "description": "Hunt and Thomas, 20th anniversary ed", "price": "39.99",  "stock": 45,  "rating": 4.7},
        {"name": "Designing Data-Intensive Apps", "description": "Martin Kleppmann",                  "price": "44.99",  "stock": 40,  "rating": 4.9},
        {"name": "Atomic Habits",              "description": "James Clear",                          "price": "16.99",  "stock": 100, "rating": 4.8},
        {"name": "Deep Work",                  "description": "Cal Newport",                          "price": "14.99",  "stock": 80,  "rating": 4.6},
        {"name": "System Design Interview",    "description": "Alex Xu, volume 1",                    "price": "29.99",  "stock": 60,  "rating": 4.7},
        {"name": "Python Crash Course",        "description": "Eric Matthes, 3rd edition",            "price": "24.99",  "stock": 70,  "rating": 4.5},
        {"name": "The Algorithm Design Manual","description": "Steven Skiena",                        "price": "49.99",  "stock": 30,  "rating": 4.6},
        {"name": "Sapiens",                    "description": "Yuval Noah Harari",                    "price": "15.99",  "stock": 90,  "rating": 4.7},
        {"name": "Zero to One",                "description": "Peter Thiel",                          "price": "13.99",  "stock": 75,  "rating": 4.5},
    ],
    [
        {"name": "Bamboo Cutting Board Set",   "description": "3-piece with juice groove",            "price": "29.99",  "stock": 60,  "rating": 4.5},
        {"name": "Cast Iron Skillet 12\"",     "description": "Pre-seasoned, oven safe",              "price": "44.99",  "stock": 40,  "rating": 4.8},
        {"name": "Coffee Grinder Electric",    "description": "Burr grinder with 12 settings",       "price": "59.99",  "stock": 35,  "rating": 4.6},
        {"name": "Desk Lamp LED",              "description": "Adjustable brightness and color temp", "price": "34.99",  "stock": 55,  "rating": 4.4},
        {"name": "Throw Pillow Set",           "description": "2-pack, linen fabric in beige",       "price": "24.99",  "stock": 80,  "rating": 4.3},
        {"name": "Stainless Steel Water Bottle","description": "1L, double-wall insulated",           "price": "19.99",  "stock": 120, "rating": 4.6},
        {"name": "Air Purifier Compact",       "description": "HEPA filter, covers 200 sq ft",       "price": "79.99",  "stock": 25,  "rating": 4.5},
        {"name": "Scented Candle Set",         "description": "3 candles, 40hr burn each",           "price": "29.99",  "stock": 70,  "rating": 4.4},
        {"name": "Wooden Shelf Floating",      "description": "Set of 3, rustic finish",              "price": "39.99",  "stock": 45,  "rating": 4.3},
        {"name": "Electric Kettle 1.7L",       "description": "Temperature control, keep warm",      "price": "49.99",  "stock": 50,  "rating": 4.7},
    ],
    [
        {"name": "Yoga Mat Non-Slip",          "description": "6mm thick with alignment lines",      "price": "29.99",  "stock": 80,  "rating": 4.5},
        {"name": "Resistance Bands Set",       "description": "5 levels, fabric with handles",       "price": "19.99",  "stock": 100, "rating": 4.4},
        {"name": "Jump Rope Speed",            "description": "Adjustable steel cable, ball bearings","price": "14.99",  "stock": 120, "rating": 4.3},
        {"name": "Dumbbell Pair 10kg",         "description": "Rubber hex, anti-roll design",        "price": "49.99",  "stock": 40,  "rating": 4.6},
        {"name": "Foam Roller Deep Tissue",    "description": "High density, 33cm",                  "price": "24.99",  "stock": 70,  "rating": 4.4},
        {"name": "Running Belt Waist Pack",    "description": "Water resistant, fits phone + keys",  "price": "17.99",  "stock": 90,  "rating": 4.2},
        {"name": "Pull-Up Bar Doorway",        "description": "No screws, 100kg capacity",           "price": "34.99",  "stock": 55,  "rating": 4.5},
        {"name": "Gym Gloves",                 "description": "Half-finger with wrist wrap",         "price": "12.99",  "stock": 110, "rating": 4.3},
        {"name": "Protein Shaker 700ml",       "description": "Leak-proof with mixing ball",         "price": "9.99",   "stock": 150, "rating": 4.4},
        {"name": "Knee Sleeves Pair",          "description": "7mm neoprene compression sleeves",    "price": "22.99",  "stock": 65,  "rating": 4.5},
    ],
]


def seed(db):
    created_categories = []
    for cat_data in CATEGORIES:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if existing:
            created_categories.append(existing)
            continue
        category = Category(**cat_data)
        db.add(category)
        db.flush()
        created_categories.append(category)

    total_products = 0
    for category, products in zip(created_categories, PRODUCTS_PER_CATEGORY):
        for prod_data in products:
            name_with_marker = f"{SEED_MARKER} {prod_data['name']}"
            existing = db.query(Product).filter(Product.name == name_with_marker).first()
            if existing:
                continue
            product = Product(
                category_id=category.id,
                name=name_with_marker,
                description=prod_data["description"],
                price=prod_data["price"],
                stock=prod_data["stock"],
                rating=prod_data["rating"],
            )
            db.add(product)
            total_products += 1

    db.commit()
    print(f"Seeded {len(created_categories)} categories and {total_products} products.")


def clean(db):
    products_deleted = db.query(Product).filter(Product.name.like(f"{SEED_MARKER}%")).delete(synchronize_session=False)
    categories_deleted = db.query(Category).filter(Category.name.like(f"{SEED_MARKER}%")).delete(synchronize_session=False)
    db.commit()
    print(f"Removed {products_deleted} products and {categories_deleted} categories.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "seed"

    if mode not in ("seed", "--clean"):
        print("Usage: python -m scripts.seed_products [--clean]")
        sys.exit(1)

    db = SessionLocal()
    try:
        if mode == "--clean":
            clean(db)
        else:
            seed(db)
    finally:
        db.close()
