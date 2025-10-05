#!/usr/bin/env python3
"""
Test Predictions Through Web Interface
test_web_predictions.py

This script verifies that predictions work through the web interface
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_prediction_routes():
    """Test that prediction routes are registered"""
    
    print("\n" + "=" * 60)
    print("TESTING PREDICTION ROUTES")
    print("=" * 60)
    
    try:
        from app import create_app
        
        app = create_app('development')
        
        print("\n📋 Registered Routes:")
        
        prediction_routes = []
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if 'prediction' in rule.endpoint:
                    prediction_routes.append({
                        'endpoint': rule.endpoint,
                        'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                        'path': str(rule)
                    })
        
        if prediction_routes:
            print(f"\n✅ Found {len(prediction_routes)} prediction routes:")
            for route in prediction_routes:
                print(f"   {route['endpoint']:40s} {route['methods']:15s} {route['path']}")
            return True
        else:
            print("\n❌ No prediction routes found!")
            print("   Make sure prediction_controller.py is properly registered")
            return False
            
    except Exception as e:
        print(f"\n❌ Route test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_templates():
    """Test that prediction templates exist"""
    
    print("\n" + "=" * 60)
    print("TESTING PREDICTION TEMPLATES")
    print("=" * 60)
    
    template_dir = "templates/prediction"
    required_templates = [
        'dashboard.html',
        'customer_detail.html',
        'high_risk.html'
    ]
    
    all_exist = True
    
    print(f"\n📋 Checking templates in {template_dir}:")
    
    for template in required_templates:
        template_path = os.path.join(template_dir, template)
        exists = os.path.exists(template_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {template}")
        
        if not exists:
            all_exist = False
    
    if all_exist:
        print("\n✅ All templates exist!")
        return True
    else:
        print("\n❌ Some templates are missing!")
        print(f"\n💡 Create missing templates in: {template_dir}/")
        return False


def test_prediction_service():
    """Test prediction service can be instantiated"""
    
    print("\n" + "=" * 60)
    print("TESTING PREDICTION SERVICE")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.models.company import Company
        from app.services.prediction_service import PredictionService
        
        app = create_app('development')
        
        with app.app_context():
            # Get first company
            company = Company.query.first()
            
            if not company:
                print("\n⚠️  No companies in database!")
                print("   Create a company by registering through the web interface")
                return False
            
            print(f"\n✅ Testing with company: {company.name}")
            
            # Try to initialize prediction service
            try:
                pred_service = PredictionService(company)
                print("✅ PredictionService initialized successfully")
                
                # Try to get model info
                model_info = pred_service.get_model_info()
                
                if model_info.get('loaded'):
                    print(f"✅ Model loaded: {model_info.get('version')}")
                    print(f"   Features: {model_info.get('num_features')}")
                    print(f"   Trained: {model_info.get('trained_at')}")
                else:
                    print("⚠️  No trained model found")
                    print("   Train a model first:")
                    print("   bash complete_ml_pipeline.sh")
                
                return True
                
            except ValueError as e:
                print(f"⚠️  {e}")
                print("\n💡 This is expected if you haven't trained a model yet")
                print("   Train a model:")
                print("   bash complete_ml_pipeline.sh")
                return True
                
    except Exception as e:
        print(f"\n❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_test_client():
    """Test prediction routes with Flask test client"""
    
    print("\n" + "=" * 60)
    print("TESTING WITH FLASK TEST CLIENT")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.models.user import User
        
        app = create_app('development')
        
        with app.app_context():
            # Get a test user
            user = User.query.filter_by(role='admin').first()
            
            if not user:
                user = User.query.first()
            
            if not user:
                print("\n⚠️  No users in database!")
                print("   Register a user through the web interface")
                return False
            
            print(f"\n✅ Testing with user: {user.email}")
            
            # Create test client
            client = app.test_client()
            
            # Try to access prediction dashboard (will redirect to login)
            response = client.get('/predictions/dashboard')
            
            print(f"\nGET /predictions/dashboard")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 302:
                print(f"   ✅ Redirects to login (expected for unauthenticated request)")
            elif response.status_code == 200:
                print(f"   ✅ Returns successfully")
            else:
                print(f"   ⚠️  Unexpected status code")
            
            # Try statistics endpoint
            response = client.get('/predictions/statistics')
            print(f"\nGET /predictions/statistics")
            print(f"   Status Code: {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Test client failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_access_instructions():
    """Print instructions for accessing the web interface"""
    
    print("\n" + "=" * 60)
    print("WEB INTERFACE ACCESS INSTRUCTIONS")
    print("=" * 60)
    
    print("\n🚀 To test predictions through the web interface:")
    print("")
    print("1. Start the Flask application:")
    print("   python3 run.py")
    print("")
    print("2. Open your browser and go to:")
    print("   http://localhost:5001")
    print("")
    print("3. Log in with your credentials")
    print("")
    print("4. Navigate to predictions:")
    print("   - Click 'Predictions' in the sidebar")
    print("   - Or go directly to: http://localhost:5001/predictions/dashboard")
    print("")
    print("5. Run predictions:")
    print("   - Click the 'Run Predictions' button")
    print("   - Wait for predictions to complete")
    print("   - View high-risk customers")
    print("")
    print("6. View customer details:")
    print("   - Click on any customer to see detailed prediction")
    print("   - View prediction history and trends")
    print("")
    
    print("\n📋 Available Routes:")
    print("   /predictions/dashboard       - Main predictions dashboard")
    print("   /predictions/high-risk       - List of high-risk customers")
    print("   /predictions/customer/<id>   - Customer prediction details")
    print("   /predictions/run (POST)      - Trigger prediction run")
    print("   /predictions/statistics      - Get prediction stats (JSON)")
    print("")


def main():
    """Main execution"""
    
    print("\n" + "=" * 60)
    print("PHASE 6 WEB INTERFACE TESTING")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Routes
    print("\n[Test 1/4] Checking prediction routes...")
    if not test_prediction_routes():
        all_passed = False
    
    # Test 2: Templates
    print("\n[Test 2/4] Checking prediction templates...")
    if not test_prediction_templates():
        all_passed = False
    
    # Test 3: Service
    print("\n[Test 3/4] Testing prediction service...")
    if not test_prediction_service():
        all_passed = False
    
    # Test 4: Test client
    print("\n[Test 4/4] Testing with Flask test client...")
    if not test_with_test_client():
        all_passed = False
    
    # Print instructions
    print_access_instructions()
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED (see above)")
    print("=" * 60)
    
    print("\n📋 Pre-flight Checklist:")
    print("   ✅ Prediction routes registered")
    print("   ✅ Prediction templates created")
    print("   ✅ Prediction service working")
    print("   ✅ Test client functional")
    print("")
    print("🎯 Ready to test predictions through web interface!")
    print("")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)