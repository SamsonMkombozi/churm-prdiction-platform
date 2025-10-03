"""
Payment Model - Payment transactions from CRM
"""
from datetime import datetime
from app.extensions import db

class Payment(db.Model):  # FIXED: Changed from "Customer" to "Payment"
    __tablename__ = 'payments'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    # CRM Fields
    crm_payment_id = db.Column(db.String(100), index=True)
    transaction_id = db.Column(db.String(100))
    
    # Payment Information
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_method = db.Column(db.String(50))  # cash, card, mobile_money, bank_transfer
    payment_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # Status
    status = db.Column(db.String(20))  # pending, completed, failed, refunded
    
    # Additional Info
    description = db.Column(db.String(255))
    reference_number = db.Column(db.String(100))
    invoice_number = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_payment_company_customer', 'company_id', 'customer_id'),
        db.Index('idx_payment_date', 'company_id', 'payment_date'),
        db.Index('idx_payment_crm', 'company_id', 'crm_payment_id'),
    )
    
    def __repr__(self):
        return f'<Payment {self.amount} {self.currency} - {self.payment_date}>'
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'crm_payment_id': self.crm_payment_id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def find_by_crm_id(company_id, crm_payment_id):
        """Find payment by CRM ID"""
        return Payment.query.filter_by(
            company_id=company_id,
            crm_payment_id=crm_payment_id
        ).first()
    
    @staticmethod
    def get_recent_payments(company_id, limit=10):
        """Get recent payments for a company"""
        return Payment.query.filter_by(
            company_id=company_id
        ).order_by(Payment.payment_date.desc()).limit(limit).all()
    
    @staticmethod
    def get_total_revenue(company_id, start_date=None, end_date=None):
        """Calculate total revenue for a company"""
        query = db.session.query(db.func.sum(Payment.amount))\
            .filter(Payment.company_id == company_id,
                   Payment.status == 'completed')
        
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        
        return query.scalar() or 0.0