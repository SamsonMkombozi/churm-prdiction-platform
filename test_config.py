"""
Test configuration setup
Run this to verify your configuration is working
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_config():
    """Test configuration loading"""
    
    print("="*60)
    print("CONFIGURATION TEST")
    print("="*60)
    
    # Check critical environment variables
    checks = {
        'FLASK_APP': os.getenv('FLASK_APP'),
        'FLASK_ENV': os.getenv('FLASK_ENV'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'HABARI_CRM_BASE_URL': os.getenv('HABARI_CRM_BASE_URL'),
        'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY'),
    }
    
    all_pass = True
    
    for key, value in checks.items():
        if value:
            # Don't print full secret keys
            if 'KEY' in key:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {key}: {display_value}")
        else:
            print(f"❌ {key}: NOT SET")
            all_pass = False
    
    print("\n" + "="*60)
    
    if all_pass:
        print("✅ All critical environment variables are set!")
        
        # Try to import config
        try:
            from app.config import get_config
            config = get_config('development')
            print(f"✅ Configuration loaded successfully!")
            print(f"   - Debug mode: {config.DEBUG}")
            print(f"   - Database: {config.SQLALCHEMY_DATABASE_URI}")
            print(f"   - ML Model Path: {config.ML_MODEL_PATH}")
            return True
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False
    else:
        print("❌ Some environment variables are missing!")
        return False

if __name__ == '__main__':
    success = test_config()
    exit(0 if success else 1)
