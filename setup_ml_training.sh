#!/bin/bash

# ============================================================
# Complete ML Pipeline for Churn Prediction
# This script fetches CRM data, prepares it, and trains the model
# ============================================================

echo "============================================================"
echo "CHURN PREDICTION ML PIPELINE"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p app/ml/data
mkdir -p app/ml/models/saved
mkdir -p app/ml/training
mkdir -p app/ml/features

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 1: Fetch and prepare data
echo "============================================================"
echo "STEP 1: FETCH AND PREPARE CRM DATA"
echo "============================================================"
echo ""

python3 app/ml/training/fetch_and_prepare_data.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data preparation failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Data preparation complete${NC}"
echo ""

# Step 2: Train model
echo "============================================================"
echo "STEP 2: TRAIN CHURN PREDICTION MODEL"
echo "============================================================"
echo ""

python3 app/ml/training/train_model.py --data-file app/ml/data/training_data.csv --model-name churn_xgboost

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Model training failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Model training complete${NC}"
echo ""

# Step 3: Summary
echo "============================================================"
echo "✅ ML PIPELINE COMPLETE!"
echo "============================================================"
echo ""
echo "📁 Files created:"
echo "   - app/ml/data/training_data.csv (Training data)"
echo "   - app/ml/models/saved/churn_xgboost.pkl (Trained model)"
echo "   - app/ml/models/saved/churn_xgboost_metadata.json (Metadata)"
echo ""
echo "🚀 Next steps:"
echo "   1. Test predictions: python3 test_predictions.py"
echo "   2. Start Flask app: python3 run.py"
echo "   3. Access predictions via API or web interface"
echo ""
echo "============================================================"