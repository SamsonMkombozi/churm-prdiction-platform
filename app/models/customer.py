from datetime import datetime, timedelta
from app.extensions import db
import json

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    crm_customer_id = db.Column(db.String(50), index=True)
    external_id = db.Column(db.String(50), unique=True)
    customer_no = db.Column(db.String(50), index=True)
    disconnection_date = db.Column(db.DateTime)
    signup_date = db.Column(db.DateTime)
    date_installed = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    connection_status = db.Column(db.String(50))
    account_type = db.Column(db.String(50), default='personal')
    service_plan = db.Column(db.String(100), default='Standard')
    monthly_charges = db.Column(db.Float, default=0.0)
    total_charges = db.Column(db.Float, default=0.0)
    outstanding_balance = db.Column(db.Float, default=0.0)
    account_value = db.Column(db.Float, default=0.0)
    tenure_months = db.Column(db.Float, default=0.0)
    total_payments = db.Column(db.Integer, default=0)
    successful_payments = db.Column(db.Integer, default=0)
    failed_payments = db.Column(db.Integer, default=0)
    total_paid_amount = db.Column(db.Float, default=0.0)
    last_payment_date = db.Column(db.DateTime)
    days_since_last_payment = db.Column(db.Integer, default=0)
    payment_consistency_score = db.Column(db.Float, default=1.0)
    total_tickets = db.Column(db.Integer, default=0)
    open_tickets = db.Column(db.Integer, default=0)
    complaint_tickets = db.Column(db.Integer, default=0)
    usage_records = db.Column(db.Integer, default=0)
    avg_data_usage = db.Column(db.Float, default=0.0)
    total_data_consumed = db.Column(db.BigInteger, default=0)
    churn_probability = db.Column(db.Float, default=0.0)
    churn_risk = db.Column(db.String(20), default='unknown')
    days_since_disconnection = db.Column(db.Integer, default=0)
    disconnection_risk_level = db.Column(db.String(20))
    last_prediction_date = db.Column(db.DateTime)
    prediction_reasoning = db.Column(db.Text)
    churn_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # FIXED: Use back_populates instead of backref
    company = db.relationship('Company', back_populates='customers')
    
    def __repr__(self):
        return f'<Customer {self.customer_name}>'
    
    @property
    def display_name(self):
        return self.customer_name or self.name or f'Customer {self.id}'
    
    @property
    def risk_badge_class(self):
        risk_classes = {'high': 'bg-danger', 'medium': 'bg-warning', 'low': 'bg-success', 'unknown': 'bg-secondary'}
        return risk_classes.get(self.churn_risk, 'bg-secondary')
    
    @property
    def risk_percentage(self):
        if self.churn_probability:
            return f"{self.churn_probability * 100:.1f}%"
        return "N/A"
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'crm_customer_id': self.crm_customer_id,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'churn_probability': self.churn_probability,
            'churn_risk': self.churn_risk,
            'last_payment_date': self.last_payment_date.isoformat() if self.last_payment_date else None,
            'days_since_last_payment': self.days_since_last_payment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None, 
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'company_id': self.company_id,
            'external_id': self.external_id,
            'customer_no': self.customer_no,
            'address': self.address,
            'account_type': self.account_type,
            'service_plan': self.service_plan,
            'monthly_charges': self.monthly_charges,
            'total_charges': self.total_charges,  
            'outstanding_balance': self.outstanding_balance,
            'account_value': self.account_value,
            'tenure_months': self.tenure_months,
            'total_payments': self.total_payments,
            'successful_payments': self.successful_payments,
            'failed_payments': self.failed_payments,
            'total_paid_amount': self.total_paid_amount,
            'payment_consistency_score': self.payment_consistency_score,
            'total_tickets': self.total_tickets,
            'open_tickets': self.open_tickets,
            'complaint_tickets': self.complaint_tickets,
            'usage_records': self.usage_records,
            'avg_data_usage': self.avg_data_usage,
            'total_data_consumed': self.total_data_consumed,
            'days_since_disconnection': self.days_since_disconnection,
            'disconnection_risk_level': self.disconnection_risk_level,
            'last_prediction_date': self.last_prediction_date.isoformat() if self.last_prediction_date else None,
            'prediction_reasoning': self.prediction_reasoning,
            'churn_score': self.churn_score,
            'risk_level': self.risk_level,   
            'name': self.name
            
        }
