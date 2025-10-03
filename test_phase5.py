"""
Test Phase 5: ML Model Setup
Run this to verify Phase 5 setup
"""
import sys
import os

print("="*60)
print("PHASE 5 SETUP VERIFICATION")
print("="*60)

# Check directory structure
print("\n1. Checking directory structure...")
required_dirs = [
    'app/ml',
    'app/ml/models',
    'app/ml/models/saved',
    'app/ml/features',
    'app/ml/training'
]

all_dirs_exist = True
for directory in required_dirs:
    if os.path.exists(directory):
        print(f"   ✅ {directory}")
    else:
        print(f"   ❌ {directory} - MISSING")
        all_dirs_exist = False

# Check if files exist
print("\n2. Checking Python files...")
required_files = [
    'app/ml/__init__.py',
    'app/ml/features/__init__.py',
    'app/ml/features/feature_engineering.py',
    'app/ml/models/__init__.py',
    'app/ml/models/churn_model.py',
    'app/ml/training/__init__.py',
    'app/ml/training/train_model.py',
    'app/services/prediction_service.py'
]

all_files_exist = True
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - MISSING")
        all_files_exist = False

# Try imports
print("\n3. Testing imports...")
try:
    from app.ml.features.feature_engineering import FeatureEngineering
    print("   ✅ FeatureEngineering")
except Exception as e:
    print(f"   ❌ FeatureEngineering: {e}")
    all_files_exist = False

try:
    from app.ml.models.churn_model import ChurnModel
    print("   ✅ ChurnModel")
except Exception as e:
    print(f"   ❌ ChurnModel: {e}")
    all_files_exist = False

try:
    from app.ml.training.train_model import ModelTrainer
    print("   ✅ ModelTrainer")
except Exception as e:
    print(f"   ❌ ModelTrainer: {e}")
    all_files_exist = False

try:
    from app.services.prediction_service import PredictionService
    print("   ✅ PredictionService")
except Exception as e:
    print(f"   ❌ PredictionService: {e}")
    all_files_exist = False

# Check dependencies
print("\n4. Checking ML dependencies...")
try:
    import xgboost
    print(f"   ✅ xgboost {xgboost.__version__}")
except:
    print("   ❌ xgboost - NOT INSTALLED")
    all_files_exist = False

try:
    import pandas
    print(f"   ✅ pandas {pandas.__version__}")
except:
    print("   ❌ pandas - NOT INSTALLED")
    all_files_exist = False

try:
    import numpy
    print(f"   ✅ numpy {numpy.__version__}")
except:
    print("   ❌ numpy - NOT INSTALLED")
    all_files_exist = False

try:
    import sklearn
    print(f"   ✅ scikit-learn {sklearn.__version__}")
except:
    print("   ❌ scikit-learn - NOT INSTALLED")
    all_files_exist = False

try:
    import joblib
    print(f"   ✅ joblib")
except:
    print("   ❌ joblib - NOT INSTALLED")
    all_files_exist = False

# Final result
print("\n" + "="*60)
if all_dirs_exist and all_files_exist:
    print("✅ PHASE 5 SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("   1. Make sure you have customer data in the database")
    print("   2. Train a model: python app/ml/training/train_model.py --company-id 1")
    print("   3. Test predictions in Phase 6")
    sys.exit(0)
else:
    print("❌ PHASE 5 SETUP INCOMPLETE")
    print("="*60)
    print("\nPlease ensure all files are created correctly.")
    sys.exit(1)
