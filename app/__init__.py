"""
Flask Application Factory
"""
import os
from flask import Flask
from app.config.settings import get_config
from app.extensions import init_extensions, db, login_manager

def create_app(config_name='development'):
    """
    Application factory pattern
    """
    # IMPORTANT: Set template_folder to project root templates directory
    # Get the project root (one level up from app/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Log template path for debugging
    app.logger.info(f"📁 Template folder: {app.template_folder}")
    app.logger.info(f"📁 Static folder: {app.static_folder}")
    
    # Initialize extensions
    init_extensions(app)
    
    # Register custom template filters
    register_template_filters(app)
    
    # Import models here (after db is initialized)
    with app.app_context():
        # Import all models
        from app.models import user, company
        # Phase 4 models
        from app.models import customer, ticket, payment
        
        # Create tables
        db.create_all()
    
    # Register user loader for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    register_blueprints(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_template_filters(app):
    """Register custom Jinja2 template filters"""
    from app.utils.template_filters import register_filters
    register_filters(app)

def register_blueprints(app):
    """Register all blueprints"""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.company_controller import company_bp
    from app.controllers.dashboard_controller import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.logger.info('✅ Auth blueprint registered')
    
    app.register_blueprint(company_bp, url_prefix='/company')
    app.logger.info('✅ Company blueprint registered')
    
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.logger.info('✅ Dashboard blueprint registered')

def register_middleware(app):
    """Register middleware"""
    from app.middleware.tenant_middleware import tenant_middleware
    
    app.before_request(tenant_middleware)

def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403