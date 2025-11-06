"""
Updated Company Model with Sync Fields
app/models/company.py

Complete Company model with all sync-related fields and methods.
"""

from app.extensions import db
from datetime import datetime
from cryptography.fernet import Fernet
import os
import json

class Company(db.Model):
    """Company model with sync capabilities"""
    
    __tablename__ = 'company'
    
    # Basic company fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # Subscription and status
    subscription_plan = db.Column(db.String(50), default='basic')
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Sync-related fields
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='never')  # never, pending, in_progress, completed, failed
    sync_error = db.Column(db.Text)
    total_syncs = db.Column(db.Integer, default=0)
    
    # PostgreSQL connection fields
    postgresql_host = db.Column(db.String(255))
    postgresql_port = db.Column(db.Integer, default=5432)
    postgresql_database = db.Column(db.String(255))
    postgresql_username = db.Column(db.String(255))
    postgresql_password_encrypted = db.Column(db.Text)
    
    # API connection fields
    api_base_url = db.Column(db.String(255))
    api_key_encrypted = db.Column(db.Text)
    
    # Additional sync settings (JSON field)
    sync_settings = db.Column(db.JSON)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True, 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    # Encryption/Decryption methods
    def _get_encryption_key(self):
        """Get encryption key from environment"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate a key if not set (for development)
            key = Fernet.generate_key()
            print(f"⚠️  Generated new encryption key: {key.decode()}")
            print("⚠️  Set ENCRYPTION_KEY environment variable for production!")
        return key if isinstance(key, bytes) else key.encode()
    
    def encrypt_password(self, password):
        """Encrypt PostgreSQL password"""
        if not password:
            return None
        f = Fernet(self._get_encryption_key())
        return f.encrypt(password.encode()).decode()
    
    def decrypt_password(self):
        """Decrypt PostgreSQL password"""
        if not self.postgresql_password_encrypted:
            return None
        try:
            f = Fernet(self._get_encryption_key())
            return f.decrypt(self.postgresql_password_encrypted.encode()).decode()
        except Exception:
            return None
    
    def encrypt_api_key(self, api_key):
        """Encrypt API key"""
        if not api_key:
            return None
        f = Fernet(self._get_encryption_key())
        return f.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self):
        """Decrypt API key"""
        if not self.api_key_encrypted:
            return None
        try:
            f = Fernet(self._get_encryption_key())
            return f.decrypt(self.api_key_encrypted.encode()).decode()
        except Exception:
            return None
    
    # Sync status methods
    def mark_sync_started(self):
        """Mark that sync has started"""
        self.sync_status = 'in_progress'
        self.sync_error = None
        db.session.commit()
    
    def mark_sync_completed(self):
        """Mark that sync completed successfully"""
        self.last_sync_at = datetime.utcnow()
        self.sync_status = 'completed'
        self.sync_error = None
        self.total_syncs = (self.total_syncs or 0) + 1
        db.session.commit()
    
    def mark_sync_failed(self, error_message):
        """Mark that sync failed"""
        self.sync_status = 'failed'
        self.sync_error = error_message
        db.session.commit()
    
    def update_sync_status(self, status, error=None, commit=True):
        """Update sync status"""
        self.sync_status = status
        
        if status == 'completed':
            self.last_sync_at = datetime.utcnow()
            self.total_syncs = (self.total_syncs or 0) + 1
            self.sync_error = None
        elif status == 'failed' and error:
            self.sync_error = str(error)
        elif status == 'pending':
            self.sync_error = None  # Clear error on reset
        
        if commit:
            db.session.commit()
    
    # Statistics methods
    def get_customer_count(self):
        """Get total number of customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            return 0
    
    def get_active_customer_count(self):
        """Get count of active customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(
                company_id=self.id,
                status='active'
            ).count()
        except (ImportError, ModuleNotFoundError, AttributeError):
            return 0
    
    def get_ticket_count(self):
        """Get total number of tickets for this company"""
        try:
            from app.models.ticket import Ticket
            return Ticket.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            return 0
    
    def get_payment_count(self):
        """Get total number of payments for this company"""
        try:
            from app.models.payment import Payment
            return Payment.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            return 0
    
    def get_prediction_count(self):
        """Get total number of predictions for this company"""
        try:
            from app.models.prediction import Prediction
            return Prediction.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            return 0
    
    def get_high_risk_customer_count(self):
        """Get count of high-risk customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(
                company_id=self.id,
                churn_risk='high'
            ).count()
        except (ImportError, ModuleNotFoundError, AttributeError):
            return 0
    
    def get_active_user_count(self):
        """Get count of active users in this company"""
        return self.users.filter_by(is_active=True).count()
    
    # Connection configuration methods
    def has_postgresql_config(self):
        """Check if PostgreSQL connection is configured"""
        return bool(
            self.postgresql_host and 
            self.postgresql_database and 
            self.postgresql_username and 
            self.postgresql_password_encrypted
        )
    
    def has_api_config(self):
        """Check if API connection is configured"""
        return bool(self.api_base_url and self.api_key_encrypted)
    
    def get_preferred_sync_method(self):
        """Get preferred sync method"""
        if self.has_postgresql_config():
            return 'postgresql'
        elif self.has_api_config():
            return 'api'
        else:
            return 'none'
    
    # Sync settings methods
    def get_sync_settings(self):
        """Get sync settings as dict"""
        if self.sync_settings:
            return self.sync_settings
        return {
            'sync_customers': True,
            'sync_payments': True,
            'sync_tickets': True,
            'sync_usage': False,
            'batch_size': 1000,
            'sync_frequency': 'manual'
        }
    
    def update_sync_settings(self, settings):
        """Update sync settings"""
        current_settings = self.get_sync_settings()
        current_settings.update(settings)
        self.sync_settings = current_settings
        db.session.commit()
    
    # Serialization
    def to_dict(self, include_sensitive=False):
        """Convert company to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'logo_url': self.logo_url,
            'industry': self.industry,
            'website': self.website,
            'subscription_plan': self.subscription_plan,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'total_syncs': self.total_syncs,
            'statistics': {
                'total_customers': self.get_customer_count(),
                'active_customers': self.get_active_customer_count(),
                'total_tickets': self.get_ticket_count(),
                'total_payments': self.get_payment_count(),
                'total_predictions': self.get_prediction_count(),
                'high_risk_customers': self.get_high_risk_customer_count(),
                'active_users': self.get_active_user_count()
            }
        }
        
        if include_sensitive:
            data.update({
                'postgresql_host': self.postgresql_host,
                'postgresql_port': self.postgresql_port,
                'postgresql_database': self.postgresql_database,
                'postgresql_username': self.postgresql_username,
                'api_base_url': self.api_base_url,
                'sync_settings': self.get_sync_settings()
            })
        
        return data
    
    @staticmethod
    def create_company(name, slug=None, **kwargs):
        """Create a new company with default settings"""
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
        
        company = Company(
            name=name,
            slug=slug,
            sync_status='never',
            total_syncs=0,
            **kwargs
        )
        
        db.session.add(company)
        db.session.commit()
        
        return company