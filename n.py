#!/usr/bin/env python3
"""
Simple Database Migration Script
Add PostgreSQL configuration columns to companies table

Usage:
1. Make sure your Flask app is not running
2. Run: python migrate_company_db.py
3. Restart your Flask application

This script will safely add the missing columns without affecting existing data.
"""

import sqlite3
import os
import sys
from pathlib import Path

def find_database():
    """Find the SQLite database file"""
    possible_paths = [
        # Common Flask database locations
        'instance/app.db',
        'instance/database.db', 
        'instance/churn.db',
        'app.db',
        'database.db',
        'churn.db',
        'churn_prediction.db',
        # Check current directory
        './app.db',
        './database.db',
        # Check parent directories
        '../instance/app.db',
        '../app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Try to find any .db file in instance or current directory
    for directory in ['instance', '.']:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith('.db'):
                    return os.path.join(directory, file)
    
    return None

def check_companies_table(cursor):
    """Check if companies table exists and get current columns"""
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies';")
        if not cursor.fetchone():
            print("❌ Error: 'companies' table not found in database")
            return False, []
        
        cursor.execute("PRAGMA table_info(companies);")
        columns = [row[1] for row in cursor.fetchall()]
        return True, columns
    except Exception as e:
        print(f"❌ Error checking companies table: {e}")
        return False, []

def add_missing_columns(cursor, existing_columns):
    """Add missing PostgreSQL configuration columns"""
    
    # Define the columns we need to add
    new_columns = [
        ('postgresql_host', 'TEXT'),
        ('postgresql_port', 'INTEGER DEFAULT 5432'),
        ('postgresql_database', 'TEXT'),
        ('postgresql_username', 'TEXT'),
        ('postgresql_password_encrypted', 'TEXT'),
        ('api_base_url', 'TEXT'),
        ('api_username', 'TEXT'),
        ('api_password_encrypted', 'TEXT'),
        ('api_key_encrypted', 'TEXT'),
        ('settings', 'TEXT DEFAULT "{}"')
    ]
    
    added_count = 0
    skipped_count = 0
    
    for column_name, column_definition in new_columns:
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE companies ADD COLUMN {column_name} {column_definition};"
                cursor.execute(sql)
                print(f"✅ Added column: {column_name}")
                added_count += 1
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠️  Column {column_name} already exists")
                    skipped_count += 1
                else:
                    print(f"❌ Error adding column {column_name}: {e}")
                    return False
        else:
            print(f"⚠️  Column {column_name} already exists")
            skipped_count += 1
    
    print(f"\n📊 Summary: {added_count} columns added, {skipped_count} already existed")
    return True

def main():
    """Main migration function"""
    print("🚀 Starting database migration for PostgreSQL configuration...")
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Could not find database file!")
        print("\nPlease ensure your database exists in one of these locations:")
        print("  - instance/app.db")
        print("  - app.db") 
        print("  - database.db")
        print("\nOr specify the path manually by editing this script.")
        return False
    
    print(f"📂 Found database: {db_path}")
    
    # Create backup
    backup_path = f"{db_path}.backup"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Created backup: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
        response = input("Continue without backup? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        return False
    
    # Check companies table
    table_exists, existing_columns = check_companies_table(cursor)
    if not table_exists:
        conn.close()
        return False
    
    print(f"📋 Found {len(existing_columns)} existing columns")
    
    # Add missing columns
    success = add_missing_columns(cursor, existing_columns)
    
    if success:
        # Commit changes
        conn.commit()
        print("✅ Changes committed successfully!")
        
        # Verify changes
        cursor.execute("PRAGMA table_info(companies);")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Database now has {len(new_columns)} columns")
        
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Restart your Flask application")
        print("  2. Go to Company Settings")
        print("  3. Configure your PostgreSQL connection")
        print("  4. Test the connection")
        print("  5. Enjoy 10-50x faster sync performance!")
        
        return True
    else:
        # Rollback on error
        conn.rollback()
        conn.close()
        print("❌ Migration failed - no changes made")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)