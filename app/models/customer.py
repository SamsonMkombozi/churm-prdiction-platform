"""
Enhanced Customer Model with Disconnection-Based Churn Prediction
app/models/customer.py

🔧 ENHANCED: Added disconnection_date field for accurate churn prediction
📊 BUSINESS LOGIC: Based on actual disconnection dates from CRM
💾 STORAGE: Saves payments, tickets, usage stats from PostgreSQL

Author: Samson David - Mawingu Group
Date: November 2024
"""

from datetime import datetime, timedelta
from app.extensions import db
from sqlalchemy.orm import relationship
import json

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic customer information
    customer_name = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200))  # Alias for backward compatibility
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Company relationship
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # 🔧 NEW: CRM Integration fields
    crm_customer_id = db.Column(db.String(50), index=True)  # ID from PostgreSQL CRM
    external_id = db.Column(db.String(50), unique=True)     # Backward compatibility
    customer_no = db.Column(db.String(50), index=True)      # For CRM integration
    
    # 📅 CRITICAL: Disconnection tracking for churn prediction
    disconnection_date = db.Column(db.DateTime)  # 🔧 NEW: From crm_customers.churned_date
    signup_date = db.Column(db.DateTime)
    date_installed = db.Column(db.DateTime)  # From CRM
    
    # Status and account info
    status = db.Column(db.String(20), default='active')
    connection_status = db.Column(db.String(50))  # From CRM
    account_type = db.Column(db.String(50), default='personal')
    service_plan = db.Column(db.String(100), default='Standard')
    
    # 💰 Financial information
    monthly_charges = db.Column(db.Float, default=0.0)
    total_charges = db.Column(db.Float, default=0.0)
    outstanding_balance = db.Column(db.Float, default=0.0)
    account_value = db.Column(db.Float, default=0.0)  # Backward compatibility
    
    # 📊 Service metrics and aggregations from PostgreSQL
    tenure_months = db.Column(db.Float, default=0.0)
    
    # 💳 Payment data (aggregated from nav_mpesa_transactions)
    total_payments = db.Column(db.Integer, default=0)
    successful_payments = db.Column(db.Integer, default=0)
    failed_payments = db.Column(db.Integer, default=0)
    total_paid_amount = db.Column(db.Float, default=0.0)
    last_payment_date = db.Column(db.DateTime)
    days_since_last_payment = db.Column(db.Integer, default=0)
    payment_consistency_score = db.Column(db.Float, default=1.0)
    
    # 🎫 Support tickets data (aggregated from crm_tickets)
    total_tickets = db.Column(db.Integer, default=0)
    open_tickets = db.Column(db.Integer, default=0)
    complaint_tickets = db.Column(db.Integer, default=0)
    
    # 📈 Usage statistics (aggregated from spl_statistics)
    usage_records = db.Column(db.Integer, default=0)
    avg_data_usage = db.Column(db.Float, default=0.0)  # MB per day
    total_data_consumed = db.Column(db.BigInteger, default=0)  # Total bytes
    
    # 🔥 ENHANCED: Disconnection-based churn prediction fields
    churn_probability = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    churn_risk = db.Column(db.String(20), default='unknown')  # low, medium, high, unknown
    days_since_disconnection = db.Column(db.Integer, default=0)  # 🔧 NEW: Key metric
    disconnection_risk_level = db.Column(db.String(20))  # 🔧 NEW: Based on disconnection
    last_prediction_date = db.Column(db.DateTime)
    prediction_reasoning = db.Column(db.Text)  # JSON string of risk factors
    
    # Legacy prediction fields (backward compatibility)
    churn_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)  # Last sync from PostgreSQL
    
    # Relationships
    company = db.relationship('Company', back_populates='customers')
    tickets = db.relationship('Ticket', back_populates='customer', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='customer', lazy='dynamic')
    predictions = db.relationship('Prediction', back_populates='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.customer_name} ({self.crm_customer_id})>'
    
    @property
    def display_name(self):
        """Get display name with fallback"""
        return self.customer_name or self.name or f'Customer {self.id}'
    
    # 🔥 ENHANCED: Disconnection-based churn prediction methods
    
    def calculate_disconnection_churn_risk(self):
        """
        Calculate churn risk based on disconnection date and payment behavior
        Business Logic:
        - HIGH: 90+ days after disconnection with no new payments
        - MEDIUM: 60+ days after disconnection with no/inconsistent payments  
        - LOW: Recent disconnection or good payment behavior
        """
        
        current_date = datetime.utcnow()
        
        # Initialize risk assessment
        risk_assessment = {
            'risk_level': 'low',
            'probability': 0.1,
            'reasoning': [],
            'days_since_disconnection': 0,
            'disconnection_status': 'active'
        }
        
        # Check if customer is disconnected
        if self.disconnection_date:
            days_disconnected = (current_date - self.disconnection_date).days
            risk_assessment['days_since_disconnection'] = days_disconnected
            risk_assessment['disconnection_status'] = 'disconnected'
            
            # Get payment behavior after disconnection
            payments_after_disconnection = self._count_payments_after_disconnection()
            
            # HIGH RISK: 90+ days disconnected with no new payments
            if days_disconnected >= 90:
                if payments_after_disconnection == 0:
                    risk_assessment['risk_level'] = 'high'
                    risk_assessment['probability'] = min(0.8 + (days_disconnected - 90) / 365, 0.95)
                    risk_assessment['reasoning'].append(f"Disconnected for {days_disconnected} days with no payments (>90 days)")
                else:
                    # Has payments but still disconnected - medium risk
                    risk_assessment['risk_level'] = 'medium'
                    risk_assessment['probability'] = 0.6
                    risk_assessment['reasoning'].append(f"Disconnected for {days_disconnected} days despite {payments_after_disconnection} payments")
            
            # MEDIUM RISK: 60+ days disconnected OR inconsistent payments
            elif days_disconnected >= 60:
                if payments_after_disconnection == 0:
                    risk_assessment['risk_level'] = 'medium'
                    risk_assessment['probability'] = 0.5 + (days_disconnected - 60) / 300
                    risk_assessment['reasoning'].append(f"Disconnected for {days_disconnected} days with no payments (60-90 days)")
                elif payments_after_disconnection < 3 or self.payment_consistency_score < 0.7:
                    risk_assessment['risk_level'] = 'medium'
                    risk_assessment['probability'] = 0.4
                    risk_assessment['reasoning'].append(f"Disconnected for {days_disconnected} days with inconsistent payments")
                else:
                    # Good payment behavior despite disconnection - lower risk
                    risk_assessment['risk_level'] = 'low'
                    risk_assessment['probability'] = 0.25
                    risk_assessment['reasoning'].append(f"Disconnected but maintaining good payment behavior")
            
            # RECENT DISCONNECTION: < 60 days
            else:
                if payments_after_disconnection > 0:
                    risk_assessment['risk_level'] = 'low'
                    risk_assessment['probability'] = 0.15
                    risk_assessment['reasoning'].append(f"Recently disconnected ({days_disconnected} days) but making payments")
                else:
                    risk_assessment['risk_level'] = 'medium'
                    risk_assessment['probability'] = 0.35
                    risk_assessment['reasoning'].append(f"Recently disconnected ({days_disconnected} days) with no payments")
        
        else:
            # Customer is not disconnected - use payment-based logic
            if self.days_since_last_payment >= 90:
                risk_assessment['risk_level'] = 'high'
                risk_assessment['probability'] = 0.7
                risk_assessment['reasoning'].append(f"Not disconnected but no payments for {self.days_since_last_payment} days")
            elif self.days_since_last_payment >= 60:
                risk_assessment['risk_level'] = 'medium'  
                risk_assessment['probability'] = 0.4
                risk_assessment['reasoning'].append(f"Not disconnected but no payments for {self.days_since_last_payment} days")
            elif self.total_payments == 0:
                risk_assessment['risk_level'] = 'high'
                risk_assessment['probability'] = 0.8
                risk_assessment['reasoning'].append("Never disconnected but no payment history")
            else:
                risk_assessment['risk_level'] = 'low'
                risk_assessment['probability'] = 0.1
                risk_assessment['reasoning'].append("Active customer with good payment behavior")
        
        return risk_assessment
    
    def _count_payments_after_disconnection(self):
        """Count payments made after disconnection date"""
        if not self.disconnection_date:
            return self.total_payments or 0
        
        # This would ideally query Payment model, but we can estimate from aggregated data
        if self.last_payment_date and self.last_payment_date > self.disconnection_date:
            # Estimate based on recent payment activity
            days_between = (self.last_payment_date - self.disconnection_date).days
            if days_between <= 30:
                return min(self.total_payments, 3)  # Conservative estimate
            else:
                return min(self.total_payments, 1)  # At least one recent payment
        return 0
    
    def update_churn_prediction(self):
        """Update churn prediction based on disconnection and payment data"""
        
        risk_assessment = self.calculate_disconnection_churn_risk()
        
        # Update prediction fields
        self.churn_risk = risk_assessment['risk_level']
        self.churn_probability = risk_assessment['probability']
        self.days_since_disconnection = risk_assessment['days_since_disconnection']
        self.disconnection_risk_level = risk_assessment['disconnection_status']
        self.prediction_reasoning = json.dumps(risk_assessment['reasoning'])
        self.last_prediction_date = datetime.utcnow()
        
        # Update legacy fields for backward compatibility
        self.churn_score = risk_assessment['probability']
        self.risk_level = risk_assessment['risk_level']
        
        return risk_assessment
    
    # Display helper properties
    
    @property
    def risk_badge_class(self):
        """Return Bootstrap badge class for risk level"""
        risk_classes = {
            'high': 'bg-danger',
            'medium': 'bg-warning', 
            'low': 'bg-success',
            'unknown': 'bg-secondary'
        }
        return risk_classes.get(self.churn_risk, 'bg-secondary')
    
    @property
    def risk_percentage(self):
        """Return risk as percentage string"""
        if self.churn_probability:
            return f"{self.churn_probability * 100:.1f}%"
        return "N/A"
    
    @property
    def disconnection_status_display(self):
        """Human-readable disconnection status"""
        if not self.disconnection_date:
            return "Active"
        
        days = self.days_since_disconnection
        if days == 0:
            return "Recently Disconnected"
        elif days < 30:
            return f"Disconnected {days} days ago"
        elif days < 90:
            return f"Disconnected {days} days ago (⚠️ Medium Risk)"
        else:
            return f"Disconnected {days} days ago (🚨 High Risk)"
    
    @property
    def needs_prediction(self):
        """Check if customer needs new prediction"""
        if not self.last_prediction_date:
            return True
        
        # Update prediction if older than 24 hours
        time_since_prediction = datetime.utcnow() - self.last_prediction_date
        return time_since_prediction.days >= 1
    
    @property
    def payment_behavior_summary(self):
        """Get payment behavior summary"""
        if self.total_payments == 0:
            return "No Payments"
        elif self.payment_consistency_score >= 0.8:
            return "Good Payer"
        elif self.payment_consistency_score >= 0.6:
            return "Moderate Payer"
        else:
            return "Poor Payer"
    
    # Data export and API methods
    
    def to_dict(self):
        """Convert customer to dictionary for API responses"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'crm_customer_id': self.crm_customer_id,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'disconnection_date': self.disconnection_date.isoformat() if self.disconnection_date else None,
            'days_since_disconnection': self.days_since_disconnection,
            'monthly_charges': self.monthly_charges,
            'total_charges': self.total_charges,
            'outstanding_balance': self.outstanding_balance,
            'total_payments': self.total_payments,
            'total_tickets': self.total_tickets,
            'churn_probability': self.churn_probability,
            'churn_risk': self.churn_risk,
            'disconnection_risk_level': self.disconnection_risk_level,
            'payment_behavior': self.payment_behavior_summary,
            'last_prediction_date': self.last_prediction_date.isoformat() if self.last_prediction_date else None,
            'prediction_reasoning': json.loads(self.prediction_reasoning) if self.prediction_reasoning else []
        }
    
    def to_prediction_dict(self):
        """Convert customer data for prediction model input"""
        return {
            'customer_id': self.crm_customer_id or str(self.id),
            'customer_name': self.customer_name,
            'tenure_months': self.tenure_months or 0,
            'monthly_charges': self.monthly_charges or 0,
            'total_charges': self.total_charges or 0,
            'total_payments': self.total_payments or 0,
            'successful_payments': self.successful_payments or 0,
            'failed_payments': self.failed_payments or 0,
            'days_since_last_payment': self.days_since_last_payment or 0,
            'total_tickets': self.total_tickets or 0,
            'complaint_tickets': self.complaint_tickets or 0,
            'avg_data_usage': self.avg_data_usage or 0,
            'disconnection_date': self.disconnection_date.isoformat() if self.disconnection_date else None,
            'days_since_disconnection': self.days_since_disconnection or 0,
            'payment_consistency_score': self.payment_consistency_score or 1.0
        }
    
    # Static methods for bulk operations
    
    @staticmethod
    def get_high_risk_customers(company_id, limit=50):
        """Get customers with high churn risk"""
        return Customer.query.filter_by(
            company_id=company_id,
            churn_risk='high'
        ).order_by(Customer.churn_probability.desc()).limit(limit).all()
    
    @staticmethod
    def get_disconnected_customers(company_id, days_threshold=90):
        """Get customers disconnected for more than threshold days"""
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        return Customer.query.filter(
            Customer.company_id == company_id,
            Customer.disconnection_date <= threshold_date
        ).order_by(Customer.disconnection_date.asc()).all()
    
    @staticmethod
    def get_prediction_summary(company_id):
        """Get prediction summary for company dashboard"""
        from sqlalchemy import func
        
        summary = db.session.query(
            Customer.churn_risk,
            func.count(Customer.id).label('count'),
            func.avg(Customer.churn_probability).label('avg_probability')
        ).filter_by(company_id=company_id).group_by(Customer.churn_risk).all()
        
        result = {
            'total_customers': Customer.query.filter_by(company_id=company_id).count(),
            'risk_distribution': {},
            'disconnected_customers': Customer.query.filter(
                Customer.company_id == company_id,
                Customer.disconnection_date.isnot(None)
            ).count()
        }
        
        for risk, count, avg_prob in summary:
            result['risk_distribution'][risk] = {
                'count': count,
                'avg_probability': float(avg_prob) if avg_prob else 0.0
            }
        
        return result