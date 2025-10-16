"""
Initialize Database
init_db.py

Creates all database tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.company import Company
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.models.prediction import ChurnPrediction

def init_database():
    """Initialize the database"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (careful!)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("✅ Database tables created successfully!")
        
        # Show what tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print("\n🎉 Database initialization complete!")

if __name__ == '__main__':
    init_database()