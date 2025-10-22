# debug_prediction.py - Run this to test prediction service

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set Flask app context
os.environ['FLASK_APP'] = 'app'

from app import create_app
from app.extensions import db
from app.models.customer import Customer

def test_prediction_service():
    """Test prediction service to identify the error"""
    print("🧪 Testing Prediction Service...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test 1: Import prediction service
            print("\n1️⃣ Testing import...")
            try:
                from app.services.prediction_service import prediction_service
                print("✅ Prediction service imported successfully")
            except Exception as e:
                print(f"❌ Import failed: {e}")
                return
            
            # Test 2: Load model
            print("\n2️⃣ Testing model loading...")
            try:
                result = prediction_service.load_model()
                print(f"✅ Model loading result: {result}")
                print(f"   - Model loaded: {prediction_service.is_loaded}")
                print(f"   - Model type: {type(prediction_service.model)}")
                print(f"   - Scaler type: {type(prediction_service.scaler)}")
                print(f"   - Feature columns: {prediction_service.feature_columns}")
            except Exception as e:
                print(f"❌ Model loading failed: {e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                return
            
            # Test 3: Get a customer
            print("\n3️⃣ Testing customer retrieval...")
            try:
                customer = Customer.query.first()
                if customer:
                    print(f"✅ Found customer: {customer.name} (ID: {customer.id})")
                    
                    # Print customer attributes
                    attrs = ['monthly_charges', 'total_charges', 'contract_length', 
                            'phone_calls', 'support_interactions', 'last_payment_days', 
                            'service_issues', 'churn_probability', 'churn_risk']
                    
                    for attr in attrs:
                        value = getattr(customer, attr, 'NOT_FOUND')
                        print(f"   - {attr}: {value}")
                        
                else:
                    print("❌ No customers found in database")
                    return
            except Exception as e:
                print(f"❌ Customer retrieval failed: {e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                return
            
            # Test 4: Prepare features
            print("\n4️⃣ Testing feature preparation...")
            try:
                features_df = prediction_service._prepare_customer_features(customer)
                if features_df is not None:
                    print(f"✅ Features prepared successfully")
                    print(f"   - Shape: {features_df.shape}")
                    print(f"   - Columns: {list(features_df.columns)}")
                    print(f"   - Data:\n{features_df}")
                else:
                    print("❌ Feature preparation returned None")
                    return
            except Exception as e:
                print(f"❌ Feature preparation failed: {e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                return
            
            # Test 5: Make prediction
            print("\n5️⃣ Testing prediction...")
            try:
                result = prediction_service.predict_single_customer(customer.id)
                print(f"✅ Prediction result: {result}")
            except Exception as e:
                print(f"❌ Prediction failed: {e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                return
            
            print("\n🎉 All tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Critical test failure: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_prediction_service()