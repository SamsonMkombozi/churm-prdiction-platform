"""
Company Model with Tenant Isolation
Fixed to not require Phase 4 models
"""
from datetime import datetime
from app.extensions import db
from cryptography.fernet import Fernet
import os
import json

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    
    # Optional fields
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # CRM Configuration
    crm_api_url = db.Column(db.String(255))
    encrypted_api_key = db.Column(db.Text)  # Encrypted API key
    
    # Company Settings (JSON)
    settings = db.Column(db.Text, default='{}')  # JSON string
    
    # Sync Status
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, completed, failed
    sync_error = db.Column(db.Text)  # Store last sync error
    total_syncs = db.Column(db.Integer, default=0)  # Track number of syncs
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy='dynamic')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    @property
    def api_key(self):
        """Decrypt and return API key"""
        if not self.encrypted_api_key:
            return None
        
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        fernet = Fernet(encryption_key.encode())
        return fernet.decrypt(self.encrypted_api_key.encode()).decode()
    
    @api_key.setter
    def api_key(self, plain_key):
        """Encrypt and store API key"""
        if not plain_key:
            self.encrypted_api_key = None
            return
        
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        fernet = Fernet(encryption_key.encode())
        self.encrypted_api_key = fernet.encrypt(plain_key.encode()).decode()
    
    def get_settings(self):
        """Parse and return settings as dictionary"""
        try:
            return json.loads(self.settings) if self.settings else {}
        except json.JSONDecodeError:
            return {}
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        settings = self.get_settings()
        return settings.get(key, default)
    
    def update_settings(self, new_settings):
        """Update settings from dictionary"""
        current_settings = self.get_settings()
        current_settings.update(new_settings)
        self.settings = json.dumps(current_settings)
    
    def set_crm_api_key(self, api_key):
        """Set CRM API key (encrypted)"""
        self.api_key = api_key
    
    # Safe methods that check if models exist
    def get_customer_count(self):
        """Get total number of customers for this company"""
        try:
            from app.models.customer import Customer
            return Customer.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            # Customer model doesn't exist yet (Phase 4)
            return 0
    
    def get_ticket_count(self):
        """Get total number of tickets for this company"""
        try:
            from app.models.ticket import Ticket
            return Ticket.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            # Ticket model doesn't exist yet (Phase 4)
            return 0
    
    def get_payment_count(self):
        """Get total number of payments for this company"""
        try:
            from app.models.payment import Payment
            return Payment.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            # Payment model doesn't exist yet (Phase 4)
            return 0
    
    def get_prediction_count(self):
        """Get total number of predictions for this company"""
        try:
            from app.models.prediction import Prediction
            return Prediction.query.filter_by(company_id=self.id).count()
        except (ImportError, ModuleNotFoundError):
            # Prediction model doesn't exist yet (Phase 6)
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
            # Customer model doesn't exist yet or doesn't have churn_risk field
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
            # Customer model doesn't exist yet (Phase 4)
            return 0
    
    def get_active_user_count(self):
        """Get count of active users in this company"""
        return self.users.filter_by(is_active=True).count()
    
    def update_sync_status(self, status, error=None, commit=True):
        """Update sync status"""
        self.sync_status = status
        
        if status == 'completed':
            self.last_sync_at = datetime.utcnow()
            self.total_syncs += 1
            self.sync_error = None
        elif status == 'failed' and error:
            self.sync_error = str(error)
        
        if commit:
            db.session.commit()
    
    @staticmethod
    def generate_encryption_key():
        """Generate a new encryption key (run once, store in .env)"""
        return Fernet.generate_key().decode()