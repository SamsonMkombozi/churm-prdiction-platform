"""
Fixed Prediction Model - Includes predicted_at column
app/models/prediction.py

Replace your existing prediction.py model with this version
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
    
    # ✅ FIX: Add will_churn column (boolean prediction result)
    will_churn = db.Column(db.Boolean, nullable=False, default=False)
    
    # ✅ FIX: Add predicted_at column that the database expects
    predicted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
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
            'will_churn': self.will_churn,
            'predicted_at': self.predicted_at.isoformat() if self.predicted_at else None,
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
        ✅ FIXED: Now includes predicted_at and will_churn calculation
        
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
        
        # ✅ FIX: Calculate will_churn based on probability threshold
        will_churn = churn_probability > 0.5  # True if >50% chance of churn
        
        # ✅ FIX: Set predicted_at timestamp
        predicted_at = prediction_result.get('prediction_date', datetime.utcnow())
        if not isinstance(predicted_at, datetime):
            predicted_at = datetime.utcnow()
        
        # Create base prediction
        prediction_data = {
            'company_id': company_id,
            'customer_id': str(customer_id),
            'churn_probability': float(churn_probability),
            'churn_risk': churn_risk,
            'will_churn': will_churn,
            'predicted_at': predicted_at  # ✅ FIX: Include predicted_at
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
            # ✅ Enhanced error handling with predicted_at
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create prediction: {e}")
            logger.error(f"Prediction data: {prediction_data}")
            
            # Try with minimal data if full creation fails
            try:
                minimal_prediction = cls(
                    company_id=company_id,
                    customer_id=str(customer_id),
                    churn_probability=float(churn_probability),
                    churn_risk=churn_risk,
                    will_churn=will_churn,
                    predicted_at=predicted_at  # ✅ Include in minimal version too
                )
                db.session.add(minimal_prediction)
                db.session.commit()
                return minimal_prediction
            except Exception as e2:
                logger.error(f"Minimal prediction creation also failed: {e2}")
                db.session.rollback()
                return None
    
    @classmethod
    def get_latest_for_customer(cls, company_id, customer_id):
        """Get the latest prediction for a customer"""
        return cls.query.filter_by(
            company_id=company_id,
            customer_id=str(customer_id)
        ).order_by(cls.predicted_at.desc()).first()
    
    @classmethod
    def get_company_predictions(cls, company_id, limit=100):
        """Get recent predictions for a company"""
        return cls.query.filter_by(
            company_id=company_id
        ).order_by(cls.predicted_at.desc()).limit(limit).all()
    
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
                          cls.churn_probability, cls.churn_risk, cls.will_churn, 
                          cls.predicted_at, cls.created_at]
            return db.session.query(*core_columns).filter_by(company_id=company_id)
    
    @classmethod
    def get_churn_predictions(cls, company_id, will_churn=True):
        """Get predictions for customers who will/won't churn"""
        return cls.query.filter_by(
            company_id=company_id,
            will_churn=will_churn
        ).all()
    
    @classmethod
    def get_accuracy_stats(cls, company_id):
        """Get accuracy statistics for predictions"""
        from sqlalchemy import func
        
        try:
            stats = db.session.query(
                func.count(cls.id).label('total'),
                func.sum(func.cast(cls.will_churn, db.Integer)).label('predicted_churn'),
                func.avg(cls.churn_probability).label('avg_probability')
            ).filter_by(company_id=company_id).first()
            
            return {
                'total_predictions': stats.total or 0,
                'predicted_churn_count': stats.predicted_churn or 0,
                'predicted_churn_rate': (stats.predicted_churn / stats.total * 100) if stats.total else 0,
                'average_probability': round(stats.avg_probability or 0, 3)
            }
        except Exception as e:
            return {
                'total_predictions': 0,
                'predicted_churn_count': 0,
                'predicted_churn_rate': 0,
                'average_probability': 0
            }

    @classmethod
    def get_predictions_by_date_range(cls, company_id, start_date, end_date):
        """Get predictions within a date range"""
        return cls.query.filter(
            cls.company_id == company_id,
            cls.predicted_at >= start_date,
            cls.predicted_at <= end_date
        ).all()
    
    @classmethod
    def get_recent_predictions(cls, company_id, days=30):
        """Get predictions from the last N days"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(
            cls.company_id == company_id,
            cls.predicted_at >= start_date
        ).order_by(cls.predicted_at.desc()).all()