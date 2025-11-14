"""
Usage Statistics Model - Customer usage data from CRM
"""
from datetime import datetime
from app.extensions import db

class UsageStats(db.Model):
    __tablename__ = 'usage_stats'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    # CRM Fields
    crm_usage_id = db.Column(db.String(100), index=True)
    
    # Usage Period
    usage_date = db.Column(db.Date, nullable=False, index=True)
    usage_month = db.Column(db.Integer, index=True)
    usage_year = db.Column(db.Integer, index=True)
    
    # Bandwidth Usage (in MB/GB)
    download_mb = db.Column(db.Float, default=0.0)
    upload_mb = db.Column(db.Float, default=0.0)
    total_mb = db.Column(db.Float, default=0.0)
    
    # Connection Time (in minutes)
    session_duration_minutes = db.Column(db.Integer, default=0)
    
    # Service Information
    service_type = db.Column(db.String(50))  # internet, phone, tv
    plan_name = db.Column(db.String(100))
    
    # Peak/Off-Peak Usage
    peak_usage_mb = db.Column(db.Float, default=0.0)
    offpeak_usage_mb = db.Column(db.Float, default=0.0)
    
    # Quality Metrics
    avg_speed_mbps = db.Column(db.Float)
    uptime_percentage = db.Column(db.Float)
    disconnections = db.Column(db.Integer, default=0)
    
    # Billing
    usage_charge = db.Column(db.Float, default=0.0)
    overage_charge = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_usage_company_customer', 'company_id', 'customer_id'),
        db.Index('idx_usage_date', 'company_id', 'usage_date'),
        db.Index('idx_usage_month_year', 'company_id', 'usage_year', 'usage_month'),
        db.Index('idx_usage_crm', 'company_id', 'crm_usage_id'),
    )
    
    def __repr__(self):
        return f'<UsageStats {self.usage_date} - {self.total_mb:.1f}MB>'
    
    def to_dict(self):
        """Convert usage stats to dictionary"""
        return {
            'id': self.id,
            'crm_usage_id': self.crm_usage_id,
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'usage_month': self.usage_month,
            'usage_year': self.usage_year,
            'download_mb': self.download_mb,
            'upload_mb': self.upload_mb,
            'total_mb': self.total_mb,
            'session_duration_minutes': self.session_duration_minutes,
            'service_type': self.service_type,
            'plan_name': self.plan_name,
            'peak_usage_mb': self.peak_usage_mb,
            'offpeak_usage_mb': self.offpeak_usage_mb,
            'avg_speed_mbps': self.avg_speed_mbps,
            'uptime_percentage': self.uptime_percentage,
            'disconnections': self.disconnections,
            'usage_charge': self.usage_charge,
            'overage_charge': self.overage_charge,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def find_by_crm_id(company_id, crm_usage_id):
        """Find usage record by CRM ID"""
        return UsageStats.query.filter_by(
            company_id=company_id,
            crm_usage_id=crm_usage_id
        ).first()
    
    @staticmethod
    def get_customer_monthly_usage(company_id, customer_id, year, month):
        """Get customer usage for a specific month"""
        return UsageStats.query.filter_by(
            company_id=company_id,
            customer_id=customer_id,
            usage_year=year,
            usage_month=month
        ).all()
    
    @staticmethod
    def get_heavy_users(company_id, threshold_gb=100, limit=None):
        """Get customers with high usage"""
        threshold_mb = threshold_gb * 1024
        
        query = UsageStats.query.filter(
            UsageStats.company_id == company_id,
            UsageStats.total_mb >= threshold_mb
        ).order_by(UsageStats.total_mb.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def calculate_totals(self):
        """Calculate total usage from download/upload"""
        if self.download_mb and self.upload_mb:
            self.total_mb = self.download_mb + self.upload_mb
        return self.total_mb
    
    def get_usage_gb(self):
        """Get usage in GB"""
        if self.total_mb:
            return round(self.total_mb / 1024, 2)
        return 0.0
    
    def is_heavy_user(self, threshold_gb=50):
        """Check if this represents heavy usage"""
        usage_gb = self.get_usage_gb()
        return usage_gb >= threshold_gb