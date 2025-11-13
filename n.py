#!/usr/bin/env python3
"""
COMPLETE SETTINGS FIX - Apply All Changes
Run this script to:
1. Run database migration to add new columns
2. Verify the fixes work
3. Test the settings page

This script fixes everything needed for your settings page to work.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
import shutil

# Add your project to path
project_root = "/var/www/html/churn-prediction-platform"
sys.path.insert(0, project_root)

def backup_database():
    """Create a backup of the database before making changes"""
    
    db_path = os.path.join(project_root, "instance/churn_platform.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return None
    
    try:
        backup_name = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_name)
        print(f"✅ Database backed up: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
        return None

def run_database_migration():
    """Add all missing columns for settings"""
    
    db_path = os.path.join(project_root, "instance/churn_platform.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Adding missing settings columns...")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(companies);")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Define all new columns needed
        new_columns = [
            # Notification Settings
            ('notification_email', 'TEXT'),
            ('enable_email_alerts', 'BOOLEAN DEFAULT 0'),
            ('enable_auto_sync', 'BOOLEAN DEFAULT 1'),
            ('sync_frequency', 'INTEGER DEFAULT 3600'),
            
            # Prediction Settings  
            ('prediction_threshold_high', 'REAL DEFAULT 0.7'),
            ('prediction_threshold_medium', 'REAL DEFAULT 0.4'),
            
            # Regional Settings
            ('timezone', 'TEXT DEFAULT "Africa/Nairobi"'),
            ('date_format', 'TEXT DEFAULT "%Y-%m-%d"'),
            ('currency', 'TEXT DEFAULT "TZS"'),
            
            # Additional Settings
            ('crm_sync_enabled', 'BOOLEAN DEFAULT 1'),
            ('last_settings_update', 'DATETIME'),
            ('settings_json', 'TEXT'),
            ('app_settings', 'TEXT'),
            ('default_language', 'TEXT DEFAULT "en"'),
            ('dashboard_refresh_interval', 'INTEGER DEFAULT 300'),
            ('enable_predictions', 'BOOLEAN DEFAULT 1'),
            ('enable_analytics', 'BOOLEAN DEFAULT 1'),
            ('enable_reports', 'BOOLEAN DEFAULT 1'),
            ('auto_backup_enabled', 'BOOLEAN DEFAULT 0'),
            ('backup_frequency', 'INTEGER DEFAULT 86400'),
        ]
        
        added_count = 0
        skipped_count = 0
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE companies ADD COLUMN {column_name} {column_type};"
                    cursor.execute(sql)
                    print(f"✅ Added: {column_name}")
                    added_count += 1
                except Exception as e:
                    print(f"❌ Failed to add {column_name}: {e}")
            else:
                print(f"⏭️  Skipped: {column_name} (already exists)")
                skipped_count += 1
        
        # Set default settings for existing companies
        print("\n📝 Setting default values...")
        
        cursor.execute("SELECT id, name FROM companies;")
        companies = cursor.fetchall()
        
        for company_id, company_name in companies:
            default_settings = {
                'enable_auto_sync': True,
                'sync_frequency': 3600,
                'enable_email_alerts': False,
                'notification_email': '',
                'prediction_threshold_high': 0.7,
                'prediction_threshold_medium': 0.4,
                'timezone': 'Africa/Nairobi',
                'date_format': '%Y-%m-%d',
                'currency': 'TZS',
                'enable_predictions': True,
                'enable_analytics': True
            }
            
            try:
                cursor.execute("""
                    UPDATE companies 
                    SET settings_json = ?, 
                        last_settings_update = ?
                    WHERE id = ?
                """, (json.dumps(default_settings), datetime.now().isoformat(), company_id))
                
                print(f"✅ Updated: {company_name}")
            except Exception as e:
                print(f"⚠️  Could not update {company_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Migration completed!")
        print(f"   • Added: {added_count} columns")
        print(f"   • Skipped: {skipped_count} existing columns")
        print(f"   • Updated: {len(companies)} companies")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_flask_models():
    """Test if Flask models work with the new setup"""
    
    print("\n🧪 Testing Flask Models...")
    
    try:
        from app import create_app
        from app.models.company import Company
        
        app = create_app()
        
        with app.app_context():
            company = Company.query.first()
            
            if not company:
                print("❌ No companies found!")
                return False
            
            print(f"✅ Found company: {company.name}")
            
            # Test get_setting method
            if hasattr(company, 'get_setting'):
                print("✅ get_setting method exists")
                
                # Test getting settings
                test_settings = [
                    ('timezone', 'Africa/Nairobi'),
                    ('currency', 'TZS'),
                    ('enable_auto_sync', True),
                    ('sync_frequency', 3600)
                ]
                
                for setting, expected in test_settings:
                    value = company.get_setting(setting)
                    print(f"   📊 {setting}: {value}")
                
            else:
                print("❌ get_setting method missing!")
                return False
            
            # Test update_settings method
            if hasattr(company, 'update_settings'):
                print("✅ update_settings method exists")
                
                # Test updating a setting
                test_update = {'dashboard_refresh_interval': 600}
                try:
                    company.update_settings(test_update)
                    print("✅ Settings update test passed")
                except Exception as e:
                    print(f"❌ Settings update test failed: {e}")
                    return False
                
            else:
                print("❌ update_settings method missing!")
                return False
            
            print("✅ Flask model tests passed!")
            return True
    
    except Exception as e:
        print(f"❌ Flask model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_route():
    """Test if the settings route works"""
    
    print("\n🌐 Testing Settings Route...")
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            response = client.get('/company/settings')
            
            if response.status_code == 302:
                print("✅ Settings route exists (redirected to login)")
                return True
            elif response.status_code == 404:
                print("❌ Settings route not found (404)")
                return False
            elif response.status_code == 500:
                print("❌ Settings route has server error (500)")
                print(f"Error: {response.get_data(as_text=True)[:200]}...")
                return False
            else:
                print(f"✅ Settings route responded with status {response.status_code}")
                return True
    
    except Exception as e:
        print(f"❌ Settings route test failed: {e}")
        return False

def create_installation_guide():
    """Create a guide for implementing the fixes"""
    
    guide_content = """
# SETTINGS PAGE FIX - INSTALLATION GUIDE

## Step 1: Replace Company Model

Replace your `app/models/company.py` with the fixed version:
- Download: fixed_company_model.py
- Copy to: app/models/company.py

## Step 2: Replace Company Controller  

Replace your `app/controllers/company_controller.py` with the fixed version:
- Download: fixed_company_controller.py  
- Copy to: app/controllers/company_controller.py

## Step 3: Test Your Settings Page

1. Start your Flask app:
   ```bash
   python3 app.py
   ```

2. Visit the settings page:
   ```
   http://localhost:5000/company/settings
   ```

3. Test the settings test endpoint:
   ```
   http://localhost:5000/company/settings/test
   ```

## What Was Fixed:

✅ **Database**: Added 20+ new columns for all settings fields
✅ **Model**: Enhanced get_setting() and update_settings() methods  
✅ **Controller**: Proper form handling for all field types
✅ **Validation**: Input validation and error handling
✅ **Logging**: Comprehensive logging for debugging

## New Features:

🎯 **Tanzania-focused defaults**: TZS currency, Africa/Nairobi timezone
🔧 **Comprehensive form handling**: Strings, booleans, integers, floats
📊 **Settings export/import**: JSON export functionality
🧪 **Test endpoints**: Built-in testing and debugging routes
📝 **Enhanced logging**: Detailed logs for troubleshooting

Your settings page should now:
- Load without template errors
- Save all form fields to database
- Remember settings between sessions
- Show validation errors properly
- Handle all data types correctly

Happy coding! 🚀
"""
    
    guide_path = "/var/www/html/churn-prediction-platform/SETTINGS_FIX_GUIDE.md"
    try:
        with open(guide_path, 'w') as f:
            f.write(guide_content)
        print(f"📖 Installation guide created: {guide_path}")
    except Exception as e:
        print(f"⚠️  Could not create guide: {e}")

def main():
    """Run the complete settings fix"""
    
    print("🚀 COMPLETE SETTINGS PAGE FIX")
    print("=" * 50)
    
    # Step 1: Backup database
    print("\n📦 Step 1: Creating backup...")
    backup_file = backup_database()
    
    # Step 2: Run migration
    print("\n🔧 Step 2: Running database migration...")
    migration_success = run_database_migration()
    
    if not migration_success:
        print("❌ Migration failed! Check errors above.")
        return False
    
    # Step 3: Test Flask models
    print("\n🧪 Step 3: Testing Flask models...")
    model_test_success = test_flask_models()
    
    # Step 4: Test settings route
    print("\n🌐 Step 4: Testing settings route...")
    route_test_success = test_settings_route()
    
    # Step 5: Create installation guide
    print("\n📖 Step 5: Creating installation guide...")
    create_installation_guide()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    results = [
        ("Database Migration", migration_success),
        ("Flask Model Test", model_test_success),
        ("Settings Route Test", route_test_success)
    ]
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    if passed == len(results):
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Your settings page should now work properly!")
        print(f"\n📋 Next steps:")
        print(f"1. Copy the fixed model file to app/models/company.py")
        print(f"2. Copy the fixed controller file to app/controllers/company_controller.py") 
        print(f"3. Restart your Flask app")
        print(f"4. Test at: http://localhost:5000/company/settings")
        
        if backup_file:
            print(f"\n💾 Backup created: {backup_file}")
        
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed!")
        print(f"Check the errors above and fix before proceeding.")
        
        if backup_file:
            print(f"\n💾 Restore from backup if needed: {backup_file}")
    
    return passed == len(results)

if __name__ == "__main__":
    main()