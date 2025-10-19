"""
Fixed Prediction Model
app/models/prediction.py

Database model for storing churn predictions
"""
from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Prediction(db.Model):
    """Model for storing customer churn predictions"""
    
    __tablename__ = 'predictions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.String(100), nullable=False)  # CRM customer ID
    
    # Prediction results
    churn_probability = db.Column(db.Float, nullable=False)
    churn_risk = db.Column(db.String(20), nullable=False)  # low, medium, high
    confidence = db.Column(db.String(20))  # low, medium, high
    
    # Model information
    model_version = db.Column(db.String(50))
    model_type = db.Column(db.String(100))
    
    # Additional data
    risk_factors = db.Column(JSON)  # List of risk factors
    feature_values = db.Column(JSON)  # Raw feature values used
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = db.relationship('Company', backref='predictions')
    
    def __repr__(self):
        return f'<Prediction {self.id}: Customer {self.customer_id} - {self.churn_risk} risk>'
    
    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'customer_id': self.customer_id,
            'churn_probability': self.churn_probability,
            'churn_risk': self.churn_risk,
            'confidence': self.confidence,
            'model_version': self.model_version,
            'model_type': self.model_type,
            'risk_factors': self.risk_factors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_prediction(cls, company_id, customer_id, prediction_result):
        """
        Create a new prediction record
        
        Args:
            company_id: Company ID
            customer_id: Customer ID from CRM
            prediction_result: Dictionary with prediction results
            
        Returns:
            Created Prediction instance
        """
        prediction = cls(
            company_id=company_id,
            customer_id=str(customer_id),
            churn_probability=prediction_result.get('churn_probability', 0.0),
            churn_risk=prediction_result.get('churn_risk', 'medium'),
            confidence=prediction_result.get('confidence', 'low'),
            model_version=prediction_result.get('model_version', '1.0.0'),
            model_type=prediction_result.get('model_type', 'Unknown'),
            risk_factors=prediction_result.get('risk_factors', []),
            feature_values=prediction_result.get('feature_values', {})
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        return prediction
    
    @classmethod
    def get_latest_for_customer(cls, company_id, customer_id):
        """Get the latest prediction for a customer"""
        return cls.query.filter_by(
            company_id=company_id,
            customer_id=str(customer_id)
        ).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_company_predictions(cls, company_id, limit=100):
        """Get recent predictions for a company"""
        return cls.query.filter_by(
            company_id=company_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_risk_distribution(cls, company_id):
        """Get distribution of risk levels for a company"""
        from sqlalchemy import func
        
        result = db.session.query(
            cls.churn_risk,
            func.count(cls.id).label('count')
        ).filter_by(
            company_id=company_id
        ).group_by(cls.churn_risk).all()
        
        return {risk: count for risk, count in result}