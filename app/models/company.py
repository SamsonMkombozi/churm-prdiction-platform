"""
Company Model with Tenant Isolation
"""
from datetime import datetime
from app.extensions import db  # Changed from 'from app import db'
from cryptography.fernet import Fernet
import os
import json

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    
    # CRM Configuration
    crm_api_url = db.Column(db.String(255))
    encrypted_api_key = db.Column(db.Text)  # Encrypted API key
    
    # Company Settings (JSON)
    settings = db.Column(db.Text, default='{}')  # JSON string
    
    # Sync Status
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, completed, failed
    
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
    
    def update_settings(self, new_settings):
        """Update settings from dictionary"""
        current_settings = self.get_settings()
        current_settings.update(new_settings)
        self.settings = json.dumps(current_settings)
    
    def get_customer_count(self):
        """Get total number of customers for this company"""
        from app.models.customer import Customer
        return Customer.query.filter_by(company_id=self.id).count()
    
    def get_ticket_count(self):
        """Get total number of tickets for this company"""
        from app.models.ticket import Ticket
        return Ticket.query.filter_by(company_id=self.id).count()
    
    def get_payment_count(self):
        """Get total number of payments for this company"""
        from app.models.payment import Payment
        return Payment.query.filter_by(company_id=self.id).count()
    
    def get_active_customer_count(self):
        """Get count of active customers"""
        from app.models.customer import Customer
        return Customer.query.filter_by(
            company_id=self.id,
            status='active'
        ).count()
    
    def update_sync_status(self, status, commit=True):
        """Update sync status"""
        self.sync_status = status
        if status == 'completed':
            self.last_sync_at = datetime.utcnow()
        
        if commit:
            db.session.commit()
    
    @staticmethod
    def generate_encryption_key():
        """Generate a new encryption key (run once, store in .env)"""
        return Fernet.generate_key().decode()