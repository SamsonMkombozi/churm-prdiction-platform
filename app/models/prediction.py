"""
Prediction Model - Stores prediction history
app/models/prediction.py
"""
from datetime import datetime
from app.extensions import db


class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    # Prediction Results
    churn_probability = db.Column(db.Float, nullable=False)
    churn_risk = db.Column(db.String(20), nullable=False)  # low, medium, high
    will_churn = db.Column(db.Boolean, nullable=False)
    
    # Model Information
    model_version = db.Column(db.String(50))
    features_used = db.Column(db.Text)  # JSON string of features
    
    # Metadata
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    prediction_batch_id = db.Column(db.String(100))  # Group predictions together
    
    # Indexes
    __table_args__ = (
        db.Index('idx_prediction_company_customer', 'company_id', 'customer_id'),
        db.Index('idx_prediction_risk', 'company_id', 'churn_risk'),
        db.Index('idx_prediction_date', 'company_id', 'predicted_at'),
    )
    
    def __repr__(self):
        return f'<Prediction {self.customer_id} - {self.churn_risk} ({self.churn_probability:.2f})>'
    
    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'churn_probability': self.churn_probability,
            'churn_risk': self.churn_risk,
            'will_churn': self.will_churn,
            'model_version': self.model_version,
            'predicted_at': self.predicted_at.isoformat() if self.predicted_at else None,
        }
    
    @staticmethod
    def get_latest_for_customer(company_id, customer_id):
        """Get the most recent prediction for a customer"""
        return Prediction.query.filter_by(
            company_id=company_id,
            customer_id=customer_id
        ).order_by(Prediction.predicted_at.desc()).first()
    
    @staticmethod
    def get_high_risk_count(company_id):
        """Count high-risk predictions"""
        return Prediction.query.filter_by(
            company_id=company_id,
            churn_risk='high'
        ).count()