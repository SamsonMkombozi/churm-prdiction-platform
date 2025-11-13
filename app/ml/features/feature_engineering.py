"""
Enhanced Feature Engineering for Churn Prediction
app/ml/features/feature_engineering.py

Calculates the key churn factors: customerNumber, status, daysSinceDisconnection, 
monthsStayed, numberOfPayments, missedPayments, numberOfComplaintsPerMonth
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Enhanced feature engineering for churn prediction with customer metrics"""
    
    def __init__(self):
        """Initialize feature engineering with enhanced customer metrics"""
        self.feature_columns = [
            # Core identification
            'customer_number',
            
            # Primary churn indicators (your PHP requirements)
            'months_stayed',
            'days_since_disconnection', 
            'number_of_payments',
            'missed_payments',
            'number_of_complaints_per_month',
            'customer_status_encoded',
            
            # Financial features
            'monthly_charges',
            'total_charges',
            'outstanding_balance',
            'payment_consistency_score',
            'balance_to_monthly_ratio',
            'avg_payment_amount',
            
            # Service features
            'tenure_months',
            'total_tickets',
            'avg_resolution_hours',
            'service_quality_score',
            
            # Derived risk features
            'new_customer_flag',
            'high_balance_flag',
            'frequent_complaints_flag',
            'payment_issues_flag',
            'disconnected_customer_flag',
            
            # Interaction features
            'complaints_to_tenure_ratio',
            'payments_to_tenure_ratio',
            'balance_stability_score'
        ]
        
        # Status encoding mapping
        self.status_mapping = {
            'active': 1,
            'inactive': 0,
            'suspended': -1,
            'disconnected': -2,
            'churned': -3,
            'terminated': -3,
            'cancelled': -3
        }
    
    def transform(self, customer_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform customer data into features for churn prediction
        
        Args:
            customer_df: DataFrame with customer data
            
        Returns:
            DataFrame with engineered features
        """
        try:
            logger.info(f"🔧 Feature engineering for {len(customer_df)} customers")
            
            # Create a copy to avoid modifying original data
            df = customer_df.copy()
            
            # Ensure required columns exist with defaults
            df = self._ensure_required_columns(df)
            
            # Core churn prediction features
            df = self._calculate_core_features(df)
            
            # Financial features
            df = self._calculate_financial_features(df)
            
            # Service features  
            df = self._calculate_service_features(df)
            
            # Derived risk flags
            df = self._calculate_risk_flags(df)
            
            # Interaction features
            df = self._calculate_interaction_features(df)
            
            # Handle missing values
            df = self._handle_missing_values(df)
            
            # Select and order final feature columns
            available_features = [col for col in self.feature_columns if col in df.columns]
            features_df = df[available_features].copy()
            
            logger.info(f"✅ Generated {len(available_features)} features: {available_features}")
            
            return features_df
            
        except Exception as e:
            logger.error(f"❌ Feature engineering failed: {e}")
            # Return minimal feature set as fallback
            return self._create_fallback_features(customer_df)
    
    def _ensure_required_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns exist with appropriate defaults"""
        
        # Core identification
        if 'customer_number' not in df.columns:
            df['customer_number'] = df.get('crm_customer_id', df.get('id', range(len(df))))
        
        # Key metrics with defaults
        required_columns = {
            'months_stayed': 0,
            'days_since_disconnection': 0,
            'number_of_payments': 0,
            'missed_payments': 0,
            'number_of_complaints_per_month': 0.0,
            'status': 'active',
            'monthly_charges': 0.0,
            'total_charges': 0.0,
            'outstanding_balance': 0.0,
            'tenure_months': 0,
            'total_tickets': 0,
            'total_payments': 0,
            'signup_date': None,
            'disconnection_date': None,
            'last_payment_date': None,
            'last_ticket_date': None,
            'payment_consistency_score': 1.0,
            'service_quality_score': 5.0
        }
        
        for col, default_value in required_columns.items():
            if col not in df.columns:
                df[col] = default_value
        
        return df
    
    def _calculate_core_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate core churn prediction features"""
        
        # Customer status encoding
        df['customer_status_encoded'] = df['status'].map(self.status_mapping).fillna(0)
        
        # Months stayed calculation
        if 'months_stayed' not in df.columns or df['months_stayed'].isna().all():
            df['months_stayed'] = self._calculate_months_stayed(df)
        
        # Days since disconnection
        if 'days_since_disconnection' not in df.columns or df['days_since_disconnection'].isna().all():
            df['days_since_disconnection'] = self._calculate_days_since_disconnection(df)
        
        # Number of payments (use existing or calculate)
        if 'number_of_payments' not in df.columns or df['number_of_payments'].isna().all():
            df['number_of_payments'] = df.get('total_payments', 0)
        
        # Missed payments (use existing or estimate)
        if 'missed_payments' not in df.columns or df['missed_payments'].isna().all():
            df['missed_payments'] = self._estimate_missed_payments(df)
        
        # Complaints per month (use existing or calculate)
        if 'number_of_complaints_per_month' not in df.columns or df['number_of_complaints_per_month'].isna().all():
            df['number_of_complaints_per_month'] = self._calculate_complaints_per_month(df)
        
        return df
    
    def _calculate_financial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate financial-related features"""
        
        # Payment consistency score
        if 'payment_consistency_score' not in df.columns:
            df['payment_consistency_score'] = self._calculate_payment_consistency(df)
        
        # Balance to monthly charges ratio
        df['balance_to_monthly_ratio'] = np.where(
            df['monthly_charges'] > 0,
            df['outstanding_balance'] / df['monthly_charges'],
            0
        )
        
        # Average payment amount
        df['avg_payment_amount'] = np.where(
            df['number_of_payments'] > 0,
            df['total_charges'] / df['number_of_payments'],
            df['monthly_charges']
        )
        
        return df
    
    def _calculate_service_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate service-related features"""
        
        # Use existing tenure_months or calculate from months_stayed
        df['tenure_months'] = df['tenure_months'].fillna(df['months_stayed'])
        
        # Service quality score (simplified calculation)
        df['service_quality_score'] = np.where(
            df['total_tickets'] > 0,
            np.maximum(1.0, 5.0 - (df['total_tickets'] / df['tenure_months'].clip(lower=1)) * 2),
            5.0
        )
        
        # Average resolution hours (estimate if not available)
        if 'avg_resolution_hours' not in df.columns:
            df['avg_resolution_hours'] = np.where(
                df['total_tickets'] > 0,
                24.0,  # Default 24 hours
                0.0
            )
        
        return df
    
    def _calculate_risk_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate binary risk flag features"""
        
        # New customer flag (less than 6 months)
        df['new_customer_flag'] = (df['months_stayed'] < 6).astype(int)
        
        # High balance flag (balance > 2x monthly charges)
        df['high_balance_flag'] = (
            df['outstanding_balance'] > (df['monthly_charges'] * 2)
        ).astype(int)
        
        # Frequent complaints flag (>0.3 complaints per month)
        df['frequent_complaints_flag'] = (
            df['number_of_complaints_per_month'] > 0.3
        ).astype(int)
        
        # Payment issues flag (consistency < 0.8 or missed payments > 2)
        df['payment_issues_flag'] = (
            (df['payment_consistency_score'] < 0.8) | 
            (df['missed_payments'] > 2)
        ).astype(int)
        
        # Disconnected customer flag
        df['disconnected_customer_flag'] = (
            df['customer_status_encoded'] < 0
        ).astype(int)
        
        return df
    
    def _calculate_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate interaction and ratio features"""
        
        # Complaints to tenure ratio
        df['complaints_to_tenure_ratio'] = np.where(
            df['tenure_months'] > 0,
            df['total_tickets'] / df['tenure_months'],
            0
        )
        
        # Payments to tenure ratio
        df['payments_to_tenure_ratio'] = np.where(
            df['tenure_months'] > 0,
            df['number_of_payments'] / df['tenure_months'],
            0
        )
        
        # Balance stability score
        df['balance_stability_score'] = np.where(
            df['monthly_charges'] > 0,
            1.0 - np.minimum(1.0, df['outstanding_balance'] / (df['monthly_charges'] * 3)),
            1.0
        )
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate imputation"""
        
        # Fill missing numeric values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Fill missing categorical values
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].fillna('unknown')
        
        return df
    
    def _calculate_months_stayed(self, df: pd.DataFrame) -> pd.Series:
        """Calculate months stayed from signup date or tenure"""
        
        result = df['tenure_months'].copy()
        
        # If signup_date is available, calculate from it
        if 'signup_date' in df.columns:
            signup_dates = pd.to_datetime(df['signup_date'], errors='coerce')
            current_date = datetime.now()
            
            months_from_signup = (
                (current_date.year - signup_dates.dt.year) * 12 + 
                (current_date.month - signup_dates.dt.month)
            )
            
            # Use signup calculation where available
            result = result.fillna(months_from_signup).fillna(0)
        
        return result.clip(lower=0)
    
    def _calculate_days_since_disconnection(self, df: pd.DataFrame) -> pd.Series:
        """Calculate days since disconnection"""
        
        result = pd.Series(0, index=df.index)
        
        # Check if customer is disconnected
        disconnected_mask = df['status'].isin(['inactive', 'suspended', 'disconnected', 'churned'])
        
        if 'disconnection_date' in df.columns:
            disconnection_dates = pd.to_datetime(df['disconnection_date'], errors='coerce')
            current_date = datetime.now()
            
            days_disconnected = (current_date - disconnection_dates).dt.days
            result.loc[disconnected_mask] = days_disconnected.loc[disconnected_mask].fillna(30)
        else:
            # Default assumption for disconnected customers
            result.loc[disconnected_mask] = 30
        
        return result.clip(lower=0)
    
    def _estimate_missed_payments(self, df: pd.DataFrame) -> pd.Series:
        """Estimate missed payments based on consistency score"""
        
        if 'payment_consistency_score' in df.columns:
            consistency = df['payment_consistency_score']
            total_payments = df['number_of_payments']
            
            # Estimate missed payments from consistency
            missed = total_payments * (1 - consistency)
            return missed.round().clip(lower=0)
        else:
            # Conservative estimate based on balance
            high_balance_mask = df['outstanding_balance'] > (df['monthly_charges'] * 1.5)
            return high_balance_mask.astype(int)
    
    def _calculate_complaints_per_month(self, df: pd.DataFrame) -> pd.Series:
        """Calculate complaints per month"""
        
        months_stayed = df['months_stayed'].clip(lower=1)  # Avoid division by zero
        total_tickets = df['total_tickets']
        
        # Assume 30% of tickets are complaints (conservative estimate)
        estimated_complaints = total_tickets * 0.3
        
        return estimated_complaints / months_stayed
    
    def _calculate_payment_consistency(self, df: pd.DataFrame) -> pd.Series:
        """Calculate payment consistency score"""
        
        total_payments = df['number_of_payments']
        missed_payments = df['missed_payments']
        
        # Calculate consistency (1 - miss rate)
        consistency = np.where(
            total_payments > 0,
            1.0 - (missed_payments / total_payments),
            1.0
        )
        
        return consistency.clip(0, 1)
    
    def _create_fallback_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create minimal feature set as fallback"""
        
        logger.warning("🔥 Creating fallback feature set")
        
        fallback_df = pd.DataFrame(index=df.index)
        
        # Minimal required features
        fallback_df['customer_number'] = df.get('id', range(len(df)))
        fallback_df['months_stayed'] = df.get('tenure_months', 0)
        fallback_df['days_since_disconnection'] = 0
        fallback_df['number_of_payments'] = df.get('total_payments', 0)
        fallback_df['missed_payments'] = 0
        fallback_df['number_of_complaints_per_month'] = 0.0
        fallback_df['customer_status_encoded'] = 1
        fallback_df['monthly_charges'] = df.get('monthly_charges', 0)
        fallback_df['total_charges'] = df.get('total_charges', 0)
        fallback_df['outstanding_balance'] = df.get('outstanding_balance', 0)
        
        return fallback_df
    
    def get_feature_importance_mapping(self) -> Dict[str, str]:
        """Get mapping of features to their business meaning"""
        
        return {
            'customer_number': 'Customer Identifier',
            'months_stayed': 'Customer Tenure (Months)',
            'days_since_disconnection': 'Days Since Service Disconnection',
            'number_of_payments': 'Total Successful Payments',
            'missed_payments': 'Failed/Missed Payments',
            'number_of_complaints_per_month': 'Monthly Complaint Rate',
            'customer_status_encoded': 'Account Status Score',
            'payment_consistency_score': 'Payment Reliability',
            'balance_to_monthly_ratio': 'Outstanding Balance Risk',
            'new_customer_flag': 'New Customer Risk',
            'high_balance_flag': 'High Balance Risk',
            'payment_issues_flag': 'Payment Problems',
            'frequent_complaints_flag': 'Service Quality Issues',
            'disconnected_customer_flag': 'Service Disconnection'
        }


# Example usage and testing
def test_feature_engineering():
    """Test feature engineering with sample data"""
    
    # Sample customer data
    sample_data = [
        {
            'id': 1,
            'customer_name': 'Test Customer 1',
            'status': 'active',
            'tenure_months': 18,
            'monthly_charges': 5000,
            'total_charges': 90000,
            'outstanding_balance': 2500,
            'total_payments': 17,
            'total_tickets': 2,
            'signup_date': '2023-01-15'
        },
        {
            'id': 2,
            'customer_name': 'Test Customer 2', 
            'status': 'inactive',
            'tenure_months': 4,
            'monthly_charges': 3000,
            'total_charges': 12000,
            'outstanding_balance': 9000,
            'total_payments': 3,
            'total_tickets': 5,
            'disconnection_date': '2024-10-01'
        }
    ]
    
    df = pd.DataFrame(sample_data)
    
    # Initialize and test feature engineering
    fe = FeatureEngineering()
    features = fe.transform(df)
    
    print("✅ Feature Engineering Test Results:")
    print(f"📊 Input customers: {len(df)}")
    print(f"🔧 Generated features: {len(features.columns)}")
    print(f"📋 Feature columns: {list(features.columns)}")
    print("\n📈 Sample feature values:")
    print(features.head())
    
    return features


if __name__ == "__main__":
    test_feature_engineering()