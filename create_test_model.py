"""
Create Test Model for Churn Prediction
app/ml/models/create_test_model.py

Run this script to create a simple test model for development
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_synthetic_data(n_samples=1000):
    """Create synthetic customer data for testing"""
    np.random.seed(42)
    
    # Generate base features
    tenure_months = np.random.exponential(24, n_samples)
    monthly_charges = np.random.normal(75, 25, n_samples)
    monthly_charges = np.clip(monthly_charges, 10, 200)
    
    total_charges = tenure_months * monthly_charges + np.random.normal(0, 100, n_samples)
    total_charges = np.clip(total_charges, 0, None)
    
    outstanding_balance = np.random.exponential(50, n_samples)
    total_payments = np.random.poisson(tenure_months * 0.8, n_samples)
    total_tickets = np.random.poisson(tenure_months * 0.1, n_samples)
    
    # Create DataFrame
    data = pd.DataFrame({
        'tenure_months': tenure_months,
        'monthly_charges': monthly_charges,
        'total_charges': total_charges,
        'outstanding_balance': outstanding_balance,
        'total_payments': total_payments,
        'total_tickets': total_tickets
    })
    
    # Generate churn labels (target variable)
    # Higher churn probability for:
    # - Short tenure
    # - High outstanding balance
    # - Many tickets
    # - Low payment consistency
    
    churn_prob = (
        0.1 +  # Base probability
        0.3 * (1 / (1 + np.exp(-(6 - tenure_months) / 3))) +  # Short tenure
        0.2 * (outstanding_balance / monthly_charges) / 5 +     # High balance ratio
        0.2 * (total_tickets / (tenure_months + 1)) * 5 +      # High ticket rate
        0.1 * (1 - (total_payments / (tenure_months + 1)))     # Low payment rate
    )
    
    # Clip probabilities
    churn_prob = np.clip(churn_prob, 0, 0.8)
    
    # Generate binary labels
    churn = np.random.binomial(1, churn_prob, n_samples)
    
    data['churn'] = churn
    
    logger.info(f"✅ Created synthetic dataset: {len(data)} samples, {churn.mean():.2%} churn rate")
    return data

def train_simple_model():
    """Train a simple Random Forest model for testing"""
    logger.info("🚀 Starting model training...")
    
    # 1. Create synthetic data
    data = create_synthetic_data(1000)
    
    # 2. Feature engineering (simplified version)
    features = data.copy()
    
    # Add derived features
    features['avg_monthly_payment'] = features['total_charges'] / (features['tenure_months'] + 1)
    features['balance_to_monthly_ratio'] = features['outstanding_balance'] / (features['monthly_charges'] + 1)
    features['tickets_per_month'] = features['total_tickets'] / (features['tenure_months'] + 1)
    features['payment_consistency'] = features['total_payments'] / (features['tenure_months'] + 1)
    
    # Risk flags
    features['high_balance_flag'] = (features['outstanding_balance'] > features['monthly_charges'] * 2).astype(int)
    features['low_usage_flag'] = (features['monthly_charges'] < 50).astype(int)
    features['high_tickets_flag'] = (features['total_tickets'] > 5).astype(int)
    features['new_customer_flag'] = (features['tenure_months'] < 6).astype(int)
    
    # Select feature columns
    feature_cols = [
        'tenure_months', 'monthly_charges', 'total_charges',
        'outstanding_balance', 'total_payments', 'total_tickets',
        'avg_monthly_payment', 'balance_to_monthly_ratio',
        'tickets_per_month', 'payment_consistency',
        'high_balance_flag', 'low_usage_flag', 'high_tickets_flag', 'new_customer_flag'
    ]
    
    X = features[feature_cols]
    y = features['churn']
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 4. Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # 5. Evaluate model
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    logger.info("📊 Model Performance:")
    logger.info(f"   AUC Score: {auc_score:.3f}")
    logger.info(f"   Test Accuracy: {model.score(X_test, y_test):.3f}")
    
    # 6. Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("🔍 Top Features:")
    for _, row in feature_importance.head(5).iterrows():
        logger.info(f"   {row['feature']}: {row['importance']:.3f}")
    
    # 7. Save model
    model_data = {
        'model': model,
        'feature_columns': feature_cols,
        'model_type': 'RandomForestClassifier',
        'version': '1.0.0',
        'metrics': {
            'auc_score': float(auc_score),
            'accuracy': float(model.score(X_test, y_test)),
            'n_features': len(feature_cols)
        },
        'created_at': datetime.utcnow().isoformat(),
        'feature_importance': feature_importance.to_dict('records')
    }
    
    # Ensure directory exists
    model_dir = 'app/ml/models/saved'
    os.makedirs(model_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(model_dir, 'churn_model_v1.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"✅ Model saved to: {model_path}")
    return model_path, model_data

def test_model_loading():
    """Test loading the saved model"""
    logger.info("🧪 Testing model loading...")
    
    model_path = 'app/ml/models/saved/churn_model_v1.pkl'
    
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        feature_cols = model_data['feature_columns']
        
        # Test prediction on sample data
        sample_data = pd.DataFrame({
            'tenure_months': [12],
            'monthly_charges': [75],
            'total_charges': [900],
            'outstanding_balance': [150],
            'total_payments': [12],
            'total_tickets': [3],
            'avg_monthly_payment': [75],
            'balance_to_monthly_ratio': [2],
            'tickets_per_month': [0.25],
            'payment_consistency': [1.0],
            'high_balance_flag': [1],
            'low_usage_flag': [0],
            'high_tickets_flag': [0],
            'new_customer_flag': [0]
        })
        
        prediction = model.predict_proba(sample_data[feature_cols])[0]
        
        logger.info(f"✅ Model loaded successfully!")
        logger.info(f"   Sample prediction: {prediction[1]:.3f} churn probability")
        logger.info(f"   Model version: {model_data['version']}")
        logger.info(f"   AUC Score: {model_data['metrics']['auc_score']:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🤖 Creating Test ML Model for Churn Prediction")
    print("=" * 50)
    
    # Create and train model
    model_path, model_data = train_simple_model()
    
    print("\n" + "=" * 50)
    
    # Test loading
    success = test_model_loading()
    
    if success:
        print("\n✅ TEST MODEL SETUP COMPLETE!")
        print(f"📁 Model saved at: {model_path}")
        print("🚀 Ready to test prediction service!")
    else:
        print("\n❌ Model setup failed. Check logs for details.")