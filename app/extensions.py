"""
Simple Flask Extensions File
app/extensions.py

Minimal extensions needed for the app to work
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Create a dummy csrf object to prevent import errors
class DummyCSRF:
    def init_app(self, app):
        pass

csrf = DummyCSRF()