"""
Flask Application Factory
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager

# Import extensions
from app.extensions import db, migrate, login_manager
from app.config import get_config


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register middleware
    register_middleware(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Template and static folder info
    logging.info(f"📁 Template folder: {app.template_folder}")
    logging.info(f"📁 Static folder: {app.static_folder}")
    
    return app


def register_middleware(app):
    """Register application middleware"""
    from app.middleware.tenant_middleware import tenant_middleware
    
    # Register tenant middleware
    app.before_request(tenant_middleware)


def register_blueprints(app):
    """Register application blueprints"""
    # Authentication routes
    from app.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Dashboard routes
    from app.controllers.dashboard_controller import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/')
    
    # Company management routes
    from app.controllers.company_controller import company_bp
    app.register_blueprint(company_bp, url_prefix='/company')
    
    # CRM routes
    from app.controllers.crm_controller import crm_bp
    app.register_blueprint(crm_bp, url_prefix='/crm')
    
    # Prediction routes - ✅ FIXED: Only import if file exists and is working
    try:
        from app.controllers.prediction_controller import prediction_bp
        app.register_blueprint(prediction_bp, url_prefix='/prediction')
        logging.info("✅ Prediction controller registered successfully")
    except ImportError as e:
        logging.warning(f"⚠️  Prediction controller not available: {e}")
        # Create a placeholder route
        from flask import Blueprint, render_template
        prediction_bp = Blueprint('prediction', __name__)
        
        @prediction_bp.route('/dashboard')
        def dashboard():
            return render_template('prediction/placeholder.html')
        
        app.register_blueprint(prediction_bp, url_prefix='/prediction')


def register_template_filters(app):
    """Register custom template filters"""
    try:
        from app.utils.template_filters import register_filters
        register_filters(app)
    except ImportError:
        # Basic filters if utils not available
        @app.template_filter('number')
        def number_filter(value):
            try:
                return "{:,}".format(int(value))
            except (ValueError, TypeError):
                return value
        
        @app.template_filter('currency')
        def currency_filter(value, symbol='$'):
            try:
                return f"{symbol}{float(value):,.2f}"
            except (ValueError, TypeError):
                return value


def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500


def create_database_tables(app):
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)