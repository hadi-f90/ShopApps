from .models import Contact, Item, StockMovement, Warehouse, db


def init_db():
    """Create all tables if they don't exist"""
    db.connect()
    db.create_tables([Contact,
                            Warehouse,
                            Item,
                            StockMovement
                            ], safe=True)  # safe=True avoids error if table exists
    print("✅ Database initialized successfully")
    db.close()

# Auto-init when imported
if __name__ == "__main__":
    init_db()