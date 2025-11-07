"""
Fixed Flask Application Factory
"""
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
import logging
import os

def create_app(config_name='development'):
    """Create Flask application with proper initialization"""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # /app
    ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))  # project root

    app = Flask(
        __name__,
        template_folder=os.path.join(ROOT_DIR, 'templates'),
        static_folder=os.path.join(ROOT_DIR, 'static')
    )
    # Load configuration
    from app.config.settings import get_config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    from app.extensions import db, migrate, login_manager, csrf
    
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
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.company_controller import company_bp
    from app.controllers.crm_controller import crm_bp
    from app.controllers.prediction_controller import prediction_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(prediction_bp, url_prefix='/prediction')
    
    # Root route - redirect to appropriate page
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500
    
    # Template filters
    from app.utils.template_filters import register_filters
    register_filters(app)
    
    
    # Add hasattr to Jinja2 templates
    app.jinja_env.globals['hasattr'] = hasattr
    
    return app
