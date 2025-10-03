"""
Feature Engineering for Churn Prediction
app/ml/features/feature_engineering.py

Extracts and engineers features from customer, ticket, and payment data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Extract and engineer features for churn prediction"""
    
    def __init__(self):
        """Initialize feature engineering"""
        self.feature_names = []
        self.required_columns = [
            'tenure_months', 'monthly_charges', 'total_charges',
            'total_tickets', 'total_payments', 'outstanding_balance'
        ]
    
    def extract_features(self, customers_df: pd.DataFrame, 
                        tickets_df: Optional[pd.DataFrame] = None,
                        payments_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Extract features from customer, ticket, and payment data
        
        Args:
            customers_df: DataFrame with customer data
            tickets_df: Optional DataFrame with ticket data
            payments_df: Optional DataFrame with payment data
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting feature extraction...")
        
        # Create feature dataframe
        features_df = customers_df.copy()
        
        # Basic customer features
        features_df = self._add_customer_features(features_df)
        
        # Ticket-based features
        if tickets_df is not None and not tickets_df.empty:
            features_df = self._add_ticket_features(features_df, tickets_df)
        else:
            features_df = self._add_default_ticket_features(features_df)
        
        # Payment-based features
        if payments_df is not None and not payments_df.empty:
            features_df = self._add_payment_features(features_df, payments_df)
        else:
            features_df = self._add_default_payment_features(features_df)
        
        # Derived features
        features_df = self._add_derived_features(features_df)
        
        # Select final features
        features_df = self._select_features(features_df)
        
        logger.info(f"Feature extraction complete. Shape: {features_df.shape}")
        
        return features_df
    
    def _add_customer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic customer features"""
        # Tenure-based features
        df['tenure_months'] = df['tenure_months'].fillna(0)
        df['is_new_customer'] = (df['tenure_months'] < 3).astype(int)
        df['is_long_term_customer'] = (df['tenure_months'] > 24).astype(int)
        
        # Financial features
        df['monthly_charges'] = df['monthly_charges'].fillna(0)
        df['total_charges'] = df['total_charges'].fillna(0)
        df['outstanding_balance'] = df['outstanding_balance'].fillna(0)
        
        # Balance-to-charges ratio
        df['balance_ratio'] = np.where(
            df['monthly_charges'] > 0,
            df['outstanding_balance'] / df['monthly_charges'],
            0
        )
        
        # High/low spender indicators
        df['is_high_spender'] = (df['monthly_charges'] > df['monthly_charges'].median()).astype(int)
        
        # Service type encoding (one-hot)
        if 'service_type' in df.columns:
            service_dummies = pd.get_dummies(df['service_type'], prefix='service')
            df = pd.concat([df, service_dummies], axis=1)
        
        # Connection type encoding
        if 'connection_type' in df.columns:
            connection_dummies = pd.get_dummies(df['connection_type'], prefix='connection')
            df = pd.concat([df, connection_dummies], axis=1)
        
        # Account type encoding
        if 'account_type' in df.columns:
            account_dummies = pd.get_dummies(df['account_type'], prefix='account')
            df = pd.concat([df, account_dummies], axis=1)
        
        return df
    
    def _add_ticket_features(self, df: pd.DataFrame, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Add ticket-based features"""
        # Group tickets by customer
        ticket_stats = tickets_df.groupby('customer_id').agg({
            'id': 'count',  # Total tickets
            'priority': lambda x: (x == 'high').sum(),  # High priority tickets
            'status': lambda x: (x == 'open').sum(),  # Open tickets
            'resolution_time_hours': ['mean', 'max']  # Resolution time stats
        }).reset_index()
        
        ticket_stats.columns = [
            'customer_id', 'total_tickets', 'high_priority_tickets',
            'open_tickets', 'avg_resolution_time', 'max_resolution_time'
        ]
        
        # Calculate recent ticket activity (last 30 days)
        if 'created_at' in tickets_df.columns:
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_tickets = tickets_df[tickets_df['created_at'] >= recent_date]
            recent_stats = recent_tickets.groupby('customer_id').size().reset_index(name='recent_tickets')
            ticket_stats = ticket_stats.merge(recent_stats, on='customer_id', how='left')
        
        # Merge with main dataframe
        df = df.merge(ticket_stats, left_on='id', right_on='customer_id', how='left')
        
        # Fill NaN values
        ticket_cols = ['total_tickets', 'high_priority_tickets', 'open_tickets', 
                      'avg_resolution_time', 'max_resolution_time', 'recent_tickets']
        for col in ticket_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Ticket rate (tickets per month of tenure)
        df['ticket_rate'] = np.where(
            df['tenure_months'] > 0,
            df['total_tickets'] / df['tenure_months'],
            0
        )
        
        return df
    
    def _add_default_ticket_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add default ticket features when no ticket data available"""
        df['total_tickets'] = df.get('total_tickets', 0)
        df['high_priority_tickets'] = 0
        df['open_tickets'] = 0
        df['avg_resolution_time'] = 0
        df['max_resolution_time'] = 0
        df['recent_tickets'] = 0
        df['ticket_rate'] = 0
        return df
    
    def _add_payment_features(self, df: pd.DataFrame, payments_df: pd.DataFrame) -> pd.DataFrame:
        """Add payment-based features"""
        # Group payments by customer
        payment_stats = payments_df.groupby('customer_id').agg({
            'id': 'count',  # Total payments
            'amount': ['sum', 'mean', 'std'],  # Payment statistics
            'status': lambda x: (x == 'completed').sum()  # Completed payments
        }).reset_index()
        
        payment_stats.columns = [
            'customer_id', 'total_payments', 'total_paid',
            'avg_payment', 'payment_std', 'completed_payments'
        ]
        
        # Payment regularity
        if 'payment_date' in payments_df.columns:
            # Calculate days between payments
            sorted_payments = payments_df.sort_values(['customer_id', 'payment_date'])
            sorted_payments['days_between'] = sorted_payments.groupby('customer_id')['payment_date'].diff().dt.days
            
            payment_regularity = sorted_payments.groupby('customer_id')['days_between'].agg(['mean', 'std']).reset_index()
            payment_regularity.columns = ['customer_id', 'avg_days_between_payments', 'payment_irregularity']
            payment_stats = payment_stats.merge(payment_regularity, on='customer_id', how='left')
        
        # Recent payment activity (last 30 days)
        if 'payment_date' in payments_df.columns:
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_payments = payments_df[payments_df['payment_date'] >= recent_date]
            recent_stats = recent_payments.groupby('customer_id').agg({
                'id': 'count',
                'amount': 'sum'
            }).reset_index()
            recent_stats.columns = ['customer_id', 'recent_payments', 'recent_payment_amount']
            payment_stats = payment_stats.merge(recent_stats, on='customer_id', how='left')
        
        # Merge with main dataframe
        df = df.merge(payment_stats, left_on='id', right_on='customer_id', how='left')
        
        # Fill NaN values
        payment_cols = ['total_payments', 'total_paid', 'avg_payment', 'payment_std',
                       'completed_payments', 'avg_days_between_payments', 'payment_irregularity',
                       'recent_payments', 'recent_payment_amount']
        for col in payment_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Payment rate (payments per month of tenure)
        df['payment_rate'] = np.where(
            df['tenure_months'] > 0,
            df['total_payments'] / df['tenure_months'],
            0
        )
        
        # Payment completion rate
        df['payment_completion_rate'] = np.where(
            df['total_payments'] > 0,
            df['completed_payments'] / df['total_payments'],
            0
        )
        
        return df
    
    def _add_default_payment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add default payment features when no payment data available"""
        df['total_payments'] = df.get('total_payments', 0)
        df['total_paid'] = 0
        df['avg_payment'] = 0
        df['payment_std'] = 0
        df['completed_payments'] = 0
        df['avg_days_between_payments'] = 0
        df['payment_irregularity'] = 0
        df['recent_payments'] = 0
        df['recent_payment_amount'] = 0
        df['payment_rate'] = 0
        df['payment_completion_rate'] = 0
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features combining multiple data sources"""
        # Engagement score (combination of tickets and payments)
        df['engagement_score'] = (
            df['total_payments'] * 0.6 +
            df['total_tickets'] * 0.4
        ) / (df['tenure_months'] + 1)  # Normalize by tenure
        
        # Customer health score
        df['health_score'] = (
            (df['payment_completion_rate'] * 40) +
            (np.clip(1 - (df['open_tickets'] / 10), 0, 1) * 30) +
            (np.clip(1 - (df['outstanding_balance'] / (df['monthly_charges'] + 1)), 0, 1) * 30)
        )
        
        # Risk indicators
        df['has_outstanding_balance'] = (df['outstanding_balance'] > 0).astype(int)
        df['has_open_tickets'] = (df['open_tickets'] > 0).astype(int)
        df['late_payer'] = (df['balance_ratio'] > 2).astype(int)
        
        # Service usage intensity
        df['service_intensity'] = (
            df['monthly_charges'] / (df['tenure_months'] + 1)
        )
        
        return df
    
    def _select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select final feature set for modeling"""
        # Define feature columns to keep
        feature_cols = [
            # Customer ID (for reference)
            'id',
            
            # Basic features
            'tenure_months', 'monthly_charges', 'total_charges',
            'outstanding_balance', 'balance_ratio',
            
            # Customer segments
            'is_new_customer', 'is_long_term_customer', 'is_high_spender',
            
            # Ticket features
            'total_tickets', 'ticket_rate', 'high_priority_tickets',
            'open_tickets', 'recent_tickets',
            
            # Payment features
            'total_payments', 'payment_rate', 'payment_completion_rate',
            'avg_payment', 'recent_payments',
            
            # Derived features
            'engagement_score', 'health_score',
            'has_outstanding_balance', 'has_open_tickets', 'late_payer'
        ]
        
        # Add one-hot encoded columns if they exist
        for col in df.columns:
            if col.startswith(('service_', 'connection_', 'account_')):
                feature_cols.append(col)
        
        # Select only existing columns
        available_cols = [col for col in feature_cols if col in df.columns]
        
        self.feature_names = [col for col in available_cols if col != 'id']
        
        return df[available_cols]
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names
    
    def prepare_for_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare dataframe for prediction (ensure all features exist)
        
        Args:
            df: Input dataframe
            
        Returns:
            DataFrame with all required features
        """
        # Ensure all required features exist
        for feature in self.feature_names:
            if feature not in df.columns:
                df[feature] = 0
        
        # Select only model features in correct order
        return df[self.feature_names]