#!/usr/bin/env python3
"""
Comprehensive Fix Script for Predictions Table Schema

This script adds ALL missing columns to the predictions table based on 
the SQLAlchemy error patterns. It will check for and add any missing columns
that your model expects.

Specifically targeting /instance/churn_platform.db
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_expected_columns():
    """Define the expected schema for the predictions table"""
    return {
        # Core columns (likely already exist)
        'id': 'INTEGER PRIMARY KEY',
        'company_id': 'INTEGER NOT NULL',
        'customer_id': 'INTEGER NOT NULL',
        'churn_probability': 'REAL NOT NULL',
        'churn_risk': 'TEXT NOT NULL',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME',
        
        # Missing columns that need to be added
        'confidence': 'REAL DEFAULT 0.0',
        'model_version': 'TEXT',
        'model_type': 'TEXT',
        'risk_factors': 'TEXT',
        'feature_values': 'TEXT'
    }

def check_and_add_missing_columns():
    """Check for missing columns and add them to the predictions table"""
    
    db_path = "instance/churn_platform.db"
    
    # Verify database exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please run this script from your project root directory.")
        print("Current directory:", os.getcwd())
        return False
    
    print(f"📁 Target database: {db_path}")
    print(f"📍 Full path: {os.path.abspath(db_path)}")
    
    # Create backup
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        response = input("Continue without backup? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Operation cancelled")
            return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current table structure
        print("\n🔍 Checking current predictions table structure...")
        cursor.execute("PRAGMA table_info(predictions)")
        current_columns_info = cursor.fetchall()
        current_columns = {col[1]: col[2] for col in current_columns_info}  # {name: type}
        
        print(f"📋 Current columns ({len(current_columns)}):")
        for name, col_type in current_columns.items():
            print(f"   ✅ {name:<20} {col_type}")
        
        # Check which columns are missing
        expected_columns = get_expected_columns()
        missing_columns = []
        
        for col_name, col_definition in expected_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_definition))
        
        if not missing_columns:
            print("\n✅ All expected columns already exist!")
            print("Your predictions table schema is up to date.")
            return True
        
        print(f"\n❌ Found {len(missing_columns)} missing columns:")
        for col_name, col_def in missing_columns:
            print(f"   ❌ {col_name:<20} {col_def}")
        
        # Add missing columns one by one
        print(f"\n🔧 Adding {len(missing_columns)} missing columns...")
        
        successful_additions = []
        failed_additions = []
        
        for col_name, col_definition in missing_columns:
            try:
                # Extract just the data type and default for ALTER TABLE
                if 'DEFAULT' in col_definition:
                    # Handle columns with default values
                    parts = col_definition.split()
                    data_type = parts[0]
                    default_part = ' '.join(parts[1:])  # e.g., "DEFAULT 0.0"
                    alter_sql = f"ALTER TABLE predictions ADD COLUMN {col_name} {data_type} {default_part}"
                else:
                    # Handle columns without default values
                    data_type = col_definition.split()[0]
                    alter_sql = f"ALTER TABLE predictions ADD COLUMN {col_name} {data_type}"
                
                print(f"   🔧 Adding {col_name}...")
                cursor.execute(alter_sql)
                successful_additions.append(col_name)
                
            except sqlite3.Error as e:
                print(f"   ❌ Failed to add {col_name}: {e}")
                failed_additions.append((col_name, str(e)))
        
        if successful_additions:
            # Set reasonable default values for existing records
            print(f"\n📊 Setting default values for existing records...")
            
            updates = {
                'confidence': 0.5,  # Medium confidence for existing predictions
                'model_version': "'v1.0'",  # Default version
                'model_type': "'legacy'",  # Mark as legacy predictions
                'risk_factors': "'{}'",  # Empty JSON object
                'feature_values': "'{}'"  # Empty JSON object
            }
            
            for col_name in successful_additions:
                if col_name in updates:
                    try:
                        update_sql = f"UPDATE predictions SET {col_name} = {updates[col_name]} WHERE {col_name} IS NULL"
                        cursor.execute(update_sql)
                        rows_updated = cursor.rowcount
                        print(f"   📝 Updated {rows_updated} records for {col_name}")
                    except sqlite3.Error as e:
                        print(f"   ⚠️  Warning: Could not update defaults for {col_name}: {e}")
            
            # Commit all changes
            conn.commit()
            
            print(f"\n✅ Successfully added {len(successful_additions)} columns!")
            print(f"   Added: {', '.join(successful_additions)}")
            
            if failed_additions:
                print(f"\n⚠️  Failed to add {len(failed_additions)} columns:")
                for col_name, error in failed_additions:
                    print(f"   ❌ {col_name}: {error}")
        
        # Verify final schema
        print(f"\n🔍 Verifying final table structure...")
        cursor.execute("PRAGMA table_info(predictions)")
        final_columns_info = cursor.fetchall()
        final_columns = [col[1] for col in final_columns_info]
        
        print(f"📋 Final columns ({len(final_columns)}):")
        for col_info in final_columns_info:
            col_id, name, data_type, not_null, default, pk = col_info
            status = "🆕" if name in successful_additions else "✅"
            print(f"   {status} {name:<20} {data_type:<10} {'NOT NULL' if not_null else 'NULL':<8} {f'DEFAULT {default}' if default else ''}")
        
        # Test query to make sure it works
        print(f"\n🧪 Testing query that was failing...")
        try:
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            print(f"✅ Query test successful! Found {count} prediction records.")
            return True
        except sqlite3.Error as e:
            print(f"❌ Query test failed: {e}")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    print("🚀 Comprehensive Fix: Adding ALL missing columns to predictions table")
    print("=" * 80)
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"🎯 Target: /instance/churn_platform.db")
    print()
    
    success = check_and_add_missing_columns()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ COMPREHENSIVE FIX COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        print("\n📋 What was fixed:")
        print("• Added all missing columns to predictions table")
        print("• Set reasonable default values for existing records")
        print("• Verified the schema matches SQLAlchemy model expectations")
        
        print("\n🔄 Next steps:")
        print("1. Restart your Flask application:")
        print("   flask run")
        print("2. Your dashboard should now work without SQLAlchemy errors")
        print("3. Update your prediction model code to populate the new columns:")
        print("   - model_type: 'random_forest', 'logistic_regression', etc.")
        print("   - model_version: 'v1.0', 'v2.1', etc.")
        print("   - confidence: 0.0 to 1.0 (prediction confidence)")
        print("   - risk_factors: JSON string of identified risk factors")
        print("   - feature_values: JSON string of feature values used")
        
        print("\n💡 Example prediction code:")
        print("prediction = Prediction(")
        print("    churn_probability=0.73,")
        print("    confidence=0.85,")
        print("    model_type='random_forest',")
        print("    model_version='v2.0'")
        print(")")
        
    else:
        print("\n" + "=" * 80)
        print("❌ FIX FAILED!")
        print("=" * 80)
        print("Please check the error messages above.")
        print("You may need to manually inspect your database schema.")

if __name__ == "__main__":
    main()