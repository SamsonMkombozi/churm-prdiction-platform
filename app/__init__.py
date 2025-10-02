"""
Flask Application Factory
"""
from flask import Flask
from app.config.settings import get_config
from app.extensions import init_extensions, db, login_manager
from app.models.user import User
from app.models.company import Company
# Import other models as you create them
# from app.models.customer import Customer
# from app.models.ticket import Ticket
# from app.models.payment import Payment

__all__ = ['User', 'Company']

def create_app(config_name='development'):
    """
    Application factory pattern
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Import models here (after db is initialized)
    with app.app_context():
        from app.models import user, company
        
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

def register_blueprints(app):
    """Register all blueprints"""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.company_controller import company_bp
    from app.controllers.dashboard_controller import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(dashboard_bp, url_prefix='/')

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