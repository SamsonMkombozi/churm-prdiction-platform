#!/usr/bin/env python3
"""
🔧 FINAL CRM SYNC TEST - With Proper Flask Context
Test the completely fixed CRM sync functionality
"""

import os
import sys

# Add the app directory to the Python path
app_path = '/var/www/html/churn-prediction-platform'
if app_path not in sys.path:
    sys.path.insert(0, app_path)

def main():
    print("🚀 FINAL CRM SYNC TEST")
    print("=" * 50)
    
    try:
        # Import and create Flask app
        print("📱 Creating Flask application...")
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app context established")
            
            # Import models
            from app.models.company import Company
            from app.services.crm_service import EnhancedCRMService
            
            # Get company
            companies = Company.query.all()
            if not companies:
                print("❌ No companies found!")
                return False
            
            company = companies[0]
            print(f"🏢 Testing with company: {company.name}")
            
            # Create CRM service
            crm_service = EnhancedCRMService(company)
            print("✅ CRM service created")
            
            # Test connection
            connection_info = crm_service.get_connection_info()
            print(f"🔌 Connection method: {connection_info['preferred_method']}")
            
            if connection_info['postgresql_configured']:
                # Test PostgreSQL connection
                test_result = crm_service.test_postgresql_connection()
                if test_result['success']:
                    print("✅ PostgreSQL connection test passed")
                    print(f"📊 Found tables: {test_result.get('tables', [])}")
                    
                    # Show actual table columns
                    if 'table_columns' in test_result:
                        for table, columns in test_result['table_columns'].items():
                            print(f"   📋 {table}: {columns}")
                    
                    # Test actual sync
                    print("\n🔄 Testing sync process...")
                    sync_options = {
                        'sync_customers': True,
                        'sync_payments': False,
                        'sync_tickets': False,
                        'sync_usage': False
                    }
                    
                    sync_result = crm_service.sync_data_selective(sync_options)
                    
                    if sync_result['success']:
                        print("✅ SYNC TEST PASSED!")
                        print(f"📊 Sync stats: {sync_result['stats']}")
                        if 'performance' in sync_result:
                            perf = sync_result['performance']
                            print(f"⚡ Performance: {perf['records_per_second']} records/sec")
                        
                        print("\n🎉 SUCCESS! Your CRM sync is now working!")
                        return True
                    else:
                        print(f"❌ Sync failed: {sync_result['message']}")
                        if 'error_details' in sync_result:
                            print(f"🔍 Details: {sync_result['error_details']}")
                        return False
                else:
                    print(f"❌ PostgreSQL connection failed: {test_result['message']}")
                    return False
            else:
                print("❌ PostgreSQL not configured")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Replace your crm_service.py with the fixed version")
        print("2. Restart your Flask application")
        print("3. Test the sync from the CRM dashboard")
        print("4. Enjoy lightning-fast PostgreSQL sync! ⚡")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check the error messages above")
        print("2. Verify PostgreSQL credentials in Company Settings")
        print("3. Ensure table columns match your actual database")
    
    print("=" * 50)

if __name__ == "__main__":
    main()