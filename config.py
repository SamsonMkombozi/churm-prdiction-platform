# config.py - Main Configuration File
import os
from datetime import timedelta

# Get the absolute path to the project root
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - Use absolute path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "instance", "churn_platform.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Redis (optional)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # ML Model Settings
    ML_MODEL_PATH = 'app/ml/models/saved/'
    ML_FEATURES_PATH = 'app/ml/features/'
    
    # Logging
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name='default'):
    """Get configuration by name"""
    return config.get(config_name, DevelopmentConfig)