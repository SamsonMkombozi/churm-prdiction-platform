"""
Updated Model Training Script with CRM Data
app/ml/training/train_model.py

Trains churn prediction model using data from Habari CRM
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app import create_app
from app.extensions import db
from app.models.company import Company
from app.ml.models.churn_model import ChurnModel
from app.ml.features.feature_engineering import FeatureEngineering

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, confusion_matrix, classification_report
)


class ModelTrainer:
    """Train churn prediction model"""
    
    def __init__(self, data_file: str, model_name: str = 'churn_xgboost'):
        """
        Initialize trainer
        
        Args:
            data_file: Path to training data CSV
            model_name: Name for saved model
        """
        self.data_file = data_file
        self.model_name = model_name
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.model = None
        self.feature_engineer = FeatureEngineering()
        self.metrics = {}
        
    def load_data(self):
        """Load training data"""
        print("\n" + "="*60)
        print("LOADING TRAINING DATA")
        print("="*60)
        
        if not os.path.exists(self.data_file):
            print(f"❌ Data file not found: {self.data_file}")
            print("\n💡 Run this first:")
            print("   python app/ml/training/fetch_and_prepare_data.py")
            return False
        
        self.df = pd.read_csv(self.data_file)
        
        print(f"✅ Loaded data from: {self.data_file}")
        print(f"   Shape: {self.df.shape}")
        print(f"   Columns: {len(self.df.columns)}")
        
        # Check for target variable
        if 'churned' not in self.df.columns:
            print("❌ Target variable 'churned' not found in data")
            return False
        
        # Check class balance
        churn_count = self.df['churned'].sum()
        churn_rate = (churn_count / len(self.df)) * 100
        
        print(f"\n📊 Target Distribution:")
        print(f"   Churned: {churn_count} ({churn_rate:.1f}%)")
        print(f"   Active: {len(self.df) - churn_count} ({100-churn_rate:.1f}%)")
        
        if churn_count < 10:
            print("\n⚠️  WARNING: Very few churned customers. Model may not train well.")
            print("   Consider adjusting churn rules in fetch_and_prepare_data.py")
        
        return True
    
    def prepare_features(self):
        """Prepare features for training"""
        print("\n" + "="*60)
        print("PREPARING FEATURES")
        print("="*60)
        
        # Define feature columns (exclude ID and target)
        exclude_cols = [
            'customer_id', 'id', 'churned', 'churn_score',
            'customer_name', 'name', 'email', 'phone', 'address',
            'signup_date', 'last_payment_date', 'last_ticket_date'
        ]
        
        feature_cols = [
            col for col in self.df.columns 
            if col not in exclude_cols and self.df[col].dtype in ['int64', 'float64', 'bool']
        ]
        
        print(f"✅ Selected {len(feature_cols)} features:")
        for col in feature_cols:
            print(f"   - {col}")
        
        # Separate features and target
        X = self.df[feature_cols].copy()
        y = self.df['churned'].copy()
        
        # Handle missing values
        X = X.fillna(0)
        
        # Convert boolean to int
        for col in X.columns:
            if X[col].dtype == 'bool':
                X[col] = X[col].astype(int)
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n✅ Data split:")
        print(f"   Training set: {len(self.X_train)} samples")
        print(f"   Test set: {len(self.X_test)} samples")
        print(f"   Training churn rate: {(self.y_train.sum() / len(self.y_train)) * 100:.1f}%")
        print(f"   Test churn rate: {(self.y_test.sum() / len(self.y_test)) * 100:.1f}%")
        
        # Store feature names
        self.feature_names = feature_cols
        
        return True
    
    def train(self):
        """Train the model"""
        print("\n" + "="*60)
        print("TRAINING MODEL")
        print("="*60)
        
        # Initialize model
        self.model = ChurnModel()
        
        # Calculate scale_pos_weight for imbalanced data
        neg_count = (self.y_train == 0).sum()
        pos_count = (self.y_train == 1).sum()
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
        
        print(f"📊 Class balance:")
        print(f"   Negative (Active): {neg_count}")
        print(f"   Positive (Churned): {pos_count}")
        print(f"   Scale pos weight: {scale_pos_weight:.2f}")
        
        # Train
        print("\n🚀 Training XGBoost model...")
        self.model.train(self.X_train, self.y_train)
        
        print("✅ Training complete!")
        
        return True
    
    def evaluate(self):
        """Evaluate model performance"""
        print("\n" + "="*60)
        print("EVALUATING MODEL")
        print("="*60)
        
        # Make predictions
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred, zero_division=0)
        recall = recall_score(self.y_test, y_pred, zero_division=0)
        f1 = f1_score(self.y_test, y_pred, zero_division=0)
        
        # ROC AUC (only if we have both classes)
        try:
            roc_auc = roc_auc_score(self.y_test, y_pred_proba)
        except:
            roc_auc = 0.0
        
        # Store metrics
        self.metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'test_samples': len(self.y_test),
            'churned_samples': self.y_test.sum()
        }
        
        # Print metrics
        print(f"\n📊 Model Performance:")
        print(f"   Accuracy:  {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1 Score:  {f1:.4f}")
        print(f"   ROC AUC:   {roc_auc:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, y_pred)
        print(f"\n📊 Confusion Matrix:")
        print(f"                 Predicted")
        print(f"                 0      1")
        print(f"   Actual  0   {cm[0][0]:4d}  {cm[0][1]:4d}")
        print(f"           1   {cm[1][0]:4d}  {cm[1][1]:4d}")
        
        # Classification report
        print(f"\n📊 Classification Report:")
        print(classification_report(self.y_test, y_pred, 
                                   target_names=['Active', 'Churned'],
                                   zero_division=0))
        
        # Feature importance
        print(f"\n📊 Top 10 Important Features:")
        feature_importance = self.model.get_feature_importance()
        
        if feature_importance:
            top_features = sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            for i, (feature, importance) in enumerate(top_features, 1):
                print(f"   {i:2d}. {feature:30s} {importance:.4f}")
        
        return True
    
    def save_model(self):
        """Save trained model"""
        print("\n" + "="*60)
        print("SAVING MODEL")
        print("="*60)
        
        # Create save directory
        save_dir = "app/ml/models/saved"
        os.makedirs(save_dir, exist_ok=True)
        
        # Save model
        model_path = self.model.save(save_dir)
        
        if model_path:
            print(f"✅ Model saved to: {model_path}")
            
            # Save metadata
            metadata = {
                'model_name': self.model_name,
                'trained_at': datetime.now().isoformat(),
                'training_data': self.data_file,
                'training_samples': len(self.X_train),
                'test_samples': len(self.X_test),
                'features': self.feature_names,
                'metrics': self.metrics
            }
            
            metadata_path = os.path.join(save_dir, f"{self.model_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Metadata saved to: {metadata_path}")
            
            return model_path
        else:
            print("❌ Failed to save model")
            return None
    
    def run_full_pipeline(self):
        """Run complete training pipeline"""
        print("\n" + "="*60)
        print("CHURN PREDICTION MODEL TRAINING")
        print("="*60)
        print(f"Data file: {self.data_file}")
        print(f"Model name: {self.model_name}")
        print("="*60)
        
        # Step 1: Load data
        if not self.load_data():
            return False
        
        # Step 2: Prepare features
        if not self.prepare_features():
            return False
        
        # Step 3: Train model
        if not self.train():
            return False
        
        # Step 4: Evaluate model
        if not self.evaluate():
            return False
        
        # Step 5: Save model
        model_path = self.save_model()
        
        if not model_path:
            return False
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"\n📁 Model saved to: {model_path}")
        print(f"\n🎯 Model Performance Summary:")
        print(f"   Accuracy:  {self.metrics['accuracy']:.2%}")
        print(f"   Precision: {self.metrics['precision']:.2%}")
        print(f"   Recall:    {self.metrics['recall']:.2%}")
        print(f"   F1 Score:  {self.metrics['f1_score']:.2%}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Test predictions with Phase 6")
        print(f"   2. Integrate into production system")
        print(f"   3. Monitor model performance")
        
        return True


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Train churn prediction model with CRM data'
    )
    
    parser.add_argument(
        '--data-file',
        type=str,
        default='app/ml/data/training_data.csv',
        help='Path to training data CSV file'
    )
    
    parser.add_argument(
        '--model-name',
        type=str,
        default='churn_xgboost',
        help='Name for the trained model'
    )
    
    args = parser.parse_args()
    
    # Create trainer
    trainer = ModelTrainer(
        data_file=args.data_file,
        model_name=args.model_name
    )
    
    # Run training pipeline
    success = trainer.run_full_pipeline()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()