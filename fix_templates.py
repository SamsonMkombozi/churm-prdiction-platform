#!/usr/bin/env python3
"""
Quick Database Migration Script
Adds missing columns to companies table
Run this: python3 migrate_company_columns.py
"""

from app import create_app, db
from sqlalchemy import text

def migrate_company_columns():
    """Add missing columns to companies table"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("DATABASE MIGRATION - Adding Missing Columns")
        print("=" * 60)
        
        # Get database connection
        connection = db.engine.connect()
        
        # List of columns to add
        migrations = [
            ("description", "ALTER TABLE companies ADD COLUMN description TEXT"),
            ("industry", "ALTER TABLE companies ADD COLUMN industry VARCHAR(100)"),
            ("website", "ALTER TABLE companies ADD COLUMN website VARCHAR(255)"),
            ("sync_error", "ALTER TABLE companies ADD COLUMN sync_error TEXT"),
            ("total_syncs", "ALTER TABLE companies ADD COLUMN total_syncs INTEGER DEFAULT 0"),
        ]
        
        for column_name, sql in migrations:
            try:
                print(f"\nAdding column: {column_name}")
                connection.execute(text(sql))
                connection.commit()
                print(f"✅ Added: {column_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️  Column {column_name} already exists, skipping")
                else:
                    print(f"❌ Error adding {column_name}: {e}")
        
        connection.close()
        
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        print("\nNext step: Restart your app")
        print("  python3 run.py")

if __name__ == '__main__':
    migrate_company_columns()