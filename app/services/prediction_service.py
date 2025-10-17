import pandas as pd
import numpy as np
from datetime import datetime
import logging
import traceback
import os
import joblib
from typing import Dict, List, Any, Optional

from app.controllers.crm_controller import customer_detail
from app.ml.models.churn_model import ChurnModel
from app.ml.features.feature_engineering import FeatureEngineering

logger = logging.getLogger(__name__)

class ChurnPredictionService:
    """Service for handling real churn prediction operations"""
    
    def __init__(self):
        self.model = None
        self.feature_engineer = None
        self.is_trained = False
        self.model_path = "app/ml/models/saved/churn_xgboost.pkl"
        
        # Try to load the trained model
        self._load_model()
    
    def _load_model(self):
        """Load the trained XGBoost model"""
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading trained model from: {self.model_path}")
                
                # Load model data
                model_data = joblib.load(self.model_path)
                
                # Initialize ChurnModel and set the loaded model
                self.model = ChurnModel()
                self.model.model = model_data['model']
                self.model.feature_names = model_data['feature_names']
                self.model.version = model_data.get('version')
                self.model.trained_at = model_data.get('trained_at')
                self.model.metrics = model_data.get('metrics', {})
                
                # Initialize feature engineering
                self.feature_engineer = FeatureEngineering()
                
                self.is_trained = True
                logger.info(f"✅ Model loaded successfully. Version: {self.model.version}")
                logger.info(f"Model accuracy: {self.model.metrics.get('accuracy', 'N/A')}")
                
            else:
                logger.warning(f"❌ Trained model not found at: {self.model_path}")
                logger.warning("Using fallback rule-based predictions")
                self.is_trained = False
                
        except Exception as e:
            logger.error(f"❌ Error loading model: {str(e)}")
            logger.error(traceback.format_exc())
            self.is_trained = False
    
    def predict_customer_churn(self, customer_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict churn for a single customer using the trained ML model
        
        Args:
            customer_detail: Dictionary with customer information
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if self.is_trained and self.model:
                return self._predict_with_ml_model(customer_detail)
            else:
                return self._predict_with_rules(customer_detail)
                
        except Exception as e:
            logger.error(f"Error predicting customer churn: {str(e)}")
            return {
                'customer_id': customer_detail.get('id', 'unknown'),
                'churn_probability': 0.5,
                'churn_risk': 'unknown',
                'will_churn': False,
                'prediction_method': 'error',
                'error': str(e),
                'predicted_at': datetime.utcnow().isoformat()
            }
    
    def _predict_with_ml_model(self, customer_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Use the trained XGBoost model for prediction"""
        try:
            # Convert customer data to DataFrame
            df = pd.DataFrame([customer_detail])
            
            # Engineer features using the same process as training
            features_df = self._engineer_features_for_prediction(df)
            
            # Get prediction from the trained model
            churn_probability = self.model.predict_proba(features_df)[0]
            
            # Determine risk level and prediction
            risk_level = self._categorize_risk(churn_probability)
            will_churn = churn_probability >= 0.5
            
            return {
                'customer_id': customer_detail.get('id', customer_detail.get('customer_id')),
                'churn_probability': float(churn_probability),
                'churn_risk': risk_level,
                'will_churn': will_churn,
                'prediction_method': 'ml_model',
                'model_version': self.model.version,
                'confidence': self._calculate_confidence(churn_probability),
                'predicted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            # Fallback to rule-based prediction
            return self._predict_with_rules(customer_detail)
    
    def _engineer_features_for_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for prediction using the same process as training"""
        try:
            # Map customer data fields to expected feature names
            features_df = df.copy()
            
            # Basic customer features
            features_df['tenure_months'] = df.get('tenure_months', 0)
            features_df['monthly_charges'] = df.get('monthly_charges', 0)
            features_df['total_charges'] = df.get('total_charges', 0)
            features_df['outstanding_balance'] = df.get('outstanding_balance', 0)
            
            # Engagement features
            features_df['total_tickets'] = df.get('total_tickets', 0)
            features_df['total_payments'] = df.get('total_payments', 0)
            
            # Derived features
            features_df['balance_ratio'] = np.where(
                features_df['monthly_charges'] > 0,
                features_df['outstanding_balance'] / features_df['monthly_charges'],
                0
            )
            
            features_df['is_new_customer'] = (features_df['tenure_months'] < 3).astype(int)
            features_df['is_long_term_customer'] = (features_df['tenure_months'] > 24).astype(int)
            features_df['is_high_spender'] = (features_df['monthly_charges'] > features_df['monthly_charges'].median()).astype(int)
            
            # Ticket and payment rates
            features_df['ticket_rate'] = np.where(
                features_df['tenure_months'] > 0,
                features_df['total_tickets'] / features_df['tenure_months'],
                0
            )
            
            features_df['payment_rate'] = np.where(
                features_df['tenure_months'] > 0,
                features_df['total_payments'] / features_df['tenure_months'],
                0
            )
            
            # Health and engagement scores
            features_df['engagement_score'] = (
                features_df['total_payments'] * 0.6 +
                features_df['total_tickets'] * 0.4
            ) / (features_df['tenure_months'] + 1)
            
            features_df['health_score'] = np.clip(
                40 - (features_df['outstanding_balance'] / (features_df['monthly_charges'] + 1)) * 20 +
                30 - features_df['total_tickets'] * 3 +
                30 * (features_df['total_payments'] / (features_df['tenure_months'] + 1)),
                0, 100
            )
            
            # Risk indicators
            features_df['has_outstanding_balance'] = (features_df['outstanding_balance'] > 0).astype(int)
            features_df['has_open_tickets'] = 0  # We don't have this info easily
            features_df['late_payer'] = (features_df['balance_ratio'] > 2).astype(int)
            
            # Ensure all model features exist
            if self.model and self.model.feature_names:
                for feature in self.model.feature_names:
                    if feature not in features_df.columns:
                        features_df[feature] = 0
                
                # Select only the features the model was trained on
                features_df = features_df[self.model.feature_names]
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error engineering features: {str(e)}")
            # Return minimal feature set
            minimal_features = pd.DataFrame({
                'tenure_months': [customer_detail.get('tenure_months', 0)],
                'monthly_charges': [customer_detail.get('monthly_charges', 0)],
                'total_charges': [customer_detail.get('total_charges', 0)],
                'outstanding_balance': [customer_detail.get('outstanding_balance', 0)],
                'total_tickets': [customer_detail.get('total_tickets', 0)],
                'total_payments': [customer_detail.get('total_payments', 0)]
            })
            return minimal_features
    
    def _predict_with_rules(self, customer_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based prediction when ML model is not available"""
        try:
            probability = 0.0
            
            # Tenure risk (shorter tenure = higher risk)
            tenure = customer_detail.get('tenure_months', 0)
            if tenure < 6:
                probability += 0.4
            elif tenure < 12:
                probability += 0.2
            elif tenure < 24:
                probability += 0.1
            
            # Payment behavior
            outstanding_balance = customer_detail.get('outstanding_balance', 0)
            monthly_charges = customer_detail.get('monthly_charges', 0)
            
            if outstanding_balance > 0 and monthly_charges > 0:
                balance_ratio = outstanding_balance / monthly_charges
                if balance_ratio > 3:
                    probability += 0.3
                elif balance_ratio > 1:
                    probability += 0.2
            
            # Support ticket activity
            total_tickets = customer_detail.get('total_tickets', 0)
            if total_tickets > 5:
                probability += 0.2
            elif total_tickets > 2:
                probability += 0.1
            
            # Payment frequency
            total_payments = customer_detail.get('total_payments', 0)
            if tenure > 0:
                payment_rate = total_payments / tenure
                if payment_rate < 0.5:  # Less than 0.5 payments per month
                    probability += 0.2
            
            # Service charges
            if monthly_charges < 20:
                probability += 0.1
            elif monthly_charges > 100:
                probability -= 0.1  # High-value customers less likely to churn
            
            # Ensure probability is between 0 and 1
            probability = max(0.0, min(1.0, probability))
            
            risk_level = self._categorize_risk(probability)
            
            return {
                'customer_id': customer_detail.get('id', customer_detail.get('customer_id')),
                'churn_probability': probability,
                'churn_risk': risk_level,
                'will_churn': probability >= 0.5,
                'prediction_method': 'rule_based',
                'confidence': 0.6,  # Lower confidence for rule-based
                'predicted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based prediction: {str(e)}")
            return {
                'customer_id': customer_detail.get('id', 'unknown'),
                'churn_probability': 0.5,
                'churn_risk': 'medium',
                'will_churn': False,
                'prediction_method': 'fallback',
                'error': str(e),
                'predicted_at': datetime.utcnow().isoformat()
            }
    
    def _categorize_risk(self, probability: float) -> str:
        """Categorize churn probability into risk levels"""
        if probability >= 0.7:
            return 'high'
        elif probability >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, probability: float) -> float:
        """Calculate prediction confidence based on probability"""
        # Higher confidence when probability is closer to 0 or 1
        confidence = 1 - (2 * abs(probability - 0.5))
        return max(0.5, confidence)  # Minimum 50% confidence
    
    def predict_batch(self, customers_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict churn for multiple customers"""
        results = []
        
        for customer_detail in customers_data:
            try:
                prediction = self.predict_customer_churn(customer_detail)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error predicting for customer {customer_detail.get('id')}: {str(e)}")
                results.append({
                    'customer_id': customer_detail.get('id', 'unknown'),
                    'churn_probability': 0.5,
                    'churn_risk': 'unknown',
                    'will_churn': False,
                    'error': str(e),
                    'predicted_at': datetime.utcnow().isoformat()
                })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.is_trained and self.model:
            return {
                'is_trained': True,
                'model_type': 'XGBoost',
                'version': self.model.version,
                'trained_at': self.model.trained_at,
                'metrics': self.model.metrics,
                'feature_count': len(self.model.feature_names) if self.model.feature_names else 0
            }
        else:
            return {
                'is_trained': False,
                'model_type': 'Rule-based fallback',
                'message': 'No trained ML model available. Using rule-based predictions.',
                'model_path': self.model_path
            }