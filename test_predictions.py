"""
Test Predictions with Trained Model - FIXED VERSION
test_predictions.py

This script tests the trained model with real CRM data
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ml.models.churn_model import ChurnModel


def test_with_sample_customers():
    """Test predictions with sample customers from training data"""
    
    print("\n" + "="*60)
    print("TESTING CHURN PREDICTIONS")
    print("="*60)
    
    # Load trained model
    model_path = "app/ml/models/saved/churn_xgboost.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        print("\n💡 Train the model first:")
        print("   bash complete_ml_pipeline.sh")
        return False
    
    print(f"\n📦 Loading model from: {model_path}")
    
    # ✅ FIX: Use model_path instead of model_name
    model = ChurnModel(model_path=model_path)
    
    if not model.load(model_path):
        print("❌ Failed to load model")
        return False
    
    print("✅ Model loaded successfully")
    
    # Get model info
    info = model.get_model_info()
    print(f"\n📊 Model Info:")
    print(f"   Version: {info.get('version')}")
    print(f"   Trained: {info.get('trained_at')}")
    print(f"   Features: {info.get('num_features')}")
    
    # Load training data to get sample customers
    data_file = "app/ml/data/training_data.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ Training data not found: {data_file}")
        return False
    
    print(f"\n📊 Loading training data from: {data_file}")
    df = pd.read_csv(data_file)
    
    print(f"✅ Loaded {len(df)} customers")
    
    # Prepare features (exclude ID and target columns)
    exclude_cols = [
        'customer_id', 'id', 'churned', 'churn_score',
        'customer_name', 'name', 'email', 'phone', 'address',
        'signup_date', 'last_payment_date', 'last_ticket_date',
        'customer_email', 'secondary_email', 'created_at', 'updated_at',
        'disconnection_date', 'churned_date', 'date_installed'
    ]
    
    feature_cols = [
        col for col in df.columns 
        if col not in exclude_cols and df[col].dtype in ['int64', 'float64', 'bool']
    ]
    
    X = df[feature_cols].fillna(0)
    
    # Convert boolean to int
    for col in X.columns:
        if X[col].dtype == 'bool':
            X[col] = X[col].astype(int)
    
    print(f"\n🔧 Using {len(feature_cols)} features for prediction")
    
    # Make predictions on all customers
    print("\n🚀 Making predictions...")
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Add predictions to dataframe
    df['churn_prediction'] = predictions
    df['churn_probability'] = probabilities
    
    # Categorize risk
    def categorize_risk(prob):
        if prob >= 0.7:
            return 'HIGH'
        elif prob >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    df['risk_category'] = df['churn_probability'].apply(categorize_risk)
    
    # Summary statistics
    print("\n" + "="*60)
    print("PREDICTION SUMMARY")
    print("="*60)
    
    total = len(df)
    predicted_churn = predictions.sum()
    high_risk = (df['risk_category'] == 'HIGH').sum()
    medium_risk = (df['risk_category'] == 'MEDIUM').sum()
    low_risk = (df['risk_category'] == 'LOW').sum()
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Customers: {total}")
    print(f"   Predicted Churners: {predicted_churn} ({predicted_churn/total*100:.1f}%)")
    print(f"   Predicted Active: {total - predicted_churn} ({(total-predicted_churn)/total*100:.1f}%)")
    
    print(f"\n📊 Risk Distribution:")
    print(f"   HIGH Risk:   {high_risk:4d} ({high_risk/total*100:.1f}%)")
    print(f"   MEDIUM Risk: {medium_risk:4d} ({medium_risk/total*100:.1f}%)")
    print(f"   LOW Risk:    {low_risk:4d} ({low_risk/total*100:.1f}%)")
    
    # Show sample high-risk customers
    print("\n" + "="*60)
    print("TOP 10 HIGH-RISK CUSTOMERS")
    print("="*60)
    
    high_risk_customers = df[df['risk_category'] == 'HIGH'].sort_values(
        'churn_probability', ascending=False
    ).head(10)
    
    if len(high_risk_customers) > 0:
        for idx, row in high_risk_customers.iterrows():
            customer_id = row.get('id', row.get('customer_id', 'N/A'))
            customer_name = row.get('customer_name', 'N/A')
            prob = row['churn_probability']
            
            print(f"\n🔴 Customer: {customer_name} (ID: {customer_id})")
            print(f"   Churn Probability: {prob:.1%}")
            print(f"   Risk: {row['risk_category']}")
            
            # Show key indicators
            if 'total_tickets' in row:
                print(f"   Total Tickets: {int(row['total_tickets'])}")
            if 'total_payments' in row:
                print(f"   Total Payments: {int(row['total_payments'])}")
            if 'days_since_last_payment' in row and row['days_since_last_payment'] < 999:
                print(f"   Days Since Last Payment: {int(row['days_since_last_payment'])}")
            if 'tenure_months' in row:
                print(f"   Tenure: {int(row['tenure_months'])} months")
            if 'balance_amount' in row:
                print(f"   Balance: ${row['balance_amount']:.2f}")
    else:
        print("✅ No high-risk customers found!")
    
    # Show sample low-risk customers
    print("\n" + "="*60)
    print("SAMPLE LOW-RISK CUSTOMERS (Healthy)")
    print("="*60)
    
    low_risk_customers = df[df['risk_category'] == 'LOW'].sort_values(
        'churn_probability'
    ).head(5)
    
    for idx, row in low_risk_customers.iterrows():
        customer_id = row.get('id', row.get('customer_id', 'N/A'))
        customer_name = row.get('customer_name', 'N/A')
        prob = row['churn_probability']
        
        print(f"\n🟢 Customer: {customer_name} (ID: {customer_id})")
        print(f"   Churn Probability: {prob:.1%}")
        print(f"   Risk: {row['risk_category']}")
    
    # Calculate accuracy if we have actual labels
    if 'churned' in df.columns:
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        actual = df['churned']
        predicted = df['churn_prediction']
        
        accuracy = accuracy_score(actual, predicted)
        precision = precision_score(actual, predicted, zero_division=0)
        recall = recall_score(actual, predicted, zero_division=0)
        f1 = f1_score(actual, predicted, zero_division=0)
        
        print("\n" + "="*60)
        print("MODEL VALIDATION (on full dataset)")
        print("="*60)
        print(f"   Accuracy:  {accuracy:.1%}")
        print(f"   Precision: {precision:.1%}")
        print(f"   Recall:    {recall:.1%}")
        print(f"   F1 Score:  {f1:.1%}")
    
    # Save predictions
    output_file = "app/ml/data/predictions.csv"
    
    # Select relevant columns for output
    output_cols = ['id', 'churn_prediction', 'churn_probability', 'risk_category']
    if 'customer_name' in df.columns:
        output_cols.insert(1, 'customer_name')
    
    # Add key features
    key_features = ['total_payments', 'total_tickets', 'tenure_months', 
                   'days_since_last_payment', 'payment_frequency', 'status']
    for feat in key_features:
        if feat in df.columns:
            output_cols.append(feat)
    
    # Only include columns that exist
    output_cols = [col for col in output_cols if col in df.columns]
    
    df[output_cols].to_csv(output_file, index=False)
    
    print(f"\n💾 Predictions saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ PREDICTION TEST COMPLETE!")
    print("="*60)
    
    print(f"\n🎯 Model Performance Indicators:")
    print(f"   - {high_risk} customers need immediate attention")
    print(f"   - {medium_risk} customers require monitoring")
    print(f"   - {low_risk} customers are healthy")
    
    print(f"\n💡 Recommendations:")
    if high_risk > 0:
        print(f"   1. Review high-risk customers immediately")
        print(f"   2. Implement retention strategies")
        print(f"   3. Contact customers with overdue balances")
    else:
        print(f"   1. Continue monitoring customer health")
        print(f"   2. Maintain good service quality")
    
    return True


def test_single_customer():
    """Test prediction for a single customer with manual input"""
    
    print("\n" + "="*60)
    print("SINGLE CUSTOMER PREDICTION TEST")
    print("="*60)
    
    # Load model
    model_path = "app/ml/models/saved/churn_xgboost.pkl"
    model = ChurnModel(model_path=model_path)
    
    if not model.load(model_path):
        print("❌ Failed to load model")
        return False
    
    print("✅ Model loaded")
    
    # Create sample customer data matching actual features
    print("\n📝 Creating test customer profile...")
    
    sample_customer = pd.DataFrame([{
        'customer_phone': 0,
        'secondary_phone': 0,
        'customer_balance': 0,
        'status': 1,  # Active
        'balance': -500,  # Has debt
        'lead_id': 0,
        'region_id': 1,
        'is_ticket_sms': 0,
        'isonboarded': 1,
        'selfcare_pin': 0,
        'customer_special': 0,
        'recovered_qualified': 0,
        'cst_call': 0,
        'cst_winback_id': 0,
        'Update_Winbackonoffer': 0,
        'call_outcome': 0,
        'total_payments': 5,
        'days_since_last_payment': 90,
        'total_tickets': 8,
        'open_tickets': 3,
        'high_priority_tickets': 2,
        'days_since_last_ticket': 15,
        'tenure_days': 365,
        'tenure_months': 12,
        'is_active': 1,
        'balance_amount': -500,
        'payment_frequency': 0.4,
        'ticket_frequency': 0.7,
        'support_engagement_ratio': 1.6
    }])
    
    print("\n👤 Test Customer Profile:")
    for col, val in sample_customer.iloc[0].items():
        print(f"   {col:30s}: {val}")
    
    # Make prediction
    prediction = model.predict(sample_customer)[0]
    probability = model.predict_proba(sample_customer)[0]
    
    risk = 'HIGH' if probability >= 0.7 else 'MEDIUM' if probability >= 0.4 else 'LOW'
    
    print(f"\n🎯 Prediction Result:")
    print(f"   Will Churn: {'YES' if prediction == 1 else 'NO'}")
    print(f"   Churn Probability: {probability:.1%}")
    print(f"   Risk Category: {risk}")
    
    if risk == 'HIGH':
        print(f"\n⚠️  Action Required:")
        print(f"   - Contact customer immediately")
        print(f"   - Review outstanding balance")
        print(f"   - Address open support tickets")
    
    return True


def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("CHURN PREDICTION MODEL TESTING")
    print("="*60)
    
    # Test with real customers
    if not test_with_sample_customers():
        print("\n❌ Testing failed")
        return False
    
    # Test with single customer
    print("\n" + "="*60)
    test_single_customer()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE!")
    print("="*60)
    
    print("\n📋 Files Created:")
    print("   - app/ml/data/predictions.csv")
    
    print("\n🚀 Next Steps:")
    print("   1. Review predictions in app/ml/data/predictions.csv")
    print("   2. Start Flask app: python3 run.py")
    print("   3. View predictions in the web interface")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)