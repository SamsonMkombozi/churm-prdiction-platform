"""
Temporary Company Model - Compatible with existing database
Replace app/models/company.py with this version temporarily

This version only includes columns that exist in your current database
"""

from app.extensions import db
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class Company(db.Model):
    """Company model compatible with existing database schema"""
    
    __tablename__ = 'companies'
    
    # Basic company fields (these should exist)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Sync-related fields (these might exist)
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='never')
    sync_error = db.Column(db.Text)
    total_syncs = db.Column(db.Integer, default=0)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True, 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    # Safe property getters (return None if column doesn't exist)
    @property
    def logo_url(self):
        return getattr(self, '_logo_url', None)
    
    @property
    def postgresql_host(self):
        return getattr(self, '_postgresql_host', None)
    
    @property
    def postgresql_port(self):
        return getattr(self, '_postgresql_port', 5432)
    
    @property
    def postgresql_database(self):
        return getattr(self, '_postgresql_database', None)
    
    @property
    def postgresql_username(self):
        return getattr(self, '_postgresql_username', None)
    
    @property
    def postgresql_password_encrypted(self):
        return getattr(self, '_postgresql_password_encrypted', None)
    
    @property
    def api_base_url(self):
        return getattr(self, '_api_base_url', None)
    
    @property
    def api_key_encrypted(self):
        return getattr(self, '_api_key_encrypted', None)
    
    @property
    def api_username(self):
        return getattr(self, '_api_username', None)
    
    @property
    def api_password_encrypted(self):
        return getattr(self, '_api_password_encrypted', None)
    
    @property
    def settings(self):
        return getattr(self, '_settings', '{}')
    
    # Safe setters
    def set_postgresql_password(self, password):
        """Placeholder - implement after schema fix"""
        logger.warning("PostgreSQL password setting not available - schema needs update")
        return
    
    def get_postgresql_password(self):
        """Placeholder - implement after schema fix"""
        return None
    
    def set_api_key(self, api_key):
        """Placeholder - implement after schema fix"""
        logger.warning("API key setting not available - schema needs update")
        return
    
    def get_api_key(self):
        """Placeholder - implement after schema fix"""
        return None
    
    def set_api_password(self, password):
        """Placeholder - implement after schema fix"""
        logger.warning("API password setting not available - schema needs update")
        return
    
    def get_api_password(self):
        """Placeholder - implement after schema fix"""
        return None
    
    # Connection configuration methods
    def has_postgresql_config(self):
        """Check if PostgreSQL connection is configured"""
        return False  # Always false until schema is fixed
    
    def has_api_config(self):
        """Check if API connection is configured"""
        return False  # Always false until schema is fixed
    
    def get_preferred_sync_method(self):
        """Get preferred sync method"""
        return 'none'
    
    # Sync status methods
    def mark_sync_started(self):
        """Mark that sync has started"""
        self.sync_status = 'in_progress'
        self.sync_error = None
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    def mark_sync_completed(self):
        """Mark that sync completed successfully"""
        self.last_sync_at = datetime.utcnow()
        self.sync_status = 'completed'
        self.sync_error = None
        self.total_syncs = (self.total_syncs or 0) + 1
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    def mark_sync_failed(self, error_message):
        """Mark that sync failed"""
        self.sync_status = 'failed'
        self.sync_error = error_message
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    # Statistics methods (safe versions)
    def get_customer_count(self):
        """Get total number of customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(company_id=self.id).count()
        except Exception as e:
            logger.error(f"Error getting customer count: {e}")
            return 0
    
    def get_active_customer_count(self):
        """Get count of active customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(
                company_id=self.id,
                status='active'
            ).count()
        except Exception as e:
            logger.error(f"Error getting active customer count: {e}")
            return 0
    
    def get_ticket_count(self):
        """Get total number of tickets"""
        try:
            from app.models.ticket import Ticket
            return Ticket.query.filter_by(company_id=self.id).count()
        except Exception as e:
            logger.error(f"Error getting ticket count: {e}")
            return 0
    
    def get_payment_count(self):
        """Get total number of payments"""
        try:
            from app.models.payment import Payment
            return Payment.query.filter_by(company_id=self.id).count()
        except Exception as e:
            logger.error(f"Error getting payment count: {e}")
            return 0
    
    def get_prediction_count(self):
        """Get total number of predictions"""
        try:
            from app.models.prediction import Prediction
            return Prediction.query.filter_by(company_id=self.id).count()
        except Exception as e:
            logger.error(f"Error getting prediction count: {e}")
            return 0
    
    def get_high_risk_customer_count(self):
        """Get count of high-risk customers"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(
                company_id=self.id,
                churn_risk='high'
            ).count()
        except Exception as e:
            logger.error(f"Error getting high risk customer count: {e}")
            return 0
    
    def get_active_user_count(self):
        """Get count of active users"""
        try:
            return self.users.filter_by(is_active=True).count()
        except Exception as e:
            logger.error(f"Error getting active user count: {e}")
            return 0
    
    # Settings methods (safe versions)
    def get_settings(self):
        """Get company settings as dict"""
        return {
            'enable_auto_sync': True,
            'sync_frequency': 3600,
            'notification_email': '',
            'enable_email_alerts': False,
            'prediction_threshold_high': 0.7,
            'prediction_threshold_medium': 0.4,
            'prediction_threshold_low': 0.2,
            'timezone': 'UTC',
            'currency': 'TZS',
            'date_format': '%Y-%m-%d'
        }
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        settings = self.get_settings()
        return settings.get(key, default)
    
    def update_settings(self, new_settings):
        """Update company settings - placeholder"""
        logger.warning("Settings update not available - schema needs update")
        return
    
    # Dashboard statistics
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        return {
            'customers': {
                'total': self.get_customer_count(),
                'active': self.get_active_customer_count(),
            },
            'tickets': {
                'total': self.get_ticket_count(),
                'open': 0,  # Placeholder
            },
            'payments': {
                'total': self.get_payment_count(),
                'total_revenue': 0.0,  # Placeholder
            },
            'predictions': {
                'total': self.get_prediction_count(),
                'high_risk': self.get_high_risk_customer_count(),
                'medium_risk': 0,  # Placeholder
                'low_risk': 0,  # Placeholder
            },
            'users': {
                'total': self.users.count(),
                'active': self.get_active_user_count(),
            },
            'sync': {
                'status': self.sync_status,
                'last_sync': self.last_sync_at,
                'total_syncs': self.total_syncs,
                'error': self.sync_error,
            }
        }
    
    def to_dict(self, include_sensitive=False):
        """Convert company to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'industry': self.industry,
            'website': self.website,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'total_syncs': self.total_syncs
        }
    
    @staticmethod
    def create_company(name, slug=None, **kwargs):
        """Create a new company"""
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