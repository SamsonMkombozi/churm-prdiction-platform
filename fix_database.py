"""
Database Schema Fix Script
fix_database.py

This script will update your database schema to match the new models
"""
import sqlite3
import os
from datetime import datetime

def fix_database():
    """Fix database schema to match new models"""
    
    db_path = 'churn_prediction.db'
    
    print("🔧 Fixing database schema...")
    print("=" * 40)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if predictions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("📊 Predictions table exists, checking columns...")
            
            # Get current columns
            cursor.execute("PRAGMA table_info(predictions);")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            # Add missing columns
            missing_columns = {
                'confidence': 'TEXT',
                'model_type': 'TEXT', 
                'risk_factors': 'TEXT',
                'feature_values': 'TEXT',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            }
            
            for column, column_type in missing_columns.items():
                if column not in columns:
                    try:
                        if column in ['created_at', 'updated_at']:
                            default_value = f"DEFAULT '{datetime.utcnow().isoformat()}'"
                        else:
                            default_value = "DEFAULT NULL"
                        
                        sql = f"ALTER TABLE predictions ADD COLUMN {column} {column_type} {default_value};"
                        cursor.execute(sql)
                        print(f"✅ Added column: {column}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print(f"⚠️ Column {column} already exists")
                        else:
                            print(f"❌ Failed to add column {column}: {e}")
        else:
            print("📊 Creating predictions table from scratch...")
            
            # Create predictions table with all columns
            create_table_sql = """
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                customer_id TEXT NOT NULL,
                churn_probability REAL NOT NULL,
                churn_risk TEXT NOT NULL,
                confidence TEXT,
                model_version TEXT,
                model_type TEXT,
                risk_factors TEXT,
                feature_values TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_sql)
            print("✅ Created predictions table")
        
        # Commit changes
        conn.commit()
        print("✅ Database schema updated successfully!")
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(predictions);")
        columns = cursor.fetchall()
        print(f"\n📋 Final predictions table schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()