"""
Churn Prediction Model
app/ml/models/churn_model.py

XGBoost-based churn prediction model
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import logging
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, confusion_matrix
)

logger = logging.getLogger(__name__)


class ChurnModel:
    """XGBoost-based churn prediction model"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize churn model
        
        Args:
            model_path: Path to saved model file
        """
        self.model = None
        self.feature_names = None
        self.model_path = model_path
        self.version = None
        self.trained_at = None
        self.metrics = {}
        
        # Model hyperparameters
        self.params = {
            'objective': 'binary:logistic',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 1,
            'gamma': 0,
            'reg_alpha': 0,
            'reg_lambda': 1,
            'random_state': 42,
            'eval_metric': 'auc'
        }
    
    def train(self, X: pd.DataFrame, y: pd.Series, 
              test_size: float = 0.2, 
              validation_split: float = 0.2) -> Dict:
        """
        Train the churn prediction model
        
        Args:
            X: Feature dataframe
            y: Target variable (0 = not churned, 1 = churned)
            test_size: Proportion of data for testing
            validation_split: Proportion of training data for validation
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Starting model training with {len(X)} samples...")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Split data into train and test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Further split training into train and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=validation_split, 
            random_state=42, stratify=y_train
        )
        
        logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
        
        # Create XGBoost classifier
        self.model = xgb.XGBClassifier(**self.params)
        
        # Train model with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
        
        self.trained_at = datetime.utcnow()
        self.version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Model training complete. Test accuracy: {self.metrics['accuracy']:.4f}")
        logger.info(f"ROC-AUC: {self.metrics['roc_auc']:.4f}")
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict churn for given features
        
        Args:
            X: Feature dataframe
            
        Returns:
            Array of predictions (0 or 1)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Ensure features are in correct order
        X = self._prepare_features(X)
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict churn probability for given features
        
        Args:
            X: Feature dataframe
            
        Returns:
            Array of churn probabilities (0.0 to 1.0)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Ensure features are in correct order
        X = self._prepare_features(X)
        
        # Return probability of positive class (churn)
        return self.model.predict_proba(X)[:, 1]
    
    def predict_with_risk(self, X: pd.DataFrame, 
                         threshold_high: float = 0.7,
                         threshold_medium: float = 0.4) -> pd.DataFrame:
        """
        Predict churn with risk categorization
        
        Args:
            X: Feature dataframe
            threshold_high: Threshold for high risk (default: 0.7)
            threshold_medium: Threshold for medium risk (default: 0.4)
            
        Returns:
            DataFrame with predictions, probabilities, and risk categories
        """
        probas = self.predict_proba(X)
        
        # Categorize risk
        risk_categories = np.where(
            probas >= threshold_high, 'high',
            np.where(probas >= threshold_medium, 'medium', 'low')
        )
        
        results = pd.DataFrame({
            'churn_probability': probas,
            'churn_risk': risk_categories,
            'will_churn': (probas >= 0.5).astype(int)
        })
        
        return results
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance scores
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        importance_scores = self.model.feature_importances_
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance_scores
        }).sort_values('importance', ascending=False)
        
        return importance_df.head(top_n)
    
    def save(self, filepath: str = None) -> str:
        """
        Save model to disk
        
        Args:
            filepath: Path to save model (optional)
            
        Returns:
            Path where model was saved
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        if filepath is None:
            if self.model_path is None:
                raise ValueError("No filepath provided and no default path set")
            filepath = self.model_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save model and metadata
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'version': self.version,
            'trained_at': self.trained_at,
            'metrics': self.metrics,
            'params': self.params
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to: {filepath}")
        
        return filepath
    
    def load(self, filepath: str = None) -> bool:
        """
        Load model from disk
        
        Args:
            filepath: Path to model file (optional)
            
        Returns:
            True if loaded successfully
        """
        if filepath is None:
            if self.model_path is None:
                raise ValueError("No filepath provided and no default path set")
            filepath = self.model_path
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        # Load model and metadata
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.version = model_data.get('version')
        self.trained_at = model_data.get('trained_at')
        self.metrics = model_data.get('metrics', {})
        self.params = model_data.get('params', {})
        
        logger.info(f"Model loaded from: {filepath}")
        logger.info(f"Version: {self.version}, Trained: {self.trained_at}")
        
        return True
    
    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for prediction (ensure correct order and presence)
        
        Args:
            X: Input feature dataframe
            
        Returns:
            DataFrame with features in correct order
        """
        if self.feature_names is None:
            raise ValueError("Feature names not set")
        
        # Add missing features with zero values
        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0
        
        # Select features in correct order
        return X[self.feature_names]
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Evaluate model on new data
        
        Args:
            X: Feature dataframe
            y: True labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        y_pred = self.predict(X)
        y_pred_proba = self.predict_proba(X)
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'f1_score': f1_score(y, y_pred),
            'roc_auc': roc_auc_score(y, y_pred_proba),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
        
        return metrics
    
    def get_model_info(self) -> Dict:
        """
        Get model information
        
        Returns:
            Dictionary with model metadata
        """
        return {
            'version': self.version,
            'trained_at': self.trained_at.isoformat() if self.trained_at else None,
            'num_features': len(self.feature_names) if self.feature_names else 0,
            'metrics': self.metrics,
            'params': self.params
        }