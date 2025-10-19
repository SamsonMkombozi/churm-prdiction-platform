"""
Minimal Working Flask App for ML Testing
app/__init__.py

Focus: Get the prediction endpoint working
"""
from flask import Flask, render_template
import os
import logging

# Simple extensions
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='development'):
    """Create minimal Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///churn_prediction.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    
    # Log template and static folders
    app.logger.info(f"📁 Template folder: {app.template_folder}")
    app.logger.info(f"📁 Static folder: {app.static_folder}")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    # login_manager.login_view = 'auth.login'  # Disabled for testing
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # CRITICAL: Add user loader function
    @login_manager.user_loader
    def load_user(user_id):
        # For now, return None (anonymous user)
        # This prevents the Flask-Login error
        return None
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info("📊 Database tables created/verified")
    
    return app


def register_blueprints(app):
    """Register all blueprints with error handling"""
    
    # 1. Prediction Controller (MOST IMPORTANT FOR ML)
    try:
        from app.controllers.prediction_controller import prediction_bp
        app.register_blueprint(prediction_bp, url_prefix='/prediction')
        app.logger.info("✅ Prediction blueprint registered")
    except Exception as e:
        app.logger.error(f"❌ Failed to register prediction blueprint: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Auth Controller
    try:
        from app.controllers.auth_controller import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.logger.info("✅ Auth blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Auth blueprint not registered: {e}")
    
    # 3. Company Controller
    try:
        from app.controllers.company_controller import company_bp
        app.register_blueprint(company_bp, url_prefix='/company')
        app.logger.info("✅ Company blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Company blueprint not registered: {e}")
    
    # 4. Dashboard Controller
    try:
        from app.controllers.dashboard_controller import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/')
        app.logger.info("✅ Dashboard blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Dashboard blueprint not registered: {e}")
    
    # 5. CRM Controller
    try:
        from app.controllers.crm_controller import crm_bp
        app.register_blueprint(crm_bp, url_prefix='/crm')
        app.logger.info("✅ CRM blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ CRM blueprint not registered: {e}")


def register_error_handlers(app):
    """Register basic error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    # Simple test route
    @app.route('/test')
    def test_route():
        return {'status': 'ok', 'message': 'Flask app is working!'}
    
    # Health check route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'ml_available': True}