"""
Customer Model - Stores customer data from CRM
"""
from datetime import datetime
from app.extensions import db

class Customer(db.Model):
    __tablename__ = 'customers'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant - Company relationship
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # CRM Fields (from Habari CRM)
    crm_customer_id = db.Column(db.String(100), index=True)  # External CRM ID
    customer_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    
    # Customer Status
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended, churned
    account_type = db.Column(db.String(50))  # personal, business, enterprise
    
    # Financial Information
    monthly_charges = db.Column(db.Float, default=0.0)
    total_charges = db.Column(db.Float, default=0.0)
    outstanding_balance = db.Column(db.Float, default=0.0)
    
    # Service Information
    service_type = db.Column(db.String(100))  # internet, phone, tv, bundle
    connection_type = db.Column(db.String(50))  # fiber, dsl, cable, wireless
    bandwidth_plan = db.Column(db.String(50))  # e.g., "100Mbps", "500Mbps"
    
    # Engagement Metrics
    total_tickets = db.Column(db.Integer, default=0)
    total_payments = db.Column(db.Integer, default=0)
    last_payment_date = db.Column(db.DateTime)
    last_ticket_date = db.Column(db.DateTime)
    
    # Tenure
    signup_date = db.Column(db.DateTime)
    tenure_months = db.Column(db.Integer, default=0)
    
    # Churn Prediction (Phase 6)
    churn_risk = db.Column(db.String(20))  # low, medium, high
    churn_probability = db.Column(db.Float)
    last_prediction_date = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)  # Last CRM sync time
    
    # Relationships
    tickets = db.relationship('Ticket', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_customer_company_crm', 'company_id', 'crm_customer_id'),
        db.Index('idx_customer_status', 'company_id', 'status'),
        db.Index('idx_customer_risk', 'company_id', 'churn_risk'),
    )
    
    def __repr__(self):
        return f'<Customer {self.customer_name} ({self.crm_customer_id})>'
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'crm_customer_id': self.crm_customer_id,
            'customer_name': self.customer_name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'account_type': self.account_type,
            'monthly_charges': self.monthly_charges,
            'total_charges': self.total_charges,
            'outstanding_balance': self.outstanding_balance,
            'service_type': self.service_type,
            'connection_type': self.connection_type,
            'bandwidth_plan': self.bandwidth_plan,
            'total_tickets': self.total_tickets,
            'total_payments': self.total_payments,
            'last_payment_date': self.last_payment_date.isoformat() if self.last_payment_date else None,
            'signup_date': self.signup_date.isoformat() if self.signup_date else None,
            'tenure_months': self.tenure_months,
            'churn_risk': self.churn_risk,
            'churn_probability': self.churn_probability,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def calculate_tenure(self):
        """Calculate tenure in months from signup date"""
        if self.signup_date:
            delta = datetime.utcnow() - self.signup_date
            self.tenure_months = int(delta.days / 30)
        return self.tenure_months
    
    def update_metrics(self):
        """Update customer metrics from related data"""
        self.total_tickets = self.tickets.count()
        self.total_payments = self.payments.count()
        
        # Get last payment date
        last_payment = self.payments.order_by(Payment.payment_date.desc()).first()
        if last_payment:
            self.last_payment_date = last_payment.payment_date
        
        # Get last ticket date
        last_ticket = self.tickets.order_by(Ticket.created_at.desc()).first()
        if last_ticket:
            self.last_ticket_date = last_ticket.created_at
        
        # Calculate total charges from payments
        total_paid = db.session.query(db.func.sum(Payment.amount))\
            .filter(Payment.customer_id == self.id)\
            .scalar() or 0.0
        self.total_charges = total_paid
    
    @staticmethod
    def find_by_crm_id(company_id, crm_customer_id):
        """Find customer by CRM ID within a company"""
        return Customer.query.filter_by(
            company_id=company_id,
            crm_customer_id=crm_customer_id
        ).first()
    
    @staticmethod
    def get_active_customers(company_id):
        """Get all active customers for a company"""
        return Customer.query.filter_by(
            company_id=company_id,
            status='active'
        ).all()
    
    @staticmethod
    def get_high_risk_customers(company_id, limit=None):
        """Get high-risk customers"""
        query = Customer.query.filter_by(
            company_id=company_id,
            churn_risk='high'
        ).order_by(Customer.churn_probability.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()