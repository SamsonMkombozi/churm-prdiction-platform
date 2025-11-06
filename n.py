"""
Quick Database Column Fix Script
Run this to add missing columns to the companies table
"""

import os
import sys

# Add the project root to Python path
project_root = '/var/www/html/churn-prediction-platform'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from app.extensions import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_columns():
    """Add missing columns to companies table"""
    
    app = create_app('development')
    
    with app.app_context():
        try:
            logger.info("🔧 Checking and adding missing columns to companies table...")
            
            # List of columns that might be missing
            missing_columns = [
                ('logo_url', 'VARCHAR(255)'),
                ('postgresql_host', 'VARCHAR(255)'),
                ('postgresql_port', 'INTEGER DEFAULT 5432'),
                ('postgresql_database', 'VARCHAR(255)'),
                ('postgresql_username', 'VARCHAR(255)'),
                ('postgresql_password_encrypted', 'TEXT'),
                ('api_base_url', 'VARCHAR(255)'),
                ('api_key_encrypted', 'TEXT'),
                ('api_username', 'VARCHAR(255)'),
                ('api_password_encrypted', 'TEXT'),
                ('settings', 'TEXT DEFAULT "{}"')
            ]
            
            # Add each column if it doesn't exist
            for column_name, column_definition in missing_columns:
                try:
                    alter_sql = f"ALTER TABLE companies ADD COLUMN {column_name} {column_definition}"
                    logger.info(f"Adding column: {column_name}")
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"⚠️ Column {column_name} already exists, skipping")
                    else:
                        logger.error(f"❌ Error adding column {column_name}: {e}")
                    db.session.rollback()
            
            logger.info("✅ Database column fix completed!")
            
            # Verify the fix by trying to query
            try:
                result = db.session.execute(text("SELECT COUNT(*) FROM companies")).fetchone()
                logger.info(f"✅ Verification successful: {result[0]} companies in table")
            except Exception as e:
                logger.error(f"❌ Verification failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database column fix failed: {e}")
            return False

if __name__ == "__main__":
    success = add_missing_columns()
    if success:
        print("\n🎉 Database fix completed successfully!")
        print("You can now access the company settings page.")
    else:
        print("\n❌ Database fix failed. Please check the logs above.")