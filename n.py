#!/usr/bin/env python3
"""
Comprehensive PostgreSQL Configuration Debug Script
This will find and fix the "NOT CONFIGURED" issue
"""

import sys
sys.path.insert(0, '/var/www/html/churn-prediction-platform')

def debug_postgresql_config():
    """Debug PostgreSQL configuration step by step"""
    
    print("=" * 80)
    print("POSTGRESQL CONFIGURATION DEBUG")
    print("=" * 80)
    print()
    
    # Step 1: Check database connection
    print("Step 1: Checking SQLite database connection...")
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask app created successfully")
    except Exception as e:
        print(f"✗ Failed to create Flask app: {e}")
        return False
    
    with app.app_context():
        try:
            from app.extensions import db
            from app.models.company import Company
            print("✓ Imports successful")
        except Exception as e:
            print(f"✗ Import error: {e}")
            return False
        
        # Step 2: Check Company table
        print("\nStep 2: Checking Company table...")
        try:
            companies = Company.query.all()
            print(f"✓ Found {len(companies)} company(ies)")
            
            if not companies:
                print("✗ No companies in database!")
                return False
            
            company = companies[0]
            print(f"  Working with: {company.name} (ID: {company.id})")
            
        except Exception as e:
            print(f"✗ Error querying companies: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Check PostgreSQL fields in database
        print("\nStep 3: Checking PostgreSQL fields in database...")
        try:
            import sqlite3
            conn = sqlite3.connect('instance/churn_platform.db')
            cursor = conn.cursor()
            
            # Get actual column names
            cursor.execute("PRAGMA table_info(companies)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print("  Available columns in companies table:")
            pg_related = [c for c in column_names if 'postgresql' in c.lower() or 'postgres' in c.lower()]
            for col in pg_related:
                print(f"    - {col}")
            
            # Get actual values
            cursor.execute(f"""
                SELECT id, name, postgresql_host, postgresql_port, 
                       postgresql_database, postgresql_username, 
                       postgresql_password_encrypted
                FROM companies WHERE id = {company.id}
            """)
            
            result = cursor.fetchone()
            if result:
                print("\n  PostgreSQL credentials in database:")
                print(f"    Host: {result[2]}")
                print(f"    Port: {result[3]}")
                print(f"    Database: {result[4]}")
                print(f"    Username: {result[5]}")
                print(f"    Password: {'***' if result[6] else 'NOT SET'}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"✗ Error checking database: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Check Company model attributes
        print("\nStep 4: Checking Company model attributes...")
        try:
            print(f"  postgresql_host: {getattr(company, 'postgresql_host', 'MISSING')}")
            print(f"  postgresql_port: {getattr(company, 'postgresql_port', 'MISSING')}")
            print(f"  postgresql_database: {getattr(company, 'postgresql_database', 'MISSING')}")
            print(f"  postgresql_username: {getattr(company, 'postgresql_username', 'MISSING')}")
            print(f"  postgresql_password_encrypted: {'***' if getattr(company, 'postgresql_password_encrypted', None) else 'MISSING'}")
        except Exception as e:
            print(f"✗ Error accessing attributes: {e}")
        
        # Step 5: Check has_postgresql_config method
        print("\nStep 5: Checking has_postgresql_config() method...")
        try:
            if hasattr(company, 'has_postgresql_config'):
                result = company.has_postgresql_config()
                print(f"  has_postgresql_config() returns: {result}")
                
                # Debug the method
                if not result:
                    print("\n  Debugging why it returns False:")
                    host = company.postgresql_host
                    database = company.postgresql_database
                    username = company.postgresql_username
                    password = company.postgresql_password_encrypted
                    
                    print(f"    host: {repr(host)} -> bool: {bool(host and host.strip())}")
                    print(f"    database: {repr(database)} -> bool: {bool(database and database.strip())}")
                    print(f"    username: {repr(username)} -> bool: {bool(username and username.strip())}")
                    print(f"    password: {repr(password)} -> bool: {bool(password and password.strip())}")
            else:
                print("  ✗ has_postgresql_config() method not found!")
                
        except Exception as e:
            print(f"✗ Error checking has_postgresql_config: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 6: Check get_postgresql_config method
        print("\nStep 6: Checking get_postgresql_config() method...")
        try:
            if hasattr(company, 'get_postgresql_config'):
                config = company.get_postgresql_config()
                print(f"  get_postgresql_config() returns:")
                for key, value in config.items():
                    if 'password' in key.lower():
                        print(f"    {key}: {'***' if value else 'None'}")
                    else:
                        print(f"    {key}: {value}")
            else:
                print("  ✗ get_postgresql_config() method not found!")
                
        except Exception as e:
            print(f"✗ Error checking get_postgresql_config: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 7: Check CRM service
        print("\nStep 7: Checking CRM service...")
        try:
            # Import the actual service being used
            try:
                from app.services.crm_service import DisconnectionBasedCRMService
                service_class = DisconnectionBasedCRMService
                print("  Using: DisconnectionBasedCRMService")
            except ImportError:
                try:
                    from app.services.crm_service import EnhancedCRMService
                    service_class = EnhancedCRMService
                    print("  Using: EnhancedCRMService")
                except ImportError:
                    from app.services.crm_service import CRMService
                    service_class = CRMService
                    print("  Using: CRMService")
            
            # Create service instance
            crm_service = service_class(company)
            print("  ✓ CRM service instance created")
            
            # Check get_connection_info
            connection_info = crm_service.get_connection_info()
            print(f"\n  get_connection_info() returns:")
            print(f"    postgresql_configured: {connection_info.get('postgresql_configured')}")
            print(f"    api_configured: {connection_info.get('api_configured')}")
            print(f"    preferred_method: {connection_info.get('preferred_method')}")
            
            if not connection_info.get('postgresql_configured'):
                print("\n  ✗ CRM service says PostgreSQL is NOT configured!")
                print("  This is the problem!")
                
        except Exception as e:
            print(f"✗ Error checking CRM service: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 8: Test PostgreSQL connection
        print("\nStep 8: Testing actual PostgreSQL connection...")
        try:
            import psycopg2
            
            config = company.get_postgresql_config()
            
            print(f"  Attempting connection to:")
            print(f"    Host: {config['host']}")
            print(f"    Port: {config['port']}")
            print(f"    Database: {config['database']}")
            print(f"    Username: {config['username']}")
            
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                dbname=config['database'],
                user=config['username'],
                password=config['password'],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crm_customers")
            count = cursor.fetchone()[0]
            
            print(f"  ✓ Connection successful!")
            print(f"  ✓ Found {count:,} customers in CRM database")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
        
        print("\n" + "=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        
        # Provide fix recommendations
        print("\nRECOMMENDATIONS:")
        
        if not company.has_postgresql_config():
            print("\n1. PostgreSQL credentials are missing or invalid")
            print("   Run this to set them:")
            print("""
   python3 << 'EOF'
   import sys
   sys.path.insert(0, '/var/www/html/churn-prediction-platform')
   from app import create_app
   from app.extensions import db
   from app.models.company import Company
   
   app = create_app()
   with app.app_context():
       company = Company.query.first()
       company.postgresql_host = '196.250.208.220'
       company.postgresql_port = 5432
       company.postgresql_database = 'AnalyticsWH'
       company.postgresql_username = 'analytics'
       company.postgresql_password_encrypted = 'NhKh4Cpcdh'
       db.session.commit()
       print("✓ Credentials updated!")
   EOF
            """)
        else:
            print("\n✓ PostgreSQL credentials look good!")
            print("  If you're still getting errors, check:")
            print("  1. The CRM service is using the right method")
            print("  2. Restart Flask after making changes")


if __name__ == "__main__":
    try:
        debug_postgresql_config()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)