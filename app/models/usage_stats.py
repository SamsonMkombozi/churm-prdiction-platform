"""
Usage Statistics Model
app/models/usage_stats.py

Tracks customer internet usage from spl_statistics table
"""
from app.extensions import db
from datetime import datetime


class UsageStats(db.Model):
    """Customer usage statistics"""
    
    __tablename__ = 'usage_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # CRM fields
    crm_usage_id = db.Column(db.String(100), unique=True)
    crm_customer_id = db.Column(db.String(100))  # From spl_statistics
    service_id = db.Column(db.String(50))
    tariff_id = db.Column(db.String(50))
    login = db.Column(db.String(100))  # e.g., SHO000000208
    
    # Usage data
    in_bytes = db.Column(db.BigInteger, default=0)  # Download
    out_bytes = db.Column(db.BigInteger, default=0)  # Upload
    total_bytes = db.Column(db.BigInteger, default=0)  # Total usage
    
    # Session timing
    start_date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_date = db.Column(db.Date)
    end_time = db.Column(db.Time)
    session_duration_minutes = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('usage_stats', lazy='dynamic'))
    customer = db.relationship('Customer', backref=db.backref('usage_stats', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UsageStats {self.login}: {self.total_bytes_mb}MB>'
    
    @property
    def total_bytes_mb(self):
        """Total usage in MB"""
        return round(self.total_bytes / (1024 * 1024), 2) if self.total_bytes else 0
    
    @property
    def total_bytes_gb(self):
        """Total usage in GB"""
        return round(self.total_bytes / (1024 * 1024 * 1024), 2) if self.total_bytes else 0
    
    def calculate_duration(self):
        """Calculate session duration in minutes"""
        if self.start_date and self.start_time and self.end_date and self.end_time:
            start_dt = datetime.combine(self.start_date, self.start_time)
            end_dt = datetime.combine(self.end_date, self.end_time)
            duration = (end_dt - start_dt).total_seconds() / 60
            self.session_duration_minutes = int(duration) if duration > 0 else 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'login': self.login,
            'total_bytes': self.total_bytes,
            'total_mb': self.total_bytes_mb,
            'total_gb': self.total_bytes_gb,
            'in_bytes': self.in_bytes,
            'out_bytes': self.out_bytes,
            'session_duration': self.session_duration_minutes,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }