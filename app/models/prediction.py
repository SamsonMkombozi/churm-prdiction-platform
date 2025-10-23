"""
Fixed Prediction Model with Better Error Handling
app/models/prediction.py

Database model for storing churn predictions with fallbacks for missing columns
"""
from app.extensions import db
from datetime import datetime
import json

# Handle JSON column types for different databases
try:
    from sqlalchemy.dialects.postgresql import JSON
except ImportError:
    from sqlalchemy import Text as JSON


class Prediction(db.Model):
    """Model for storing customer churn predictions"""
    
    __tablename__ = 'predictions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.String(100), nullable=False)  # CRM customer ID
    
    # Core prediction results (required)
    churn_probability = db.Column(db.Float, nullable=False)
    churn_risk = db.Column(db.String(20), nullable=False)  # low, medium, high
    
    # Optional fields with defaults (for backward compatibility)
    confidence = db.Column(db.String(20), default='medium')  # low, medium, high
    model_version = db.Column(db.String(50), default='1.0.0')
    model_type = db.Column(db.String(100), default='RandomForest')
    
    # JSON fields (can be NULL)
    risk_factors = db.Column(JSON)  # List of risk factors
    feature_values = db.Column(JSON)  # Raw feature values used
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
            'confidence': getattr(self, 'confidence', 'medium'),
            'model_version': getattr(self, 'model_version', '1.0.0'),
            'model_type': getattr(self, 'model_type', 'RandomForest'),
            'risk_factors': self.get_risk_factors(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if getattr(self, 'updated_at', None) else None
        }
    
    def get_risk_factors(self):
        """Safely get risk factors as list"""
        try:
            if hasattr(self, 'risk_factors') and self.risk_factors:
                if isinstance(self.risk_factors, str):
                    return json.loads(self.risk_factors)
                return self.risk_factors
        except:
            pass
        return []
    
    def get_feature_values(self):
        """Safely get feature values as dict"""
        try:
            if hasattr(self, 'feature_values') and self.feature_values:
                if isinstance(self.feature_values, str):
                    return json.loads(self.feature_values)
                return self.feature_values
        except:
            pass
        return {}
    
    @classmethod
    def create_prediction(cls, company_id, customer_id, prediction_result):
        """
        Create a new prediction record safely
        
        Args:
            company_id: Company ID
            customer_id: Customer ID from CRM
            prediction_result: Dictionary with prediction results
            
        Returns:
            Created Prediction instance
        """
        # Extract required fields
        churn_probability = prediction_result.get('churn_probability', 0.0)
        churn_risk = prediction_result.get('churn_risk', 'medium')
        
        # Create base prediction
        prediction_data = {
            'company_id': company_id,
            'customer_id': str(customer_id),
            'churn_probability': float(churn_probability),
            'churn_risk': churn_risk
        }
        
        # Add optional fields if they exist in the model
        optional_fields = {
            'confidence': prediction_result.get('confidence', 'medium'),
            'model_version': prediction_result.get('model_version', '1.0.0'),
            'model_type': prediction_result.get('model_type', 'RandomForest'),
            'risk_factors': prediction_result.get('risk_factors', []),
            'feature_values': prediction_result.get('feature_values', {})
        }
        
        # Only add fields that exist in the database schema
        for field, value in optional_fields.items():
            if hasattr(cls, field):
                prediction_data[field] = value
        
        try:
            prediction = cls(**prediction_data)
            db.session.add(prediction)
            db.session.commit()
            return prediction
        except Exception as e:
            db.session.rollback()
            # Try with minimal data if full creation fails
            minimal_prediction = cls(
                company_id=company_id,
                customer_id=str(customer_id),
                churn_probability=float(churn_probability),
                churn_risk=churn_risk
            )
            db.session.add(minimal_prediction)
            db.session.commit()
            return minimal_prediction
    
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
        
        try:
            result = db.session.query(
                cls.churn_risk,
                func.count(cls.id).label('count')
            ).filter_by(
                company_id=company_id
            ).group_by(cls.churn_risk).all()
            
            return {risk: count for risk, count in result}
        except Exception as e:
            # Return empty distribution if query fails
            return {'low': 0, 'medium': 0, 'high': 0}

    @classmethod
    def safe_query(cls, company_id):
        """Create a safe query that handles missing columns"""
        try:
            # Try to query with all columns
            return cls.query.filter_by(company_id=company_id)
        except Exception as e:
            # If that fails, query only core columns
            from sqlalchemy import select
            core_columns = [cls.id, cls.company_id, cls.customer_id, 
                          cls.churn_probability, cls.churn_risk, cls.created_at]
            return db.session.query(*core_columns).filter_by(company_id=company_id)