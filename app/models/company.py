"""
FIXED Company Model - Matches Your Encrypted Database Schema
app/models/company.py

✅ FIXES:
1. Uses encrypted column names that actually exist in your database
2. Handles decryption for PostgreSQL credentials
3. Matches your exact database schema
"""

from app.extensions import db
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class Company(db.Model):
    """Company model matching your actual encrypted database schema"""
    
    __tablename__ = 'companies'
    
    # Basic company fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # CRM API fields (existing in your schema)
    crm_api_url = db.Column(db.String(255))
    encrypted_api_key = db.Column(db.Text)
    
    # General settings
    settings = db.Column(db.Text)
    
    # Sync-related fields
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20))
    sync_error = db.Column(db.Text)
    total_syncs = db.Column(db.Integer)
    
    # Status and timestamps
    is_active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # API configuration (existing in your schema)
    api_token = db.Column(db.String(255))
    api_base_url = db.Column(db.String(255))
    
    # ✅ PostgreSQL configuration (matches your actual database schema)
    postgresql_host = db.Column(db.String(255))
    postgresql_port = db.Column(db.Integer, default=5432)
    postgresql_database = db.Column(db.String(100))
    postgresql_username = db.Column(db.String(100))
    postgresql_password_encrypted = db.Column(db.Text)  # ✅ MATCHES YOUR DATABASE
    
    # ✅ API configuration (matches your actual database schema)
    api_key_encrypted = db.Column(db.Text)  # ✅ MATCHES YOUR DATABASE
    api_username = db.Column(db.String(100))
    api_password_encrypted = db.Column(db.Text)  # ✅ MATCHES YOUR DATABASE
    
    # Additional fields from your schema
    logo_url = db.Column(db.String(255))
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    customers = db.relationship('Customer', backref='company', lazy=True, 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    # ✅ FIXED: Configuration methods that work with encrypted columns
    
    def get_postgresql_password(self):
        """Get decrypted PostgreSQL password"""
        try:
            if self.postgresql_password_encrypted:
                # Try to decrypt (if you have encryption setup)
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(self.postgresql_password_encrypted)
                except ImportError:
                    # If no encryption module, assume it's stored as plain text
                    return self.postgresql_password_encrypted
            return None
        except Exception as e:
            logger.warning(f"Error getting PostgreSQL password: {e}")
            return self.postgresql_password_encrypted  # Fallback to encrypted value
    
    def set_postgresql_password(self, password):
        """Set PostgreSQL password (with encryption if available)"""
        try:
            if password:
                try:
                    from app.utils.encryption import encrypt_value
                    self.postgresql_password_encrypted = encrypt_value(password)
                except ImportError:
                    # If no encryption module, store as plain text
                    self.postgresql_password_encrypted = password
            else:
                self.postgresql_password_encrypted = None
        except Exception as e:
            logger.warning(f"Error setting PostgreSQL password: {e}")
            # Fallback to plain storage
            self.postgresql_password_encrypted = password
    
    def has_postgresql_config(self):
        """✅ FIXED: Check PostgreSQL configuration using actual database columns"""
        try:
            # Check the actual database columns that exist
            host = self.postgresql_host
            database = self.postgresql_database
            username = self.postgresql_username
            password = self.postgresql_password_encrypted  # Use encrypted column
            
            logger.info(f"🔍 PostgreSQL config check for {self.name}:")
            logger.info(f"   Host: {repr(host)}")
            logger.info(f"   Database: {repr(database)}")
            logger.info(f"   Username: {repr(username)}")
            logger.info(f"   Password: {'***' if password else 'None'}")
            
            # All required fields must have values
            has_config = bool(
                host and host.strip() and
                database and database.strip() and
                username and username.strip() and
                password and password.strip()
            )
            
            if has_config:
                logger.info("✅ PostgreSQL configuration is COMPLETE")
            else:
                logger.warning("❌ PostgreSQL configuration is INCOMPLETE")
                
            return has_config
            
        except Exception as e:
            logger.error(f"❌ Error checking PostgreSQL config: {e}")
            return False
    
    def has_api_config(self):
        """Check if API connection is configured"""
        try:
            # Check both possible API URL columns
            api_url = self.api_base_url or self.crm_api_url
            has_config = bool(api_url and api_url.strip())
            
            logger.info(f"🌐 API config for {self.name}: {repr(api_url)} -> {has_config}")
            return has_config
            
        except Exception as e:
            logger.error(f"❌ Error checking API config: {e}")
            return False
    
    def get_preferred_sync_method(self):
        """✅ FIXED: Get preferred sync method"""
        try:
            if self.has_postgresql_config():
                logger.info("🚀 Preferred method: PostgreSQL (Fast)")
                return 'postgresql'
            elif self.has_api_config():
                logger.info("🌐 Preferred method: API (Standard)")
                return 'api'
            else:
                logger.warning("❌ No sync method configured")
                return 'none'
        except Exception as e:
            logger.error(f"❌ Error getting preferred sync method: {e}")
            return 'none'
    
    # ✅ FIXED: Configuration getters that use actual database columns
    
    def get_postgresql_config(self):
        """Get complete PostgreSQL configuration"""
        try:
            config = {
                'host': self.postgresql_host,
                'port': self.postgresql_port or 5432,
                'database': self.postgresql_database,
                'username': self.postgresql_username,
                'password': self.get_postgresql_password()  # Decrypt password
            }
            
            logger.info(f"📊 Retrieved PostgreSQL config: host={config['host']}, db={config['database']}, user={config['username']}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error getting PostgreSQL config: {e}")
            return {'host': None, 'port': 5432, 'database': None, 'username': None, 'password': None}
    
    def get_api_config(self):
        """Get complete API configuration"""
        try:
            return {
                'base_url': self.api_base_url or self.crm_api_url,
                'username': self.api_username,
                'password': self.get_api_password(),  # Decrypt if needed
                'api_key': self.get_api_key(),  # Decrypt if needed
                'token': self.api_token
            }
        except Exception as e:
            logger.error(f"❌ Error getting API config: {e}")
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
            # Try both possible API key columns
            encrypted_key = self.api_key_encrypted or self.encrypted_api_key
            if encrypted_key:
                try:
                    from app.utils.encryption import decrypt_value
                    return decrypt_value(encrypted_key)
                except ImportError:
                    return encrypted_key
            return None
        except Exception as e:
            logger.warning(f"Error getting API key: {e}")
            return encrypted_key
    
    # ✅ FIXED: Debug method to check what's actually in the database
    
    def debug_config(self):
        """Debug method to see exactly what's stored in database"""
        try:
            logger.info(f"🔍 DEBUG CONFIG for {self.name} (ID: {self.id}):")
            logger.info(f"   postgresql_host: {repr(self.postgresql_host)}")
            logger.info(f"   postgresql_port: {repr(self.postgresql_port)}")
            logger.info(f"   postgresql_database: {repr(self.postgresql_database)}")
            logger.info(f"   postgresql_username: {repr(self.postgresql_username)}")
            logger.info(f"   postgresql_password_encrypted: {'***' if self.postgresql_password_encrypted else 'None'}")
            logger.info(f"   api_base_url: {repr(self.api_base_url)}")
            logger.info(f"   crm_api_url: {repr(self.crm_api_url)}")
            
            # Check what methods return
            has_pg = self.has_postgresql_config()
            has_api = self.has_api_config()
            preferred = self.get_preferred_sync_method()
            
            logger.info(f"   has_postgresql_config(): {has_pg}")
            logger.info(f"   has_api_config(): {has_api}")
            logger.info(f"   get_preferred_sync_method(): {preferred}")
            
            return {
                'postgresql_configured': has_pg,
                'api_configured': has_api,
                'preferred_method': preferred
            }
            
        except Exception as e:
            logger.error(f"❌ Debug config failed: {e}")
            return None
    
    # ✅ SAFE: Update configuration methods that handle encryption
    
    def update_postgresql_config(self, config_data):
        """Update PostgreSQL configuration"""
        try:
            if 'postgresql_host' in config_data:
                self.postgresql_host = config_data['postgresql_host']
            if 'postgresql_port' in config_data:
                self.postgresql_port = int(config_data['postgresql_port']) if config_data['postgresql_port'] else 5432
            if 'postgresql_database' in config_data:
                self.postgresql_database = config_data['postgresql_database']
            if 'postgresql_username' in config_data:
                self.postgresql_username = config_data['postgresql_username']
            if 'postgresql_password' in config_data:
                self.set_postgresql_password(config_data['postgresql_password'])
            
            logger.info(f"✅ PostgreSQL config updated for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update PostgreSQL config: {e}")
            return False
    
    # Sync status methods (unchanged)
    
    def mark_sync_started(self):
        """Mark that sync has started"""
        self.sync_status = 'in_progress'
        self.sync_error = None
        try:
            db.session.commit()
            logger.info(f"✅ Marked sync started for {self.name}")
        except Exception as e:
            logger.error(f"❌ Error updating sync status: {e}")
    
    def mark_sync_completed(self):
        """Mark that sync completed successfully"""
        self.last_sync_at = datetime.utcnow()
        self.sync_status = 'completed'
        self.sync_error = None
        self.total_syncs = (self.total_syncs or 0) + 1
        try:
            db.session.commit()
            logger.info(f"✅ Marked sync completed for {self.name}")
        except Exception as e:
            logger.error(f"❌ Error updating sync status: {e}")
    
    def mark_sync_failed(self, error_message):
        """Mark that sync failed"""
        self.sync_status = 'failed'
        self.sync_error = error_message
        try:
            db.session.commit()
            logger.info(f"❌ Marked sync failed for {self.name}: {error_message}")
        except Exception as e:
            logger.error(f"❌ Error updating sync status: {e}")
    
    # Statistics methods (unchanged but with safe access)
    
    def get_customer_count(self):
        """Get total number of customers"""
        try:
            from app.models.customer import Customer
            count = Customer.query.filter_by(company_id=self.id).count()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting customer count: {e}")
            return 0
    
    def get_active_customer_count(self):
        """Get count of active customers"""
        try:
            from app.models.customer import Customer
            count = Customer.query.filter_by(
                company_id=self.id,
                status='active'
            ).count()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting active customer count: {e}")
            return 0
    
    def get_ticket_count(self):
        """Get total number of tickets"""
        try:
            from app.models.ticket import Ticket
            count = Ticket.query.filter_by(company_id=self.id).count()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting ticket count: {e}")
            return 0
    
    def get_payment_count(self):
        """Get total number of payments"""
        try:
            from app.models.payment import Payment
            count = Payment.query.filter_by(company_id=self.id).count()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting payment count: {e}")
            return 0
    
    def get_high_risk_customer_count(self):
        """Get count of high-risk customers"""
        try:
            from app.models.customer import Customer
            count = Customer.query.filter_by(
                company_id=self.id,
                churn_risk='high'
            ).count()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting high risk customer count: {e}")
            return 0
    
    def get_active_user_count(self):
        """Get count of active users"""
        try:
            return len([u for u in self.users if getattr(u, 'is_active', True)])
        except Exception as e:
            logger.error(f"❌ Error getting active user count: {e}")
            return 1
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            stats = {
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
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
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
    
    def to_dict(self, include_sensitive=False):
        """Convert company to dictionary"""
        try:
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
                'total_syncs': self.total_syncs,
                'has_postgresql_config': self.has_postgresql_config(),
                'has_api_config': self.has_api_config(),
                'preferred_sync_method': self.get_preferred_sync_method()
            }
            
            if include_sensitive:
                data.update({
                    'postgresql_config': self.get_postgresql_config(),
                    'api_config': self.get_api_config(),
                })
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error converting company to dict: {e}")
            return {'error': str(e)}
    
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
                **kwargs
            )
            
            db.session.add(company)
            db.session.commit()
            
            logger.info(f"✅ Created new company: {name}")
            return company
            
        except Exception as e:
            logger.error(f"❌ Error creating company: {e}")
            db.session.rollback()
            raise