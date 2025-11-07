"""
FIXED Company Model - Prevents Recursion Issues
app/models/company.py

Replace your Company model with this version to fix the recursion error.
"""

from app.extensions import db
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class Company(db.Model):
    """Company model with safe configuration handling - NO RECURSION"""
    
    __tablename__ = 'companies'
    
    # ✅ Basic company fields (these should always exist)
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
    
    # Sync-related fields
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='never')
    sync_error = db.Column(db.Text)
    total_syncs = db.Column(db.Integer, default=0)
    
    # ✅ OPTIONAL: Configuration columns (may or may not exist)
    # These are defined here but we'll access them safely
    # postgresql_host = db.Column(db.String(255))  # May not exist
    # postgresql_port = db.Column(db.Integer, default=5432)  # May not exist
    # etc.
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True, 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    # ✅ SAFE CONFIGURATION METHODS (NO RECURSION)
    
    def get_config(self, key, default=None):
        """
        SAFE method to get configuration values without recursion
        """
        try:
            # Method 1: Try direct database column access
            if hasattr(self.__class__, key):
                # Check if it's a real column (not a property)
                column = getattr(self.__class__, key)
                if hasattr(column, 'type'):  # It's a SQLAlchemy column
                    value = getattr(self, key, None)
                    if value is not None:
                        return value
            
            # Method 2: Try temporary cache
            if hasattr(self, '_config_cache') and self._config_cache and key in self._config_cache:
                return self._config_cache[key]
            
            # Method 3: Try settings JSON
            settings = self._get_settings_dict_safe()
            if key in settings:
                return settings[key]
            
            return default
            
        except Exception as e:
            logger.warning(f"Error getting config {key}: {e}")
            return default
    
    def set_config(self, key, value):
        """
        SAFE method to set configuration values
        """
        try:
            # Method 1: Try to set as database column
            if hasattr(self.__class__, key):
                column = getattr(self.__class__, key)
                if hasattr(column, 'type'):  # It's a real SQLAlchemy column
                    setattr(self, key, value)
                    return True
            
            # Method 2: Store in temporary cache
            if not hasattr(self, '_config_cache'):
                self._config_cache = {}
            self._config_cache[key] = value
            logger.info(f"Stored {key} in config cache")
            return True
            
        except AttributeError as e:
            # Method 3: Store in temporary cache as fallback
            if not hasattr(self, '_config_cache'):
                self._config_cache = {}
            self._config_cache[key] = value
            logger.warning(f"Stored {key} in config cache due to AttributeError: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting config {key}: {e}")
            return False
    
    def _get_settings_dict_safe(self):
        """Safely get settings dictionary"""
        try:
            # Try to get from settings column
            if hasattr(self, 'settings') and self.settings:
                return json.loads(self.settings)
            
            # Try from cache
            if hasattr(self, '_settings_cache'):
                return self._settings_cache
            
            return {}
            
        except (json.JSONDecodeError, AttributeError):
            return {}
    
    # ✅ POSTGRESQL CONFIGURATION METHODS
    
    def get_postgresql_host(self):
        return self.get_config('postgresql_host')
    
    def set_postgresql_host(self, value):
        return self.set_config('postgresql_host', value)
    
    def get_postgresql_port(self):
        return self.get_config('postgresql_port', 5432)
    
    def set_postgresql_port(self, value):
        return self.set_config('postgresql_port', int(value) if value else 5432)
    
    def get_postgresql_database(self):
        return self.get_config('postgresql_database')
    
    def set_postgresql_database(self, value):
        return self.set_config('postgresql_database', value)
    
    def get_postgresql_username(self):
        return self.get_config('postgresql_username')
    
    def set_postgresql_username(self, value):
        return self.set_config('postgresql_username', value)
    
    def get_postgresql_password(self):
        return self.get_config('postgresql_password')
    
    def set_postgresql_password(self, value):
        return self.set_config('postgresql_password', value)
    
    # ✅ API CONFIGURATION METHODS
    
    def get_api_base_url(self):
        return self.get_config('api_base_url')
    
    def set_api_base_url(self, value):
        return self.set_config('api_base_url', value)
    
    def get_api_username(self):
        return self.get_config('api_username')
    
    def set_api_username(self, value):
        return self.set_config('api_username', value)
    
    def get_api_password(self):
        return self.get_config('api_password')
    
    def set_api_password(self, value):
        return self.set_config('api_password', value)
    
    def get_api_key(self):
        return self.get_config('api_key')
    
    def set_api_key(self, value):
        return self.set_config('api_key', value)
    
    # ✅ CONNECTION STATUS METHODS
    
    def has_postgresql_config(self):
        """Check if PostgreSQL connection is configured"""
        return bool(
            self.get_postgresql_host() and 
            self.get_postgresql_database() and 
            self.get_postgresql_username()
        )
    
    def has_api_config(self):
        """Check if API connection is configured"""
        return bool(self.get_api_base_url())
    
    def get_preferred_sync_method(self):
        """Get preferred sync method"""
        if self.has_postgresql_config():
            return 'postgresql'
        elif self.has_api_config():
            return 'api'
        else:
            return 'none'
    
    # ✅ SYNC STATUS METHODS
    
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
    
    # ✅ STATISTICS METHODS
    
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
            return len([u for u in self.users if u.is_active])
        except Exception as e:
            logger.error(f"Error getting active user count: {e}")
            return 0
    
    # ✅ SETTINGS METHODS
    
    def get_settings(self):
        """Get company settings as dict"""
        base_settings = {
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
        
        # Merge with stored settings
        stored_settings = self._get_settings_dict_safe()
        base_settings.update(stored_settings)
        
        return base_settings
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        settings = self.get_settings()
        return settings.get(key, default)
    
    def update_settings(self, new_settings):
        """Update company settings"""
        try:
            current_settings = self.get_settings()
            current_settings.update(new_settings)
            
            # Try to store in database
            try:
                self.settings = json.dumps(current_settings)
            except AttributeError:
                # Store in cache if column doesn't exist
                self._settings_cache = current_settings
            
            db.session.commit()
            logger.info(f"Settings updated for company {self.id}")
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
    
    # ✅ DASHBOARD STATISTICS
    
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
                'total': len(self.users),
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
        data = {
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
        
        if include_sensitive:
            data.update({
                'postgresql_host': self.get_postgresql_host(),
                'postgresql_port': self.get_postgresql_port(),
                'postgresql_database': self.get_postgresql_database(),
                'postgresql_username': self.get_postgresql_username(),
                'api_base_url': self.get_api_base_url(),
                'api_username': self.get_api_username(),
            })
        
        return data
    
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