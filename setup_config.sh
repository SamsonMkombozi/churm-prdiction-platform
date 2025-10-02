#!/bin/bash

# ================================================================
# Quick Configuration Setup Script
# Run this script to set up all configuration files
# ================================================================

echo "🚀 Setting up configuration files..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p app/config
mkdir -p logs
mkdir -p uploads

# Generate secret keys
echo "🔐 Generating secret keys..."

# Generate Flask SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Generate ENCRYPTION_KEY
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create .env file from .env.example
echo "📝 Creating .env file..."

cat > .env << EOL
# ================================================================
# ENVIRONMENT CONFIGURATION
# Auto-generated on $(date)
# ================================================================

# Application Settings
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=${SECRET_KEY}
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Database Configuration
DATABASE_URL=sqlite:///churn_platform.db

# Redis Configuration (Optional - comment out if not using)
# REDIS_URL=redis://localhost:6379/0

# Celery Configuration (Optional - comment out if not using)
# CELERY_BROKER_URL=redis://localhost:6379/1
# CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_ALWAYS_EAGER=True

# Habari CRM API Configuration
HABARI_CRM_BASE_URL=https://palegreen-porpoise-596991.hostingersite.com/Web_CRM/api.php
HABARI_API_TIMEOUT=30
CRM_SYNC_INTERVAL=3600

# ML Model Configuration
ML_MODEL_PATH=app/ml/pretrained
MODEL_VERSION=v1.0
PREDICTION_BATCH_SIZE=1000
PREDICTION_THRESHOLD_HIGH=0.7
PREDICTION_THRESHOLD_MEDIUM=0.4

# Email Configuration (Optional - configure when needed)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-specific-password
# MAIL_DEFAULT_SENDER=noreply@churnprediction.com

# Security Settings
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600
WTF_CSRF_ENABLED=True

# Encryption Key
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# API Rate Limiting
RATELIMIT_ENABLED=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Feature Flags
ENABLE_EMAIL_NOTIFICATIONS=False
ENABLE_BACKGROUND_SYNC=True
ENABLE_API_ACCESS=True
ENABLE_REGISTRATION=True

# Pagination
ITEMS_PER_PAGE=50
MAX_ITEMS_PER_PAGE=200

# Cache Settings
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Timezone
TIMEZONE=UTC
EOL

echo -e "${GREEN}✅ .env file created!${NC}"

# Create __init__.py for config package
echo "📝 Creating app/config/__init__.py..."

cat > app/config/__init__.py << 'EOL'
"""
Configuration Package
"""

from .settings import config, get_config, DevelopmentConfig, ProductionConfig, TestingConfig
from .database import DatabaseConfig, DatabaseHealthCheck, init_database

__all__ = [
    'config',
    'get_config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'DatabaseConfig',
    'DatabaseHealthCheck',
    'init_database'
]
EOL

echo -e "${GREEN}✅ app/config/__init__.py created!${NC}"

# Create a simple test script
echo "📝 Creating test_config.py..."

cat > test_config.py << 'EOL'
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
EOL

echo -e "${GREEN}✅ test_config.py created!${NC}"

# Summary
echo ""
echo "="*60
echo -e "${GREEN}✅ Configuration setup complete!${NC}"
echo "="*60
echo ""
echo "📋 What was created:"
echo "   1. .env file with auto-generated secrets"
echo "   2. app/config/__init__.py"
echo "   3. test_config.py for verification"
echo ""
echo "🔍 Next steps:"
echo "   1. Copy the code from artifacts for:"
echo "      - app/config/settings.py"
echo "      - app/config/database.py"
echo "   2. Run: python test_config.py"
echo "   3. Verify all checks pass ✅"
echo ""
echo "📝 Important:"
echo "   - Your SECRET_KEY and ENCRYPTION_KEY are in .env"
echo "   - Never commit .env to git!"
echo "   - Keep these keys secure!"
echo ""
echo "="*60

# Make the script executable
chmod +x "$0"

echo -e "${YELLOW}💡 Tip: Run 'python test_config.py' to verify everything is set up correctly${NC}"