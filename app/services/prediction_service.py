"""
Prediction Service - Makes churn predictions using trained model
app/services/prediction_service.py
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

from app.extensions import db
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.payment import Payment
from app.models.company import Company
from app.ml.features.feature_engineering import FeatureEngineering
from app.ml.models.churn_model import ChurnModel

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for making churn predictions"""
    
    def __init__(self, company: Company):
        """
        Initialize prediction service
        
        Args:
            company: Company instance
        """
        self.company = company
        self.feature_engineer = FeatureEngineering()
        self.model = None
        self._load_model()
    
    def _load_model(self) -> bool:
        """
        Load trained model for company
        
        Returns:
            True if model loaded successfully
        """
        model_dir = os.path.join(
            os.path.dirname(__file__), 
            '../ml/models/saved'
        )
        model_path = os.path.join(
            model_dir, 
            f'churn_model_company_{self.company.id}.joblib'
        )
        
        if not os.path.exists(model_path):
            logger.warning(f"No trained model found for company {self.company.id}")
            return False
        
        try:
            self.model = ChurnModel(model_path=model_path)
            self.model.load()
            logger.info(f"Model loaded for company {self.company.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def predict_customer(self, customer_id: int) -> Dict:
        """
        Predict churn for a single customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with prediction results
        """
        if self.model is None:
            raise ValueError("Model not loaded. Train a model first.")
        
        # Get customer data
        customer = Customer.query.filter_by(
            id=customer_id,
            company_id=self.company.id
        ).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Get related data
        tickets = Ticket.query.filter_by(customer_id=customer_id).all()
        payments = Payment.query.filter_by(customer_id=customer_id).all()
        
        # Convert to dataframes
        customers_df = pd.DataFrame([customer.to_dict()])
        tickets_df = pd.DataFrame([t.to_dict() for t in tickets]) if tickets else pd.DataFrame()
        payments_df = pd.DataFrame([p.to_dict() for p in payments]) if payments else pd.DataFrame()
        
        # Extract features
        features_df = self.feature_engineer.extract_features(
            customers_df, tickets_df, payments_df
        )
        
        # Remove ID column
        X = features_df.drop('id', axis=1, errors='ignore')
        
        # Make prediction
        prediction_result = self.model.predict_with_risk(
            X,
            threshold_high=self.company.get_setting('prediction_threshold_high', 0.7),
            threshold_medium=self.company.get_setting('prediction_threshold_medium', 0.4)
        )
        
        result = {
            'customer_id': customer_id,
            'customer_name': customer.customer_name,
            'churn_probability': float(prediction_result['churn_probability'].iloc[0]),
            'churn_risk': prediction_result['churn_risk'].iloc[0],
            'will_churn': bool(prediction_result['will_churn'].iloc[0]),
            'predicted_at': datetime.utcnow().isoformat()
        }
        
        return result
    
    def predict_batch(self, customer_ids: List[int] = None, 
                     batch_size: int = 1000) -> List[Dict]:
        """
        Predict churn for multiple customers
        
        Args:
            customer_ids: List of customer IDs (if None, predict for all customers)
            batch_size: Number of customers to process at once
            
        Returns:
            List of prediction results
        """
        if self.model is None:
            raise ValueError("Model not loaded. Train a model first.")
        
        logger.info(f"Starting batch prediction for company {self.company.id}")
        
        # Get customers
        query = Customer.query.filter_by(company_id=self.company.id)
        if customer_ids:
            query = query.filter(Customer.id.in_(customer_ids))
        
        customers = query.all()
        logger.info(f"Predicting for {len(customers)} customers")
        
        if not customers:
            return []
        
        # Get all related data
        customer_ids_list = [c.id for c in customers]
        tickets = Ticket.query.filter(
            Ticket.customer_id.in_(customer_ids_list),
            Ticket.company_id == self.company.id
        ).all()
        payments = Payment.query.filter(
            Payment.customer_id.in_(customer_ids_list),
            Payment.company_id == self.company.id
        ).all()
        
        # Convert to dataframes
        customers_df = pd.DataFrame([c.to_dict() for c in customers])
        tickets_df = pd.DataFrame([t.to_dict() for t in tickets]) if tickets else pd.DataFrame()
        payments_df = pd.DataFrame([p.to_dict() for p in payments]) if payments else pd.DataFrame()
        
        # Extract features
        features_df = self.feature_engineer.extract_features(
            customers_df, tickets_df, payments_df
        )
        
        # Keep customer IDs for reference
        customer_ids_series = features_df['id'].copy()
        
        # Remove ID column for prediction
        X = features_df.drop('id', axis=1, errors='ignore')
        
        # Make predictions
        prediction_results = self.model.predict_with_risk(
            X,
            threshold_high=self.company.get_setting('prediction_threshold_high', 0.7),
            threshold_medium=self.company.get_setting('prediction_threshold_medium', 0.4)
        )
        
        # Combine with customer info
        prediction_results['customer_id'] = customer_ids_series.values
        
        # Create customer lookup
        customer_lookup = {c.id: c.customer_name for c in customers}
        prediction_results['customer_name'] = prediction_results['customer_id'].map(customer_lookup)
        
        # Convert to list of dicts
        results = []
        for _, row in prediction_results.iterrows():
            results.append({
                'customer_id': int(row['customer_id']),
                'customer_name': row['customer_name'],
                'churn_probability': float(row['churn_probability']),
                'churn_risk': row['churn_risk'],
                'will_churn': bool(row['will_churn']),
                'predicted_at': datetime.utcnow().isoformat()
            })
        
        logger.info(f"Batch prediction complete: {len(results)} predictions")
        
        return results
    
    def update_customer_predictions(self, customer_ids: List[int] = None) -> Dict:
        """
        Update churn predictions in database
        
        Args:
            customer_ids: List of customer IDs (if None, update all)
            
        Returns:
            Dictionary with update statistics
        """
        if self.model is None:
            raise ValueError("Model not loaded. Train a model first.")
        
        # Make predictions
        predictions = self.predict_batch(customer_ids)
        
        # Update database
        updated = 0
        errors = 0
        
        for pred in predictions:
            try:
                customer = Customer.query.filter_by(
                    id=pred['customer_id'],
                    company_id=self.company.id
                ).first()
                
                if customer:
                    customer.churn_probability = pred['churn_probability']
                    customer.churn_risk = pred['churn_risk']
                    customer.last_prediction_date = datetime.utcnow()
                    updated += 1
                    
            except Exception as e:
                logger.error(f"Error updating customer {pred['customer_id']}: {e}")
                errors += 1
        
        # Commit changes
        db.session.commit()
        
        result = {
            'total_predictions': len(predictions),
            'updated': updated,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Updated {updated} customer predictions")
        
        return result
    
    def get_high_risk_customers(self, limit: int = None) -> List[Dict]:
        """
        Get customers with high churn risk
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            List of high-risk customers with predictions
        """
        query = Customer.query.filter_by(
            company_id=self.company.id,
            churn_risk='high'
        ).order_by(Customer.churn_probability.desc())
        
        if limit:
            query = query.limit(limit)
        
        customers = query.all()
        
        results = []
        for customer in customers:
            results.append({
                'customer_id': customer.id,
                'customer_name': customer.customer_name,
                'email': customer.email,
                'phone': customer.phone,
                'churn_probability': customer.churn_probability,
                'churn_risk': customer.churn_risk,
                'monthly_charges': customer.monthly_charges,
                'tenure_months': customer.tenure_months,
                'last_prediction_date': customer.last_prediction_date.isoformat() 
                    if customer.last_prediction_date else None
            })
        
        return results
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {
                'loaded': False,
                'message': 'No model loaded for this company'
            }
        
        info = self.model.get_model_info()
        info['loaded'] = True
        info['company_id'] = self.company.id
        info['company_name'] = self.company.name
        
        return info