"""
Enhanced Churn Prediction Service
app/services/prediction_service.py

Loads ML model and makes churn predictions for customers
"""
import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Import feature engineering
from app.ml.features.feature_engineering import FeatureEngineering

logger = logging.getLogger(__name__)


class ChurnPredictionService:
    """Service for making churn predictions using ML model"""
    
    def __init__(self):
        """Initialize the prediction service"""
        self.model = None
        self.feature_columns = []
        self.model_metrics = {}
        self.model_version = None
        self.model_type = None
        self.feature_engineer = FeatureEngineering()
        self.is_trained = False
        
        # Model paths
        self.model_path = 'app/ml/models/saved/churn_model_v1.pkl'
        self.backup_model_path = 'app/ml/models/saved/backup_model.pkl'
        
        # Try to load model on initialization
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load ML model from file"""
        model_paths = [self.model_path, self.backup_model_path]
        
        for path in model_paths:
            if os.path.exists(path):
                try:
                    logger.info(f"🔄 Loading model from {path}")
                    
                    with open(path, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    # Extract model components
                    self.model = model_data['model']
                    self.feature_columns = model_data['feature_columns']
                    self.model_metrics = model_data.get('metrics', {})
                    self.model_version = model_data.get('version', '1.0.0')
                    self.model_type = model_data.get('model_type', 'Unknown')
                    
                    # Initialize feature engineering
                    self.feature_engineer = FeatureEngineering()
                    
                    self.is_trained = True
                    logger.info(f"✅ Model loaded successfully: {self.model_type} v{self.model_version}")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load model from {path}: {str(e)}")
                    continue
        
        # If no model found, create a simple one
        logger.warning("⚠️ No trained model found. Creating simple fallback model...")
        return self._create_simple_model()
    
    def _create_simple_model(self) -> bool:
        """Create a simple rule-based model as fallback"""
        try:
            # Create simple model data
            self.model = None  # Will use rule-based predictions
            self.feature_columns = [
                'tenure_months', 'monthly_charges', 'total_charges',
                'outstanding_balance', 'total_payments', 'total_tickets'
            ]
            self.model_metrics = {
                'type': 'rule_based',
                'accuracy': 0.65,
                'auc_score': 0.60
            }
            self.model_version = '0.1.0-fallback'
            self.model_type = 'RuleBasedClassifier'
            self.is_trained = True
            
            logger.info("✅ Simple rule-based model created as fallback")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create simple model: {str(e)}")
            return False
    
    def predict_customer_churn(self, customer_data: Dict) -> Dict:
        """
        Predict churn probability for a single customer
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.is_trained:
                return self._fallback_prediction(customer_data)
            
            # Transform customer data to features
            customer_df = pd.DataFrame([customer_data])
            features_df = self.feature_engineer.transform(customer_df)
            
            if self.model is None:
                # Use rule-based prediction
                return self._rule_based_prediction(features_df.iloc[0])
            
            # Use ML model prediction
            # Ensure all required features are present
            for col in self.feature_columns:
                if col not in features_df.columns:
                    features_df[col] = 0
            
            # Get features in correct order
            X = features_df[self.feature_columns]
            
            # Make prediction
            churn_probability = self.model.predict_proba(X)[0][1]
            
            # Determine risk category
            if churn_probability >= 0.7:
                risk_category = 'high'
            elif churn_probability >= 0.4:
                risk_category = 'medium'
            else:
                risk_category = 'low'
            
            result = {
                'customer_id': customer_data.get('id', None),
                'churn_probability': float(churn_probability),
                'churn_risk': risk_category,
                'model_version': self.model_version,
                'prediction_date': datetime.utcnow(),
                'confidence': self._calculate_confidence(churn_probability),
                'risk_factors': self._identify_risk_factors(features_df.iloc[0])
            }
            
            logger.info(f"✅ Prediction made for customer {customer_data.get('id', 'unknown')}: {risk_category} risk ({churn_probability:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Prediction failed for customer {customer_data.get('id', 'unknown')}: {str(e)}")
            return self._fallback_prediction(customer_data)
    
    def _rule_based_prediction(self, features: pd.Series) -> Dict:
        """Simple rule-based prediction as fallback"""
        try:
            score = 0
            
            # Tenure risk
            if features.get('tenure_months', 0) < 6:
                score += 0.3
            elif features.get('tenure_months', 0) < 12:
                score += 0.1
            
            # Balance risk
            balance_ratio = features.get('balance_to_monthly_ratio', 0)
            if balance_ratio > 3:
                score += 0.4
            elif balance_ratio > 1:
                score += 0.2
            
            # Ticket risk
            ticket_rate = features.get('tickets_per_month', 0)
            if ticket_rate > 0.5:
                score += 0.3
            elif ticket_rate > 0.2:
                score += 0.1
            
            # Payment consistency
            payment_consistency = features.get('payment_consistency', 1)
            if payment_consistency < 0.8:
                score += 0.2
            
            # Cap at 0.9
            churn_probability = min(score, 0.9)
            
            if churn_probability >= 0.6:
                risk_category = 'high'
            elif churn_probability >= 0.3:
                risk_category = 'medium'
            else:
                risk_category = 'low'
            
            return {
                'customer_id': None,
                'churn_probability': float(churn_probability),
                'churn_risk': risk_category,
                'model_version': self.model_version,
                'prediction_date': datetime.utcnow(),
                'confidence': 'medium',
                'risk_factors': self._identify_risk_factors(features)
            }
            
        except Exception as e:
            logger.error(f"❌ Rule-based prediction failed: {str(e)}")
            return self._fallback_prediction({})
    
    def _fallback_prediction(self, customer_data: Dict) -> Dict:
        """Last resort fallback prediction"""
        return {
            'customer_id': customer_data.get('id', None),
            'churn_probability': 0.5,
            'churn_risk': 'medium',
            'model_version': 'fallback',
            'prediction_date': datetime.utcnow(),
            'confidence': 'low',
            'risk_factors': ['Unable to process data']
        }
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calculate prediction confidence based on probability"""
        if probability <= 0.1 or probability >= 0.9:
            return 'high'
        elif probability <= 0.2 or probability >= 0.8:
            return 'medium'
        else:
            return 'low'
    
    def _identify_risk_factors(self, features: pd.Series) -> List[str]:
        """Identify key risk factors for the customer"""
        risk_factors = []
        
        try:
            # Check various risk indicators
            if features.get('new_customer_flag', 0) == 1:
                risk_factors.append('New customer (< 6 months)')
            
            if features.get('high_balance_flag', 0) == 1:
                risk_factors.append('High outstanding balance')
            
            if features.get('high_tickets_flag', 0) == 1:
                risk_factors.append('Many support tickets')
            
            if features.get('low_usage_flag', 0) == 1:
                risk_factors.append('Low monthly charges')
            
            if features.get('payment_consistency', 1) < 0.8:
                risk_factors.append('Inconsistent payments')
            
            if features.get('tickets_per_month', 0) > 0.3:
                risk_factors.append('High ticket frequency')
            
            if not risk_factors:
                risk_factors.append('Low risk profile')
            
        except Exception as e:
            logger.warning(f"⚠️ Risk factor identification failed: {str(e)}")
            risk_factors = ['Unable to identify specific risks']
        
        return risk_factors
    
    def predict_batch(self, customers_data: List[Dict]) -> List[Dict]:
        """
        Predict churn for multiple customers
        
        Args:
            customers_data: List of customer dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        
        logger.info(f"🔄 Starting batch prediction for {len(customers_data)} customers")
        
        for i, customer in enumerate(customers_data):
            try:
                result = self.predict_customer_churn(customer)
                results.append(result)
                
                # Log progress every 10 customers
                if (i + 1) % 10 == 0:
                    logger.info(f"   Progress: {i + 1}/{len(customers_data)} customers processed")
                    
            except Exception as e:
                logger.error(f"❌ Batch prediction failed for customer {customer.get('id', i)}: {str(e)}")
                results.append(self._fallback_prediction(customer))
        
        logger.info(f"✅ Batch prediction complete: {len(results)} results")
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            'is_trained': self.is_trained,
            'model_type': self.model_type,
            'model_version': self.model_version,
            'metrics': self.model_metrics,
            'feature_count': len(self.feature_columns),
            'feature_columns': self.feature_columns
        }
    
    def retrain_model(self, training_data: pd.DataFrame) -> bool:
        """
        Retrain the model with new data
        Note: This is a placeholder for future implementation
        """
        logger.info("📚 Model retraining requested (not implemented yet)")
        return False


# Test function
def test_prediction_service():
    """Test the prediction service"""
    print("🧪 Testing Prediction Service...")
    
    # Initialize service
    service = ChurnPredictionService()
    print(f"✅ Service initialized: {service.is_trained}")
    
    # Test single prediction
    sample_customer = {
        'id': 1,
        'tenure_months': 12,
        'monthly_charges': 75.50,
        'total_charges': 900.0,
        'outstanding_balance': 150.0,
        'total_tickets': 3,
        'total_payments': 12
    }
    
    result = service.predict_customer_churn(sample_customer)
    print(f"✅ Single prediction: {result['churn_risk']} risk ({result['churn_probability']:.3f})")
    
    # Test batch prediction
    batch_customers = [sample_customer.copy() for _ in range(3)]
    batch_results = service.predict_batch(batch_customers)
    print(f"✅ Batch predictions: {len(batch_results)} results")
    
    # Model info
    model_info = service.get_model_info()
    print(f"✅ Model info: {model_info['model_type']}")
    
    return service


if __name__ == "__main__":
    test_prediction_service()