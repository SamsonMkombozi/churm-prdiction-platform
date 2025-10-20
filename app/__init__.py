"""
Fixed Flask Application Factory - app/__init__.py
With proper authentication flow and churn prediction integration
"""
from flask import Flask, render_template, redirect, url_for, g
from flask_login import current_user
import logging
import os

# Import extensions from separate file to avoid circular imports
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_name='development'):
    """Create Flask application factory"""

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # app/
    ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))  # project root

    app = Flask(
        __name__,
        template_folder=os.path.join(ROOT_DIR, 'templates'),
        static_folder=os.path.join(ROOT_DIR, 'static')
)

    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///churn_prediction.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.models.user import User
            return User.query.get(int(user_id))
        except:
            return None
    
    # Register components
    register_blueprints(app)
    register_error_handlers(app)
    
    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    return app

def register_blueprints(app):
    """Register all blueprints with error handling"""
    
    # 1. Auth Controller (REQUIRED)
    try:
        from app.controllers.auth_controller import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.logger.info("✅ Auth blueprint registered")
    except Exception as e:
        app.logger.error(f"❌ Auth blueprint failed: {e}")
    
    # 2. Dashboard Controller
    try:
        from app.controllers.dashboard_controller import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.logger.info("✅ Dashboard blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Dashboard blueprint not registered: {e}")
    
    # 3. Company Controller
    try:
        from app.controllers.company_controller import company_bp
        app.register_blueprint(company_bp, url_prefix='/company')
        app.logger.info("✅ Company blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Company blueprint not registered: {e}")
    
    # 4. CRM Controller
    try:
        from app.controllers.crm_controller import crm_bp
        app.register_blueprint(crm_bp, url_prefix='/crm')
        app.logger.info("✅ CRM blueprint registered")
    except Exception as e:
        app.logger.warning(f"⚠️ CRM blueprint not registered: {e}")

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except:
            pass
        return render_template('errors/500.html'), 500
