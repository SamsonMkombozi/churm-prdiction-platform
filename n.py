"""
Database Migration Script - Add predicted_at Column
run_migration.py

This script adds the missing predicted_at column to the predictions table
"""
import sqlite3
import os
from datetime import datetime

def migrate_predictions_table():
    """Add predicted_at column to predictions table"""
    
    # Database path (adjust if needed)
    db_path = 'instance/churn_platform.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please update the db_path variable to point to your database file")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if predictions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='predictions'
        """)
        
        if not cursor.fetchone():
            print("❌ Predictions table not found")
            return False
        
        # Check if predicted_at column already exists
        cursor.execute("PRAGMA table_info(predictions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'predicted_at' in columns:
            print("✅ predicted_at column already exists")
            return True
        
        print("🔄 Adding predicted_at column...")
        
        # Add the predicted_at column
        cursor.execute("""
            ALTER TABLE predictions 
            ADD COLUMN predicted_at DATETIME
        """)
        
        # Update existing records to use created_at as predicted_at
        current_time = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE predictions 
            SET predicted_at = COALESCE(created_at, ?)
            WHERE predicted_at IS NULL
        """, (current_time,))
        
        # Count updated records
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE predicted_at IS NOT NULL")
        updated_count = cursor.fetchone()[0]
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Migration completed successfully!")
        print(f"   - Added predicted_at column")
        print(f"   - Updated {updated_count} existing records")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    db_path = '/instance/Churn_platform.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(predictions)")
        columns = {column[1]: column[2] for column in cursor.fetchall()}
        
        print("\n📋 Current predictions table structure:")
        for col_name, col_type in columns.items():
            marker = "✅" if col_name == 'predicted_at' else "  "
            print(f"{marker} {col_name}: {col_type}")
        
        # Check data
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(predicted_at) as with_predicted_at
            FROM predictions
        """)
        
        result = cursor.fetchone()
        total_records = result[0]
        records_with_predicted_at = result[1]
        
        print(f"\n📊 Data verification:")
        print(f"   Total records: {total_records}")
        print(f"   Records with predicted_at: {records_with_predicted_at}")
        
        if total_records > 0 and records_with_predicted_at == total_records:
            print("✅ All records have predicted_at values")
        elif total_records > 0:
            print(f"⚠️  {total_records - records_with_predicted_at} records missing predicted_at")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting predictions table migration...")
    
    # Run migration
    if migrate_predictions_table():
        print("\n🔍 Verifying migration...")
        verify_migration()
    else:
        print("\n❌ Migration failed - see errors above")
    
    print("\n📝 Next steps:")
    print("1. Replace your app/models/prediction.py with the fixed version")
    print("2. Restart your Flask application")
    print("3. Test predictions again")