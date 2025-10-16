"""Simple Database Initialization"""
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("Creating all database tables...")
    db.create_all()
    print("✅ Done!")
    
    # Show tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📊 Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"   ✓ {table}")
