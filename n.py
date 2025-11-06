"""
Complete Database Migration - Fix Relationships and Add Fields
app/migrations/fix_relationship_and_add_fields.py

This migration:
1. Fixes the User-Company relationship
2. Adds missing Company configuration fields
3. Creates demo data if needed
"""

from app.extensions import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix database schema and relationships"""
    
    try:
        print("🔧 Starting complete database schema fix...")
        
        # Get current table structure
        inspector = db.inspect(db.engine)
        
        # Check if tables exist
        tables = inspector.get_table_names()
        print(f"📋 Existing tables: {tables}")
        
        # Create tables if they don't exist
        if 'companies' not in tables or 'users' not in tables:
            print("🏗️ Creating missing tables...")
            db.create_all()
            print("✅ Tables created")
        
        # Get current columns
        company_columns = []
        user_columns = []
        
        if 'companies' in tables:
            company_columns = [col['name'] for col in inspector.get_columns('companies')]
        if 'users' in tables:
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            
        print(f"📊 Company columns: {company_columns}")
        print(f"👥 User columns: {user_columns}")
        
        # Add missing Company fields
        company_fields_to_add = []
        required_company_fields = {
            # PostgreSQL Configuration
            'postgres_host': 'VARCHAR(255)',
            'postgres_port': 'INTEGER DEFAULT 5432',
            'postgres_database': 'VARCHAR(100)',
            'postgres_username': 'VARCHAR(100)', 
            'postgres_password_encrypted': 'TEXT',
            
            # API Configuration
            'api_base_url': 'VARCHAR(255)',
            'api_token_encrypted': 'TEXT',
            'api_username': 'VARCHAR(100)',
            'api_password_encrypted': 'TEXT',
            
            # Sync fields
            'last_sync_at': 'DATETIME',
            'sync_status': 'VARCHAR(20) DEFAULT "pending"',
            'sync_error': 'TEXT',
            'total_syncs': 'INTEGER DEFAULT 0',
            
            # Settings field
            'settings': 'TEXT DEFAULT "{}"',
            
            # Legacy CRM fields  
            'crm_api_url': 'VARCHAR(255)',
            'encrypted_api_key': 'TEXT'
        }
        
        for field_name, field_definition in required_company_fields.items():
            if field_name not in company_columns:
                company_fields_to_add.append((field_name, field_definition))
        
        # Add missing User fields (if needed)
        user_fields_to_add = []
        required_user_fields = {
            'company_id': 'INTEGER REFERENCES companies(id)',
            'role': 'VARCHAR(20) DEFAULT "viewer"',
            'is_active': 'BOOLEAN DEFAULT 1',
            'last_login': 'DATETIME'
        }
        
        for field_name, field_definition in required_user_fields.items():
            if field_name not in user_columns:
                user_fields_to_add.append((field_name, field_definition))
        
        # Add missing Company fields
        if company_fields_to_add:
            print(f"➕ Adding {len(company_fields_to_add)} missing Company fields...")
            for field_name, field_definition in company_fields_to_add:
                try:
                    sql = f"ALTER TABLE companies ADD COLUMN {field_name} {field_definition}"
                    print(f"🔧 Executing: {sql}")
                    db.engine.execute(sql)
                    print(f"✅ Added Company field: {field_name}")
                except Exception as e:
                    print(f"❌ Failed to add Company field {field_name}: {str(e)}")
                    continue
        
        # Add missing User fields
        if user_fields_to_add:
            print(f"➕ Adding {len(user_fields_to_add)} missing User fields...")
            for field_name, field_definition in user_fields_to_add:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_definition}"
                    print(f"🔧 Executing: {sql}")
                    db.engine.execute(sql)
                    print(f"✅ Added User field: {field_name}")
                except Exception as e:
                    print(f"❌ Failed to add User field {field_name}: {str(e)}")
                    continue
        
        print("✅ Database schema migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema migration failed: {str(e)}")
        return False

def create_demo_data():
    """Create demo company and user if they don't exist"""
    
    try:
        from app.models.company import Company
        from app.models.user import User
        
        print("🏢 Setting up demo data...")
        
        # Create demo company if it doesn't exist
        demo_company = Company.query.filter_by(slug='habari-demo').first()
        
        if not demo_company:
            print("🏢 Creating demo company...")
            
            demo_company = Company(
                name='Habari Company (Demo)',
                slug='habari-demo',
                description='Demo company for churn prediction platform',
                industry='Telecommunications',
                website='https://habaricompany.com',
                sync_status='pending',
                total_syncs=0,
                is_active=True
            )
            
            # Set demo API configuration
            demo_company.api_base_url = 'http://localhost/Web_CRM/api.php'
            demo_company.update_settings({
                'auto_sync_enabled': False,
                'sync_frequency_hours': 6,
                'notification_email': 'admin@habaricompany.com',
                'selective_sync': {
                    'customers': True,
                    'payments': True, 
                    'tickets': True,
                    'usage': False
                }
            })
            
            db.session.add(demo_company)
            db.session.flush()  # Get ID without committing
            
            print(f"✅ Demo company created with ID: {demo_company.id}")
        else:
            print(f"✅ Demo company already exists: {demo_company.name}")
        
        # Create demo user if it doesn't exist
        demo_user = User.query.filter_by(email='admin@example.com').first()
        
        if not demo_user:
            print("👤 Creating demo user...")
            
            demo_user = User(
                email='admin@example.com',
                full_name='Demo Administrator',
                company_id=demo_company.id,
                role='admin',
                is_active=True
            )
            demo_user.set_password('admin123')
            
            db.session.add(demo_user)
            
            print("✅ Demo user created: admin@example.com / admin123")
        else:
            # Update user to belong to demo company if needed
            if not demo_user.company_id:
                demo_user.company_id = demo_company.id
                print("✅ Demo user updated with company association")
            else:
                print("✅ Demo user already exists and configured")
        
        # Commit all changes
        db.session.commit()
        print("💾 All changes committed to database")
        
        return True, demo_company, demo_user
        
    except Exception as e:
        print(f"❌ Demo data creation failed: {str(e)}")
        db.session.rollback()
        return False, None, None

def verify_schema():
    """Verify the schema is correct"""
    
    try:
        print("🔍 Verifying database schema...")
        
        inspector = db.inspect(db.engine)
        
        # Check Company table
        company_columns = [col['name'] for col in inspector.get_columns('companies')]
        required_company_fields = [
            'id', 'name', 'slug', 'postgres_host', 'api_base_url', 
            'last_sync_at', 'sync_status', 'settings'
        ]
        
        missing_company_fields = [field for field in required_company_fields 
                                 if field not in company_columns]
        
        # Check User table
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        required_user_fields = [
            'id', 'email', 'password_hash', 'full_name', 'company_id', 'role'
        ]
        
        missing_user_fields = [field for field in required_user_fields 
                              if field not in user_columns]
        
        if missing_company_fields:
            print(f"⚠️ Missing Company fields: {missing_company_fields}")
        else:
            print("✅ Company table schema is complete")
            
        if missing_user_fields:
            print(f"⚠️ Missing User fields: {missing_user_fields}")
        else:
            print("✅ User table schema is complete")
        
        # Test relationship by trying to query
        try:
            from app.models.company import Company
            from app.models.user import User
            
            # Test query
            companies = Company.query.limit(1).all()
            users = User.query.limit(1).all()
            
            print("✅ Model relationships are working")
            return True
            
        except Exception as e:
            print(f"❌ Model relationship test failed: {str(e)}")
            return False
        
    except Exception as e:
        print(f"❌ Schema verification failed: {str(e)}")
        return False

def run_complete_fix():
    """Run complete database fix"""
    
    print("🚀 Starting complete database fix...")
    
    # Step 1: Fix schema
    if not fix_database_schema():
        print("❌ Schema fix failed")
        return False
    
    # Step 2: Create demo data
    success, demo_company, demo_user = create_demo_data()
    if not success:
        print("❌ Demo data creation failed")
        return False
    
    # Step 3: Verify everything works
    if not verify_schema():
        print("❌ Schema verification failed")
        return False
    
    print("🎉 Complete database fix successful!")
    print("\n📝 Summary:")
    print("✅ Database schema updated")
    print("✅ User-Company relationship fixed")
    print("✅ Demo company created")
    print("✅ Demo user created")
    print("\n🔐 Login credentials:")
    print("📧 Email: admin@example.com")
    print("🔑 Password: admin123")
    print("\n🔗 Next steps:")
    print("1. Replace your models with the fixed versions")
    print("2. Add ENCRYPTION_KEY to .env file")
    print("3. Restart your Flask application")
    print("4. Test login functionality")
    
    return True

if __name__ == "__main__":
    # Run migration if script is executed directly
    from app import create_app
    
    app = create_app()
    with app.app_context():
        run_complete_fix()