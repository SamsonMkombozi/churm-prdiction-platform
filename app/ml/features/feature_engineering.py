"""
Fixed Feature Engineering Pipeline for Churn Prediction
app/ml/features/feature_engineering.py

Transforms raw customer data into ML-ready features
"""
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Feature engineering pipeline for churn prediction"""
    
    def __init__(self):
        """Initialize feature engineering pipeline"""
        self.feature_names = []
        self.is_fitted = False
    
    def fit(self, df: pd.DataFrame):
        """
        Fit the feature engineering pipeline
        
        Args:
            df: Raw customer dataframe
        """
        logger.info("Fitting feature engineering pipeline")
        
        # Store feature names after transformation
        transformed_df = self.transform(df)
        self.feature_names = list(transformed_df.columns)
        self.is_fitted = True
        
        logger.info(f"Feature pipeline fitted with {len(self.feature_names)} features")
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw customer data into ML features
        
        Args:
            df: Raw customer dataframe
            
        Returns:
            Transformed feature dataframe
        """
        if df.empty:
            logger.warning("Empty dataframe provided for transformation")
            return pd.DataFrame()
        
        logger.info(f"Transforming {len(df)} customer records")
        
        # Create copy for transformation
        features_df = df.copy()
        
        try:
            # 1. Basic customer features - ensure numeric conversion
            features_df['tenure_months'] = pd.to_numeric(features_df.get('tenure_months', 0), errors='coerce').fillna(0)
            features_df['monthly_charges'] = pd.to_numeric(features_df.get('monthly_charges', 0), errors='coerce').fillna(0)
            features_df['total_charges'] = pd.to_numeric(features_df.get('total_charges', 0), errors='coerce').fillna(0)
            
            # 2. Financial features
            features_df['outstanding_balance'] = pd.to_numeric(features_df.get('outstanding_balance', 0), errors='coerce').fillna(0)
            features_df['total_payments'] = pd.to_numeric(features_df.get('total_payments', 0), errors='coerce').fillna(0)
            features_df['total_tickets'] = pd.to_numeric(features_df.get('total_tickets', 0), errors='coerce').fillna(0)
            
            # 3. Derived features
            features_df['avg_monthly_payment'] = np.where(
                features_df['tenure_months'] > 0,
                features_df['total_charges'] / features_df['tenure_months'],
                0
            )
            
            features_df['balance_to_monthly_ratio'] = np.where(
                features_df['monthly_charges'] > 0,
                features_df['outstanding_balance'] / features_df['monthly_charges'],
                0
            )
            
            features_df['tickets_per_month'] = np.where(
                features_df['tenure_months'] > 0,
                features_df['total_tickets'] / features_df['tenure_months'],
                0
            )
            
            features_df['payment_consistency'] = np.where(
                features_df['tenure_months'] > 0,
                features_df['total_payments'] / features_df['tenure_months'],
                0
            )
            
            # 4. Risk indicators
            features_df['high_balance_flag'] = (features_df['outstanding_balance'] > features_df['monthly_charges'] * 2).astype(int)
            features_df['low_usage_flag'] = (features_df['monthly_charges'] < 50).astype(int)
            features_df['high_tickets_flag'] = (features_df['total_tickets'] > 5).astype(int)
            features_df['new_customer_flag'] = (features_df['tenure_months'] < 6).astype(int)
            
            # 5. Select final feature columns
            final_features = [
                'tenure_months', 'monthly_charges', 'total_charges',
                'outstanding_balance', 'total_payments', 'total_tickets',
                'avg_monthly_payment', 'balance_to_monthly_ratio',
                'tickets_per_month', 'payment_consistency',
                'high_balance_flag', 'low_usage_flag', 'high_tickets_flag', 'new_customer_flag'
            ]
            
            # Ensure all features exist
            for feature in final_features:
                if feature not in features_df.columns:
                    features_df[feature] = 0
            
            # Return only final features
            result_df = features_df[final_features].copy()
            
            # Handle any remaining NaN values
            result_df = result_df.fillna(0)
            
            # Ensure all values are numeric
            for col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
            
            logger.info(f"✅ Feature transformation complete: {len(result_df.columns)} features")
            return result_df
            
        except Exception as e:
            logger.error(f"❌ Feature transformation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return basic features as fallback
            basic_features = pd.DataFrame({
                'tenure_months': [0] * len(df),
                'monthly_charges': [0] * len(df),
                'total_charges': [0] * len(df),
                'outstanding_balance': [0] * len(df),
                'total_payments': [0] * len(df),
                'total_tickets': [0] * len(df),
                'avg_monthly_payment': [0] * len(df),
                'balance_to_monthly_ratio': [0] * len(df),
                'tickets_per_month': [0] * len(df),
                'payment_consistency': [0] * len(df),
                'high_balance_flag': [0] * len(df),
                'low_usage_flag': [0] * len(df),
                'high_tickets_flag': [0] * len(df),
                'new_customer_flag': [0] * len(df)
            })
            return basic_features
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit and transform in one step
        
        Args:
            df: Raw customer dataframe
            
        Returns:
            Transformed feature dataframe
        """
        return self.fit(df).transform(df)
    
    def get_feature_names(self) -> list:
        """Get list of feature names"""
        return self.feature_names if self.is_fitted else []
    
    def transform_single_customer(self, customer_data: dict) -> pd.DataFrame:
        """
        Transform single customer data
        
        Args:
            customer_data: Dictionary with customer info
            
        Returns:
            Single-row transformed dataframe
        """
        # Convert to dataframe
        df = pd.DataFrame([customer_data])
        
        # Transform
        return self.transform(df)