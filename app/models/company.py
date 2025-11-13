"""
COMPLETE FIXED Company Model - Enhanced for Settings Page
app/models/company.py

✅ INCLUDES:
1. All new database columns for settings
2. Enhanced get_setting and update_settings methods
3. Proper validation and error handling
4. All existing functionality preserved
"""

from app.extensions import db
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class Company(db.Model):
    """Enhanced Company model with complete settings support"""
    
    __tablename__ = 'companies'
    
    # ===== EXISTING BASIC FIELDS =====
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # ===== EXISTING CRM API FIELDS =====
    crm_api_url = db.Column(db.String(255))
    encrypted_api_key = db.Column(db.Text)
    
    # ===== EXISTING SETTINGS AND SYNC FIELDS =====
    settings = db.Column(db.Text)  # Legacy settings field
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20))
    sync_error = db.Column(db.Text)
    total_syncs = db.Column(db.Integer)
    
    # ===== EXISTING STATUS AND TIMESTAMPS =====
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ===== EXISTING API CONFIGURATION =====
    api_token = db.Column(db.String(255))
    api_base_url = db.Column(db.String(255))
    
    # ===== EXISTING POSTGRESQL CONFIGURATION =====
    postgresql_host = db.Column(db.String(255))
    postgresql_port = db.Column(db.Integer, default=5432)
    postgresql_database = db.Column(db.String(100))
    postgresql_username = db.Column(db.String(100))
    postgresql_password_encrypted = db.Column(db.Text)
    
    # ===== EXISTING API CONFIGURATION (ENCRYPTED) =====
    api_key_encrypted = db.Column(db.Text)
    api_username = db.Column(db.String(100))
    api_password_encrypted = db.Column(db.Text)
    
    # ===== EXISTING ADDITIONAL FIELDS =====
    logo_url = db.Column(db.String(255))
    
    # ===== NEW SETTINGS COLUMNS =====
    # These will be added by the migration script
    
    # Notification Settings
    notification_email = db.Column(db.String(255))
    enable_email_alerts = db.Column(db.Boolean, default=False)
    enable_auto_sync = db.Column(db.Boolean, default=True)
    sync_frequency = db.Column(db.Integer, default=3600)
    
    # Prediction Settings
    prediction_threshold_high = db.Column(db.Float, default=0.7)
    prediction_threshold_medium = db.Column(db.Float, default=0.4)
    
    # Regional Settings
    timezone = db.Column(db.String(50), default='Africa/Nairobi')
    date_format = db.Column(db.String(20), default='%Y-%m-%d')
    currency = db.Column(db.String(3), default='TZS')
    
    # Additional CRM Settings
    crm_sync_enabled = db.Column(db.Boolean, default=True)
    last_settings_update = db.Column(db.DateTime)
    
    # JSON field for flexible settings storage
    settings_json = db.Column(db.Text)
    app_settings = db.Column(db.Text)
    
    # User preferences
    default_language = db.Column(db.String(10), default='en')
    dashboard_refresh_interval = db.Column(db.Integer, default=300)
    
    # Feature flags
    enable_predictions = db.Column(db.Boolean, default=True)
    enable_analytics = db.Column(db.Boolean, default=True)
    enable_reports = db.Column(db.Boolean, default=True)
    
    # Backup and maintenance
    auto_backup_enabled = db.Column(db.Boolean, default=False)
    backup_frequency = db.Column(db.Integer, default=86400)
    
    # ===== RELATIONSHIPS =====
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True, 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    # ===== ENHANCED SETTINGS METHODS =====
    
    def get_setting(self, key, default=None):
        """
        Enhanced get_setting with multiple fallback strategies
        
        Args:
            key (str): Setting key to retrieve
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        try:
            # Strategy 1: Check direct database column first (highest priority)
            if hasattr(self, key):
                value = getattr(self, key, None)
                if value is not None:
                    logger.debug(f"Found {key} in direct column: {value}")
                    return value
            
            # Strategy 2: Check settings_json field
            if hasattr(self, 'settings_json') and self.settings_json:
                try:
                    settings_dict = json.loads(self.settings_json)
                    if key in settings_dict:
                        logger.debug(f"Found {key} in settings_json: {settings_dict[key]}")
                        return settings_dict[key]
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing settings_json for company {self.id}: {e}")
            
            # Strategy 3: Check app_settings field
            if hasattr(self, 'app_settings') and self.app_settings:
                try:
                    settings_dict = json.loads(self.app_settings)
                    if key in settings_dict:
                        logger.debug(f"Found {key} in app_settings: {settings_dict[key]}")
                        return settings_dict[key]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Strategy 4: Check legacy settings field
            if hasattr(self, 'settings') and self.settings:
                if isinstance(self.settings, dict):
                    if key in self.settings:
                        return self.settings[key]
                elif isinstance(self.settings, str):
                    try:
                        settings_dict = json.loads(self.settings)
                        if key in settings_dict:
                            return settings_dict[key]
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Strategy 5: Hardcoded defaults for Tanzania/East Africa
            defaults = {
                # Notification Settings
                'notification_email': '',
                'enable_email_alerts': False,
                'enable_auto_sync': True,
                'sync_frequency': 3600,
                
                # Prediction Settings
                'prediction_threshold_high': 0.7,
                'prediction_threshold_medium': 0.4,
                
                # Regional Settings (Tanzania-focused)
                'timezone': 'Africa/Nairobi',  # East Africa Time
                'date_format': '%Y-%m-%d',
                'currency': 'TZS',  # Tanzanian Shilling
                
                # Feature Settings
                'enable_predictions': True,
                'enable_analytics': True,
                'enable_reports': True,
                'dashboard_refresh_interval': 300,
                'default_language': 'en',
                
                # CRM Settings
                'crm_sync_enabled': True,
                
                # Backup Settings
                'auto_backup_enabled': False,
                'backup_frequency': 86400
            }
            
            result = defaults.get(key, default)
            logger.debug(f"Using default for {key}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting setting '{key}' for company {self.id}: {e}")
            return default
    
    def update_settings(self, settings_dict):
        """
        Enhanced update_settings with comprehensive handling
        
        Args:
            settings_dict (dict): Dictionary of setting key-value pairs
        """
        try:
            logger.info(f"Updating settings for company {self.id} ({self.name}): {list(settings_dict.keys())}")
            
            # Strategy 1: Update direct database columns if they exist
            direct_updates = {}
            for key, value in settings_dict.items():
                if hasattr(self, key):
                    try:
                        old_value = getattr(self, key, None)
                        setattr(self, key, value)
                        direct_updates[key] = value
                        logger.debug(f"Direct column update {key}: {old_value} -> {value}")
                    except Exception as e:
                        logger.warning(f"Could not set direct attribute {key}: {e}")
            
            # Strategy 2: Update JSON settings for remaining items
            json_settings = {k: v for k, v in settings_dict.items() if k not in direct_updates}
            
            if json_settings and hasattr(self, 'settings_json'):
                # Load existing JSON settings
                current_settings = {}
                if self.settings_json:
                    try:
                        current_settings = json.loads(self.settings_json)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Error parsing existing settings_json: {e}")
                        current_settings = {}
                
                # Update with new settings
                current_settings.update(json_settings)
                
                # Save back to JSON field
                self.settings_json = json.dumps(current_settings)
                logger.debug(f"Updated JSON settings: {json_settings}")
            
            # Strategy 3: Update legacy settings field as fallback
            elif json_settings and hasattr(self, 'settings'):
                current_settings = {}
                if self.settings:
                    try:
                        if isinstance(self.settings, str):
                            current_settings = json.loads(self.settings)
                        elif isinstance(self.settings, dict):
                            current_settings = self.settings.copy()
                    except (json.JSONDecodeError, TypeError):
                        current_settings = {}
                
                current_settings.update(json_settings)
                self.settings = json.dumps(current_settings)
                logger.debug(f"Updated legacy settings: {json_settings}")
            
            # Update timestamp if field exists
            if hasattr(self, 'last_settings_update'):
                self.last_settings_update = datetime.utcnow()
            
            # Update general updated_at timestamp
            if hasattr(self, 'updated_at'):
                self.updated_at = datetime.utcnow()
            
            # Commit changes
            db.session.commit()
            
            logger.info(f"Successfully updated {len(settings_dict)} settings for company {self.name}")
            
        except Exception as e:
            logger.error(f"Error updating settings for company {self.id}: {e}")
            try:
                db.session.rollback()
            except:
                pass
            raise e
    
    def set_crm_api_key(self, api_key):
        """Enhanced CRM API key handling"""
        try:
            if hasattr(self, 'encrypted_api_key'):
                self.encrypted_api_key = api_key
                logger.info(f"Updated encrypted_api_key for company {self.name}")
            elif hasattr(self, 'api_key_encrypted'):
                self.api_key_encrypted = api_key
                logger.info(f"Updated api_key_encrypted for company {self.name}")
            else:
                # Store in settings as fallback
                self.update_settings({'crm_api_key': api_key})
                logger.info(f"Stored CRM API key in settings for company {self.name}")
        except Exception as e:
            logger.error(f"Error setting API key for company {self.id}: {e}")
            raise e
    
    def validate_settings(self, settings_dict):
        """
        Validate settings before saving
        
        Args:
            settings_dict (dict): Settings to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Validate email format
            if 'notification_email' in settings_dict:
                email = settings_dict['notification_email']
                if email and '@' not in email:
                    return False, "Invalid email format for notification_email"
            
            # Validate threshold values
            for threshold_key in ['prediction_threshold_high', 'prediction_threshold_medium']:
                if threshold_key in settings_dict:
                    try:
                        value = float(settings_dict[threshold_key])
                        if not 0 <= value <= 1:
                            return False, f"{threshold_key} must be between 0 and 1"
                    except (ValueError, TypeError):
                        return False, f"Invalid {threshold_key} value: must be a number"
            
            # Validate sync frequency
            if 'sync_frequency' in settings_dict:
                try:
                    frequency = int(settings_dict['sync_frequency'])
                    if frequency < 60:  # Minimum 1 minute
                        return False, "Sync frequency must be at least 60 seconds"
                except (ValueError, TypeError):
                    return False, "Invalid sync frequency: must be a number"
            
            # Validate currency (Tanzania focus)
            if 'currency' in settings_dict:
                valid_currencies = ['TZS', 'USD', 'EUR', 'GBP', 'KES']
                if settings_dict['currency'] not in valid_currencies:
                    return False, f"Currency must be one of: {', '.join(valid_currencies)}"
            
            # Validate timezone (East Africa focus)
            if 'timezone' in settings_dict:
                valid_timezones = ['UTC', 'Africa/Nairobi', 'Africa/Dar_es_Salaam', 'America/New_York', 'Europe/London']
                if settings_dict['timezone'] not in valid_timezones:
                    return False, f"Invalid timezone. Must be one of: {', '.join(valid_timezones)}"
            
            return True, "Settings are valid"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    # ===== EXISTING METHODS (PRESERVED) =====
    
    def get_postgresql_password(self):
        """Get decrypted PostgreSQL password"""
        try:
            if self.postgresql_password_encrypted:
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(self.postgresql_password_encrypted)
                except ImportError:
                    return self.postgresql_password_encrypted
            return None
        except Exception as e:
            logger.warning(f"Error getting PostgreSQL password: {e}")
            return self.postgresql_password_encrypted
    
    def set_postgresql_password(self, password):
        """Set PostgreSQL password (with encryption if available)"""
        try:
            if password:
                try:
                    from app.utils.encryption import encrypt_value
                    self.postgresql_password_encrypted = encrypt_value(password)
                except ImportError:
                    self.postgresql_password_encrypted = password
            else:
                self.postgresql_password_encrypted = None
        except Exception as e:
            logger.warning(f"Error setting PostgreSQL password: {e}")
            self.postgresql_password_encrypted = password
    
    def has_postgresql_config(self):
        """Check PostgreSQL configuration"""
        try:
            host = self.postgresql_host
            database = self.postgresql_database
            username = self.postgresql_username
            password = self.postgresql_password_encrypted
            
            has_config = bool(
                host and host.strip() and
                database and database.strip() and
                username and username.strip() and
                password and password.strip()
            )
            
            return has_config
        except Exception as e:
            logger.error(f"Error checking PostgreSQL config: {e}")
            return False
    
    def has_api_config(self):
        """Check if API connection is configured"""
        try:
            api_url = self.api_base_url or self.crm_api_url
            return bool(api_url and api_url.strip())
        except Exception as e:
            logger.error(f"Error checking API config: {e}")
            return False
    
    def get_preferred_sync_method(self):
        """Get preferred sync method"""
        try:
            if self.has_postgresql_config():
                return 'postgresql'
            elif self.has_api_config():
                return 'api'
            else:
                return 'none'
        except Exception as e:
            logger.error(f"Error getting preferred sync method: {e}")
            return 'none'
    
    def get_postgresql_config(self):
        """Get complete PostgreSQL configuration"""
        try:
            return {
                'host': self.postgresql_host,
                'port': self.postgresql_port or 5432,
                'database': self.postgresql_database,
                'username': self.postgresql_username,
                'password': self.get_postgresql_password()
            }
        except Exception as e:
            logger.error(f"Error getting PostgreSQL config: {e}")
            return {'host': None, 'port': 5432, 'database': None, 'username': None, 'password': None}
    
    def get_api_config(self):
        """Get complete API configuration"""
        try:
            return {
                'base_url': self.api_base_url or self.crm_api_url,
                'username': self.api_username,
                'password': self.get_api_password(),
                'api_key': self.get_api_key(),
                'token': self.api_token
            }
        except Exception as e:
            logger.error(f"Error getting API config: {e}")
            return {'base_url': None, 'username': None, 'password': None, 'api_key': None, 'token': None}
    
    def get_api_password(self):
        """Get decrypted API password"""
        try:
            if self.api_password_encrypted:
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(self.api_password_encrypted)
                except ImportError:
                    return self.api_password_encrypted
            return None
        except Exception as e:
            logger.warning(f"Error getting API password: {e}")
            return self.api_password_encrypted
    
    def get_api_key(self):
        """Get decrypted API key"""
        try:
            if self.api_key_encrypted:
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(self.api_key_encrypted)
                except ImportError:
                    return self.api_key_encrypted
            elif self.encrypted_api_key:
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(self.encrypted_api_key)
                except ImportError:
                    return self.encrypted_api_key
            return None
        except Exception as e:
            logger.warning(f"Error getting API key: {e}")
            return self.api_key_encrypted or self.encrypted_api_key
    
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
    
    def get_active_user_count(self):
        """Get count of active users"""
        try:
            return len([u for u in self.users if getattr(u, 'is_active', True)])
        except Exception as e:
            logger.error(f"Error getting active user count: {e}")
            return 1
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            return {
                'total_customers': self.get_customer_count(),
                'active_customers': self.get_active_customer_count(),
                'high_risk_customers': self.get_high_risk_customer_count(),
                'total_tickets': self.get_ticket_count(),
                'total_payments': self.get_payment_count(),
                'active_users': self.get_active_user_count(),
                'last_sync': self.last_sync_at,
                'sync_status': self.sync_status or 'never',
                'total_syncs': self.total_syncs or 0,
                'sync_error': self.sync_error
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                'total_customers': 0,
                'active_customers': 0,
                'high_risk_customers': 0,
                'total_tickets': 0,
                'total_payments': 0,
                'active_users': 1,
                'last_sync': None,
                'sync_status': 'error',
                'total_syncs': 0,
                'sync_error': str(e)
            }
    
    # ===== SYNC STATUS MANAGEMENT METHODS =====
    
    def mark_sync_started(self):
        """Mark that a sync operation has started"""
        try:
            self.sync_status = 'syncing'
            self.sync_error = None
            db.session.commit()
            logger.info(f"Company {self.name}: Sync started")
        except Exception as e:
            logger.error(f"Error marking sync started: {e}")
            db.session.rollback()
    
    def mark_sync_completed(self):
        """Mark that a sync operation completed successfully"""
        try:
            self.sync_status = 'completed'
            self.last_sync_at = datetime.utcnow()
            self.sync_error = None
            self.total_syncs = (self.total_syncs or 0) + 1
            db.session.commit()
            logger.info(f"Company {self.name}: Sync completed successfully (Total syncs: {self.total_syncs})")
        except Exception as e:
            logger.error(f"Error marking sync completed: {e}")
            db.session.rollback()
    
    def mark_sync_failed(self, error_message):
        """Mark that a sync operation failed"""
        try:
            self.sync_status = 'failed'
            self.sync_error = error_message[:500] if error_message else 'Unknown error'  # Truncate long errors
            db.session.commit()
            logger.error(f"Company {self.name}: Sync failed - {error_message}")
        except Exception as e:
            logger.error(f"Error marking sync failed: {e}")
            db.session.rollback()
    
    @staticmethod
    def create_company(name, slug=None, **kwargs):
        """Create a new company"""
        try:
            if not slug:
                slug = name.lower().replace(' ', '-').replace('_', '-')
            
            company = Company(
                name=name,
                slug=slug,
                sync_status='never',
                total_syncs=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                **kwargs
            )
            
            db.session.add(company)
            db.session.commit()
            
            logger.info(f"Created new company: {name}")
            return company
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            db.session.rollback()
            raise