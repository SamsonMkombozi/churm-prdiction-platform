#!/bin/bash

echo "🔧 Fixing train_model.py - Adding missing XGBClassifier import..."

# Backup original file
cp app/ml/training/train_model.py app/ml/training/train_model.py.backup

# Add the import at the top of the file after other imports
sed -i '/from app.ml.features.feature_engineering import FeatureEngineering/a\
\
# ✅ CRITICAL FIX: Import XGBClassifier\
from xgboost import XGBClassifier' app/ml/training/train_model.py

echo "✅ Fixed! Added XGBClassifier import"
echo ""
echo "📄 Backup saved to: app/ml/training/train_model.py.backup"
echo ""
echo "🚀 Now run:"
echo "   python3 app/ml/training/train_model.py --data-file app/ml/data/training_data.csv"
