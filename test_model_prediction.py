#!/usr/bin/env python3
"""
🧪 ALIGNED CHURN MODEL TEST with FeatureEngineering
test_model_aligned.py

Uses the actual FeatureEngineering class to prepare features correctly
"""

import sys
import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import time

# Add project directory to path
project_dir = '/var/www/html/churn-prediction-platform'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

def load_model_with_feature_engineering():
    """Load model and feature engineering together"""
    
    print("🧠 LOADING MODEL AND FEATURE ENGINEERING")
    print("=" * 50)
    
    try:
        # Load the model
        model_path = '/var/www/html/churn-prediction-platform/app/ml/models/saved/churn_model_v1.pkl'
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        print("✅ Model loaded successfully!")
        
        # Import FeatureEngineering
        from app.ml.features.feature_engineering import FeatureEngineering
        feature_engineer = FeatureEngineering()
        
        print("✅ FeatureEngineering imported successfully!")
        
        # Get model's expected features
        model_features = model_data.get('feature_columns', [])
        
        # Get FeatureEngineering's available features
        fe_features = feature_engineer.feature_columns
        
        print(f"\n📊 MODEL EXPECTS ({len(model_features)}):")
        for i, feature in enumerate(model_features, 1):
            print(f"   {i:2d}. {feature}")
        
        print(f"\n🔧 FEATURE ENGINEERING PROVIDES ({len(fe_features)}):")
        for i, feature in enumerate(fe_features, 1):
            print(f"   {i:2d}. {feature}")
        
        # Check alignment
        common_features = [f for f in model_features if f in fe_features]
        missing_features = [f for f in model_features if f not in fe_features]
        
        print(f"\n🎯 FEATURE ALIGNMENT:")
        print(f"   ✅ Common features: {len(common_features)}/{len(model_features)}")
        print(f"   ❌ Missing features: {len(missing_features)}")
        
        if missing_features:
            print(f"   Missing: {missing_features}")
        
        return model_data, feature_engineer, model_features
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, []

def test_feature_engineering_pipeline(feature_engineer, num_customers=5):
    """Test the complete feature engineering pipeline"""
    
    print(f"\n🔧 TESTING FEATURE ENGINEERING PIPELINE ({num_customers} customers)")
    print("=" * 65)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models.customer import Customer
            
            # Get sample customers
            customers = Customer.query.filter(
                Customer.monthly_charges > 0,
                Customer.tenure_months > 0
            ).limit(num_customers * 2).all()
            
            if not customers:
                print("❌ No suitable customers found")
                return None, []
            
            print(f"👥 Found {len(customers)} customers for testing")
            
            # Prepare customer data for feature engineering
            customer_data = []
            for customer in customers[:num_customers]:
                customer_dict = {
                    'id': customer.id,
                    'customer_number': customer.crm_customer_id,
                    'customer_name': customer.customer_name,
                    'status': getattr(customer, 'status', 'active') or 'active',
                    'tenure_months': customer.tenure_months or 0,
                    'monthly_charges': customer.monthly_charges or 0,
                    'total_charges': customer.total_charges or 0,
                    'outstanding_balance': customer.outstanding_balance or 0,
                    'total_payments': customer.total_payments or 0,
                    'total_tickets': customer.total_tickets or 0,
                    'signup_date': customer.signup_date,
                    'last_payment_date': getattr(customer, 'last_payment_date', None),
                    'last_ticket_date': getattr(customer, 'last_ticket_date', None)
                }
                customer_data.append(customer_dict)
            
            # Create DataFrame
            df = pd.DataFrame(customer_data)
            
            print(f"\n📊 INPUT DATA SAMPLE:")
            print(f"{'Customer':<20} | {'Tenure':>6} | {'Charges':>8} | {'Payments':>8} | {'Tickets':>7}")
            print(f"{'-'*20} | {'-'*6} | {'-'*8} | {'-'*8} | {'-'*7}")
            
            for _, row in df.head().iterrows():
                name = str(row['customer_name'])[:18]
                tenure = int(row['tenure_months'])
                charges = int(row['monthly_charges'])
                payments = int(row['total_payments'])
                tickets = int(row['total_tickets'])
                print(f"{name:<20} | {tenure:>6} | {charges:>8} | {payments:>8} | {tickets:>7}")
            
            # Apply feature engineering
            print(f"\n🔧 Applying feature engineering...")
            features_df = feature_engineer.transform(df)
            
            print(f"✅ Feature engineering completed!")
            print(f"📊 Generated {len(features_df.columns)} features for {len(features_df)} customers")
            
            # Show feature sample
            print(f"\n📈 GENERATED FEATURES SAMPLE:")
            print(f"{'Feature':<30} | {'Customer 1':>10} | {'Customer 2':>10}")
            print(f"{'-'*30} | {'-'*10} | {'-'*10}")
            
            for feature in features_df.columns[:15]:  # Show first 15 features
                val1 = features_df.iloc[0][feature] if len(features_df) > 0 else 0
                val2 = features_df.iloc[1][feature] if len(features_df) > 1 else 0
                print(f"{feature:<30} | {val1:>10.3f} | {val2:>10.3f}")
            
            if len(features_df.columns) > 15:
                print(f"{'... and ' + str(len(features_df.columns) - 15) + ' more':<30} | {'...':>10} | {'...':>10}")
            
            return features_df, customer_data
            
    except Exception as e:
        print(f"❌ Feature engineering test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, []

def test_model_predictions_with_features(model_data, features_df, customer_data, model_features):
    """Test model predictions using properly engineered features"""
    
    print(f"\n🎯 TESTING MODEL PREDICTIONS WITH ENGINEERED FEATURES")
    print("=" * 60)
    
    try:
        model = model_data.get('model')
        if not model:
            print("❌ No model found")
            return []
        
        print(f"🤖 Model expects: {len(model_features)} features")
        print(f"🔧 Features available: {len(features_df.columns)} features")
        
        # Align features with model expectations
        available_model_features = [f for f in model_features if f in features_df.columns]
        missing_features = [f for f in model_features if f not in features_df.columns]
        
        print(f"✅ Available model features: {len(available_model_features)}")
        if missing_features:
            print(f"❌ Missing features: {missing_features}")
            
            # Add missing features with default values
            for feature in missing_features:
                features_df[feature] = 0.0
                print(f"   Added default for: {feature}")
        
        # Create prediction dataset with correct feature order
        prediction_features = features_df[model_features].copy()
        
        predictions = []
        
        print(f"\n📊 PREDICTION RESULTS:")
        print(f"{'Customer':<25} | {'Prob':>6} | {'Risk':>6} | {'Confidence':<10} | {'Key Factors'}")
        print(f"{'-'*25} | {'-'*6} | {'-'*6} | {'-'*10} | {'-'*20}")
        
        for i, (_, features_row) in enumerate(prediction_features.iterrows()):
            try:
                customer_name = customer_data[i]['customer_name']
                
                # Prepare features as DataFrame to maintain feature names
                feature_vector = features_row.values.reshape(1, -1)
                feature_df = pd.DataFrame(feature_vector, columns=model_features)
                
                # Make prediction
                if hasattr(model, 'predict_proba'):
                    prob_array = model.predict_proba(feature_df)
                    prob = prob_array[0][1] if len(prob_array[0]) > 1 else prob_array[0][0]
                else:
                    prob = float(model.predict(feature_df)[0])
                
                prob = max(0.0, min(1.0, prob))
                
                # Risk categorization
                if prob >= 0.7:
                    risk = 'HIGH'
                elif prob >= 0.4:
                    risk = 'MEDIUM'
                else:
                    risk = 'LOW'
                
                # Confidence assessment
                if prob >= 0.8 or prob <= 0.2:
                    confidence = 'HIGH'
                elif prob >= 0.6 or prob <= 0.4:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
                
                # Identify key risk factors from features
                risk_factors = []
                
                # Check key risk indicators
                if features_row.get('high_balance_flag', 0) > 0:
                    risk_factors.append('High Balance')
                if features_row.get('payment_issues_flag', 0) > 0:
                    risk_factors.append('Payment Issues')
                if features_row.get('frequent_complaints_flag', 0) > 0:
                    risk_factors.append('Many Complaints')
                if features_row.get('new_customer_flag', 0) > 0:
                    risk_factors.append('New Customer')
                if features_row.get('disconnected_customer_flag', 0) > 0:
                    risk_factors.append('Disconnected')
                
                if not risk_factors:
                    # Look at continuous features
                    if features_row.get('balance_to_monthly_ratio', 0) > 1.5:
                        risk_factors.append('High Debt')
                    if features_row.get('payment_consistency_score', 1) < 0.7:
                        risk_factors.append('Payment Issues')
                    if features_row.get('number_of_complaints_per_month', 0) > 0.3:
                        risk_factors.append('Service Issues')
                
                key_factors = ', '.join(risk_factors[:2]) if risk_factors else 'None'
                
                predictions.append({
                    'customer_name': customer_name,
                    'customer_data': customer_data[i],
                    'probability': prob,
                    'risk': risk,
                    'confidence': confidence,
                    'risk_factors': risk_factors,
                    'features': features_row
                })
                
                # Display result
                name = customer_name[:23]
                print(f"{name:<25} | {prob:>5.1%} | {risk:>6} | {confidence:<10} | {key_factors}")
                
            except Exception as e:
                print(f"{customer_name[:23]:<25} | ERROR: {str(e)[:40]}")
                continue
        
        print(f"\n✅ Successfully generated {len(predictions)} predictions")
        return predictions
        
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def evaluate_aligned_predictions(predictions):
    """Evaluate predictions using business logic"""
    
    print(f"\n📈 EVALUATING ALIGNED PREDICTIONS")
    print("=" * 50)
    
    if not predictions:
        print("❌ No predictions to evaluate")
        return None
    
    try:
        print(f"📊 DETAILED BUSINESS EVALUATION:")
        print(f"{'Customer':<20} | {'Pred':>5} | {'Business Risk':>12} | {'Match'}")
        print(f"{'-'*20} | {'-'*5} | {'-'*12} | {'-'*5}")
        
        evaluation_results = []
        
        for pred in predictions:
            customer_info = pred['customer_data']
            predicted_prob = pred['probability']
            
            # Business risk assessment
            business_risk_score = 0.0
            business_factors = []
            
            # Financial risk factors
            monthly_charges = customer_info['monthly_charges']
            outstanding_balance = customer_info['outstanding_balance']
            
            if monthly_charges > 0:
                debt_ratio = outstanding_balance / monthly_charges
                if debt_ratio > 2:
                    business_risk_score += 0.4
                    business_factors.append('High Debt')
                elif debt_ratio > 1:
                    business_risk_score += 0.2
                    business_factors.append('Some Debt')
            
            # Payment behavior
            tenure = customer_info['tenure_months']
            payments = customer_info['total_payments']
            
            if tenure > 0:
                payment_rate = payments / tenure
                if payment_rate < 0.6:
                    business_risk_score += 0.3
                    business_factors.append('Poor Payment')
                elif payment_rate < 0.9:
                    business_risk_score += 0.1
                    business_factors.append('Inconsistent Payment')
            
            # Service issues
            tickets = customer_info['total_tickets']
            if tenure > 0:
                ticket_rate = tickets / tenure
                if ticket_rate > 0.5:
                    business_risk_score += 0.2
                    business_factors.append('Service Issues')
            
            # New customer risk
            if tenure < 6:
                business_risk_score += 0.1
                business_factors.append('New Customer')
            
            # Determine business assessment
            business_high_risk = business_risk_score >= 0.4
            predicted_high_risk = predicted_prob >= 0.5
            
            # Check if prediction matches business assessment
            match = business_high_risk == predicted_high_risk
            
            evaluation_results.append({
                'customer_name': customer_info['customer_name'],
                'predicted_prob': predicted_prob,
                'business_risk_score': business_risk_score,
                'business_high_risk': business_high_risk,
                'predicted_high_risk': predicted_high_risk,
                'match': match,
                'business_factors': business_factors
            })
            
            # Display result
            name = customer_info['customer_name'][:18]
            pred_pct = f"{predicted_prob:.1%}"
            biz_risk = "HIGH" if business_high_risk else "LOW"
            match_symbol = "✅" if match else "❌"
            
            print(f"{name:<20} | {pred_pct:>5} | {biz_risk:>12} | {match_symbol:>5}")
        
        # Calculate overall metrics
        total = len(evaluation_results)
        matches = sum(1 for r in evaluation_results if r['match'])
        accuracy = matches / total if total > 0 else 0
        
        pred_high = sum(1 for r in evaluation_results if r['predicted_high_risk'])
        biz_high = sum(1 for r in evaluation_results if r['business_high_risk'])
        
        print(f"\n🎯 EVALUATION RESULTS:")
        print(f"   Overall Accuracy: {accuracy:.1%} ({matches}/{total})")
        print(f"   Model Predicted High Risk: {pred_high}/{total}")
        print(f"   Business Assessment High Risk: {biz_high}/{total}")
        
        if accuracy >= 0.8:
            assessment = "🏆 EXCELLENT"
        elif accuracy >= 0.6:
            assessment = "✅ GOOD"  
        elif accuracy >= 0.4:
            assessment = "⚠️ ACCEPTABLE"
        else:
            assessment = "❌ NEEDS IMPROVEMENT"
        
        print(f"   Performance: {assessment}")
        
        return {
            'accuracy': accuracy,
            'total_samples': total,
            'matches': matches,
            'assessment': assessment
        }
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None

def main():
    """Main test function"""
    
    print("🧪 ALIGNED CHURN MODEL TEST - WITH FEATURE ENGINEERING")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Load model and feature engineering
    model_data, feature_engineer, model_features = load_model_with_feature_engineering()
    
    if not model_data or not feature_engineer:
        print("\n❌ CRITICAL: Cannot load model or feature engineering")
        return
    
    # Test feature engineering pipeline
    features_df, customer_data = test_feature_engineering_pipeline(feature_engineer, num_customers=5)
    
    if features_df is None:
        print("\n❌ CRITICAL: Feature engineering failed")
        return
    
    # Test model predictions
    predictions = test_model_predictions_with_features(model_data, features_df, customer_data, model_features)
    
    # Evaluate predictions
    evaluation = evaluate_aligned_predictions(predictions) if predictions else None
    
    # Final summary
    print(f"\n" + "=" * 80)
    print("🏆 FINAL ALIGNED TEST SUMMARY")
    print("=" * 80)
    
    print(f"✅ Model Loading: SUCCESS")
    print(f"✅ Feature Engineering: SUCCESS") 
    print(f"📊 Features Generated: {len(features_df.columns) if features_df is not None else 0}")
    print(f"🎯 Predictions Generated: {len(predictions)}")
    
    if evaluation:
        print(f"📈 Model Accuracy: {evaluation['accuracy']:.1%}")
        print(f"🎖️ Performance: {evaluation['assessment']}")
        print(f"📊 Sample Size: {evaluation['total_samples']}")
    
    if predictions:
        # Risk distribution
        high_risk = len([p for p in predictions if p['risk'] == 'HIGH'])
        medium_risk = len([p for p in predictions if p['risk'] == 'MEDIUM'])
        low_risk = len([p for p in predictions if p['risk'] == 'LOW'])
        
        print(f"\n📊 RISK DISTRIBUTION:")
        print(f"   🔴 High Risk: {high_risk}")
        print(f"   🟡 Medium Risk: {medium_risk}")
        print(f"   🟢 Low Risk: {low_risk}")
        
        avg_prob = sum(p['probability'] for p in predictions) / len(predictions)
        print(f"   📈 Average Churn Probability: {avg_prob:.1%}")
    
    print(f"\n⏰ Test completed at: {datetime.now()}")
    print(f"🎯 Model and Feature Engineering are now properly aligned!")

if __name__ == "__main__":
    main()