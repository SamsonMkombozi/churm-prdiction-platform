#!/usr/bin/env python3
"""
Fixed PostgreSQL Configuration Debug Script

This script handles the import issues and checks your PostgreSQL configuration.
"""

import os
import sys

def setup_environment():
    """Setup the environment to work from current directory"""
    
    # Go to home directory where the project should be
    os.chdir('/home/claude')
    
    # Check if project exists
    project_paths = [
        'churn-prediction-platform',
        '/var/www/html/churn-prediction-platform',
        '/home/mkombozi/churn-prediction-platform'  # Common user location
    ]
    
    project_path = None
    for path in project_paths:
        if os.path.exists(path):
            project_path = path
            break
    
    if not project_path:
        print("❌ Could not find churn-prediction-platform directory")
        print("Please run this script from your project directory")
        return None
    
    print(f"📁 Found project at: {project_path}")
    os.chdir(project_path)
    
    # Add to Python path
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
    
    return project_path

def check_models_structure():
    """Check if models are properly structured"""
    
    print("\n🔍 Checking Models Structure...")
    print("-" * 40)
    
    # Check if models directory exists
    if not os.path.exists('app/models'):
        print("❌ app/models directory doesn't exist")
        return False
    
    # Check for __init__.py
    if not os.path.exists('app/models/__init__.py'):
        print("❌ app/models/__init__.py doesn't exist")
        return False
    
    # Check for individual model files
    model_files = ['company.py', 'customer.py', 'payment.py', 'ticket.py', 'user.py']
    missing_files = []
    
    for model_file in model_files:
        if os.path.exists(f'app/models/{model_file}'):
            print(f"   ✅ {model_file}")
        else:
            print(f"   ❌ {model_file} - MISSING!")
            missing_files.append(model_file)
    
    # Check __init__.py imports
    try:
        with open('app/models/__init__.py', 'r') as f:
            init_content = f.read()
            
        print(f"\n📋 Current __init__.py content:")
        print(init_content)
        
        # Check for proper imports
        required_imports = ['Company', 'Customer', 'Payment', 'Ticket', 'User']
        missing_imports = []
        
        for imp in required_imports:
            if imp not in init_content:
                missing_imports.append(imp)
        
        if missing_imports:
            print(f"\n⚠️  Missing imports in __init__.py: {missing_imports}")
            return False
        else:
            print(f"\n✅ All required imports present in __init__.py")
            return True
            
    except Exception as e:
        print(f"❌ Error reading __init__.py: {str(e)}")
        return False

def fix_models_init():
    """Fix the models __init__.py file"""
    
    print("\n🔧 Fixing models/__init__.py...")
    
    # Create proper __init__.py content
    init_content = '''"""
Models package initialization
"""

from .company import Company
from .user import User

# Import CRM models if they exist
try:
    from .customer import Customer
except ImportError:
    Customer = None

try:
    from .payment import Payment
except ImportError:
    Payment = None

try:
    from .ticket import Ticket
except ImportError:
    Ticket = None

# Export all models
__all__ = ['Company', 'User', 'Customer', 'Payment', 'Ticket']
'''
    
    try:
        os.makedirs('app/models', exist_ok=True)
        
        with open('app/models/__init__.py', 'w') as f:
            f.write(init_content)
        
        print("   ✅ Fixed models/__init__.py")
        return True
    except Exception as e:
        print(f"   ❌ Error fixing __init__.py: {str(e)}")
        return False

def create_missing_models():
    """Create minimal versions of missing model files"""
    
    print("\n🏗️  Creating missing model files...")
    
    # Customer model
    customer_model = '''"""
Customer model for CRM functionality
"""

from app.extensions import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False)  # External CRM ID
    customer_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    monthly_charges = db.Column(db.Float, default=0.0)
    contract_start_date = db.Column(db.DateTime)
    contract_end_date = db.Column(db.DateTime)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('customers', lazy=True))
    payments = db.relationship('Payment', backref='customer', lazy=True)
    tickets = db.relationship('Ticket', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.customer_name}>'
'''

    # Payment model
    payment_model = '''"""
Payment model for CRM functionality
"""

from app.extensions import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_reference = db.Column(db.String(100), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)  # Store tx_amount here
    transaction_time = db.Column(db.DateTime, nullable=False)
    phone_number = db.Column(db.String(20))
    payer_name = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, completed, refunded
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('payments', lazy=True))
    
    def __repr__(self):
        return f'<Payment {self.transaction_reference}: {self.amount}>'
'''

    # Ticket model
    ticket_model = '''"""
Ticket model for CRM functionality
"""

from app.extensions import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), nullable=False)  # External CRM ID
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('tickets', lazy=True))
    
    def __repr__(self):
        return f'<Ticket {self.ticket_id}: {self.subject}>'
'''

    models_to_create = [
        ('customer.py', customer_model),
        ('payment.py', payment_model),
        ('ticket.py', ticket_model)
    ]
    
    for filename, content in models_to_create:
        filepath = f'app/models/{filename}'
        if not os.path.exists(filepath):
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"   ✅ Created {filename}")
            except Exception as e:
                print(f"   ❌ Error creating {filename}: {str(e)}")
        else:
            print(f"   ⚠️  {filename} already exists, skipping")

def debug_postgresql_config():
    """Debug PostgreSQL configuration"""
    
    try:
        # Import Flask app
        from app import create_app
        from app.models.company import Company
        
        app = create_app()
        
        with app.app_context():
            print("\n🔍 PostgreSQL Configuration Debug Report")
            print("=" * 50)
            
            # Get all companies
            companies = Company.query.all()
            
            if not companies:
                print("❌ No companies found in database!")
                return
            
            for company in companies:
                print(f"\n🏢 Company: {company.name} (ID: {company.id})")
                print("-" * 40)
                
                # Check PostgreSQL configuration
                print("📋 Configuration Status:")
                
                # Check if company has PostgreSQL settings
                has_postgres_host = hasattr(company, 'postgres_host') and company.postgres_host
                has_postgres_db = hasattr(company, 'postgres_database') and company.postgres_database
                has_postgres_user = hasattr(company, 'postgres_username') and company.postgres_username
                
                print(f"   PostgreSQL Host: {getattr(company, 'postgres_host', 'NOT SET')}")
                print(f"   PostgreSQL Database: {getattr(company, 'postgres_database', 'NOT SET')}")
                print(f"   PostgreSQL Username: {getattr(company, 'postgres_username', 'NOT SET')}")
                print(f"   PostgreSQL Password: {'SET' if getattr(company, 'postgres_password', None) else 'NOT SET'}")
                print(f"   PostgreSQL Port: {getattr(company, 'postgres_port', 'NOT SET')}")
                
                # Check API configuration
                has_api_token = hasattr(company, 'api_token') and company.api_token
                has_api_base_url = hasattr(company, 'api_base_url') and company.api_base_url
                
                print(f"   API Token: {'SET' if has_api_token else 'NOT SET'}")
                print(f"   API Base URL: {getattr(company, 'api_base_url', 'NOT SET')}")
                
                # Determine configuration status
                postgresql_configured = (
                    has_postgres_host and 
                    has_postgres_db and 
                    has_postgres_user and 
                    getattr(company, 'postgres_password', None)
                )
                
                api_configured = has_api_token and has_api_base_url
                
                print(f"\n🔧 Detection Results:")
                print(f"   PostgreSQL Configured: {'✅ YES' if postgresql_configured else '❌ NO'}")
                print(f"   API Configured: {'✅ YES' if api_configured else '❌ NO'}")
                
                if postgresql_configured:
                    print(f"   Preferred Method: PostgreSQL (Fast)")
                    
                    # Test PostgreSQL connection if configured
                    print(f"\n🧪 Testing PostgreSQL Connection...")
                    try:
                        import psycopg2
                        conn_string = f"host='{company.postgres_host}' port='{company.postgres_port}' dbname='{company.postgres_database}' user='{company.postgres_username}' password='{company.postgres_password}'"
                        
                        with psycopg2.connect(conn_string) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT version();")
                                version = cursor.fetchone()[0]
                                print(f"   ✅ Connection successful!")
                                print(f"   📊 Database version: {version[:50]}...")
                                
                    except Exception as e:
                        print(f"   ❌ Connection failed: {str(e)}")
                
                elif api_configured:
                    print(f"   Preferred Method: API (Fallback)")
                else:
                    print(f"   Preferred Method: None (Not Configured)")
    
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run all checks and fixes"""
    
    print("🚀 PostgreSQL Configuration Fixer & Debugger")
    print("=" * 50)
    
    # Setup environment
    project_path = setup_environment()
    if not project_path:
        return
    
    # Check models structure
    models_ok = check_models_structure()
    
    if not models_ok:
        print("\n🔧 Fixing models structure...")
        
        # Fix models init
        fix_models_init()
        
        # Create missing models
        create_missing_models()
        
        print("\n✅ Models structure fixed!")
    
    # Now try to debug PostgreSQL config
    try:
        debug_postgresql_config()
    except Exception as e:
        print(f"\n❌ Could not complete PostgreSQL debug: {str(e)}")
        print("\n💡 Suggested fixes:")
        print("   1. Run: flask db migrate -m 'Add PostgreSQL fields'")
        print("   2. Run: flask db upgrade")
        print("   3. Restart Flask application")
        print("   4. Run this script again")

if __name__ == "__main__":
    main()