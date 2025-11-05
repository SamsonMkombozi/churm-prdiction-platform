"""
Database Migration: Add Sync Fields to Company Model
migrations/add_company_sync_fields.py

Run this to add missing sync-related fields to your Company table.
"""

from sqlalchemy import text
from app.extensions import db

def add_company_sync_fields():
    """Add sync-related fields to Company table if they don't exist"""
    
    # List of fields to add with their SQL definitions
    fields_to_add = [
        ('last_sync_at', 'TIMESTAMP NULL'),
        ('sync_status', "VARCHAR(50) DEFAULT 'never'"),
        ('sync_error', 'TEXT NULL'),
        ('total_syncs', 'INTEGER DEFAULT 0'),
        ('postgresql_host', 'VARCHAR(255) NULL'),
        ('postgresql_port', 'INTEGER NULL'),
        ('postgresql_database', 'VARCHAR(255) NULL'),
        ('postgresql_username', 'VARCHAR(255) NULL'),
        ('postgresql_password_encrypted', 'TEXT NULL'),
        ('api_base_url', 'VARCHAR(255) NULL'),
        ('api_key_encrypted', 'TEXT NULL'),
        ('sync_settings', 'JSON NULL')
    ]
    
    try:
        # Check if we're using SQLite or PostgreSQL
        engine_name = db.engine.name
        
        for field_name, field_definition in fields_to_add:
            # Check if column exists
            if engine_name == 'sqlite':
                result = db.session.execute(text(
                    f"PRAGMA table_info(company)"
                )).fetchall()
                
                existing_columns = [row[1] for row in result]
                
                if field_name not in existing_columns:
                    print(f"Adding column {field_name} to company table...")
                    
                    # SQLite syntax
                    alter_sql = f"ALTER TABLE company ADD COLUMN {field_name} {field_definition}"
                    db.session.execute(text(alter_sql))
                    
            elif engine_name == 'postgresql':
                # Check if column exists in PostgreSQL
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'company' AND column_name = :column_name
                """), {'column_name': field_name}).fetchone()
                
                if not result:
                    print(f"Adding column {field_name} to company table...")
                    
                    # PostgreSQL syntax - adjust field definitions
                    if field_definition.startswith('JSON'):
                        pg_definition = 'JSONB'
                    else:
                        pg_definition = field_definition
                    
                    alter_sql = f"ALTER TABLE company ADD COLUMN {field_name} {pg_definition}"
                    db.session.execute(text(alter_sql))
        
        # Commit all changes
        db.session.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration failed: {str(e)}")
        return False

def check_company_schema():
    """Check what columns currently exist in the company table"""
    
    try:
        engine_name = db.engine.name
        
        if engine_name == 'sqlite':
            result = db.session.execute(text("PRAGMA table_info(company)")).fetchall()
            print("\n🔍 Current Company table schema (SQLite):")
            print("Column Name | Type | Not Null | Default")
            print("-" * 50)
            for row in result:
                print(f"{row[1]:<20} | {row[2]:<10} | {row[3]:<8} | {row[4]}")
                
        elif engine_name == 'postgresql':
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'company'
                ORDER BY ordinal_position
            """)).fetchall()
            
            print("\n🔍 Current Company table schema (PostgreSQL):")
            print("Column Name | Type | Nullable | Default")
            print("-" * 50)
            for row in result:
                print(f"{row[0]:<20} | {row[1]:<10} | {row[2]:<8} | {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema check failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Company Sync Fields Migration")
    print("=" * 40)
    
    # First check current schema
    print("\n1. Checking current schema...")
    check_company_schema()
    
    # Then add missing fields
    print("\n2. Adding missing fields...")
    success = add_company_sync_fields()
    
    if success:
        print("\n3. Verifying updated schema...")
        check_company_schema()
        print("\n✅ Migration completed! Your Company model now has all required sync fields.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")