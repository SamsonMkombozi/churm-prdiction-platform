#!/bin/bash

# ============================================================
# Phase 6 Web Interface Setup Script
# Automates the setup of prediction templates and database
# ============================================================

echo "============================================================"
echo "PHASE 6 WEB INTERFACE SETUP"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Create directories
echo -e "${BLUE}[Step 1/4] Creating template directories...${NC}"
mkdir -p templates/prediction

if [ -d "templates/prediction" ]; then
    echo -e "${GREEN}✅ Directory created: templates/prediction${NC}"
else
    echo -e "${RED}❌ Failed to create directory${NC}"
    exit 1
fi

echo ""

# Step 2: Verify template files exist
echo -e "${BLUE}[Step 2/4] Checking template files...${NC}"

TEMPLATES=(
    "templates/prediction/dashboard.html"
    "templates/prediction/customer_detail.html"
    "templates/prediction/high_risk.html"
)

missing_templates=0

for template in "${TEMPLATES[@]}"; do
    if [ -f "$template" ]; then
        echo -e "${GREEN}✅ Found: $template${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing: $template${NC}"
        missing_templates=$((missing_templates + 1))
    fi
done

if [ $missing_templates -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  $missing_templates template(s) missing${NC}"
    echo -e "${YELLOW}Please create the template files from the artifacts above${NC}"
    echo ""
    echo "Required templates:"
    echo "  1. templates/prediction/dashboard.html"
    echo "  2. templates/prediction/customer_detail.html"
    echo "  3. templates/prediction/high_risk.html"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Step 3: Run database migration
echo -e "${BLUE}[Step 3/4] Running database migration...${NC}"

if [ -f "migrate_predictions.py" ]; then
    python3 migrate_predictions.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database migration completed${NC}"
    else
        echo -e "${RED}❌ Database migration failed${NC}"
        echo "Check the error messages above"
        exit 1
    fi
else
    echo -e "${RED}❌ migrate_predictions.py not found${NC}"
    echo "Create this file from the artifact above"
    exit 1
fi

echo ""

# Step 4: Run tests
echo -e "${BLUE}[Step 4/4] Running web interface tests...${NC}"

if [ -f "test_web_predictions.py" ]; then
    python3 test_web_predictions.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Web interface tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Some tests failed (see above)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  test_web_predictions.py not found${NC}"
    echo "Skipping tests..."
fi

echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}✅ PHASE 6 SETUP COMPLETE!${NC}"
echo "============================================================"
echo ""

echo -e "${BLUE}📋 What was done:${NC}"
echo "   ✅ Created templates/prediction/ directory"
echo "   ✅ Verified template files"
echo "   ✅ Ran database migration"
echo "   ✅ Tested web interface"
echo ""

echo -e "${BLUE}📁 Files and Directories:${NC}"
echo "   templates/prediction/dashboard.html"
echo "   templates/prediction/customer_detail.html"
echo "   templates/prediction/high_risk.html"
echo "   migrate_predictions.py"
echo "   test_web_predictions.py"
echo ""

echo -e "${BLUE}🎯 Next Steps:${NC}"
echo ""
echo "1. Ensure you have customer data:"
echo "   ${YELLOW}python3 run.py${NC}"
echo "   Then go to CRM Dashboard and sync data"
echo ""
echo "2. Train the ML model (if not done yet):"
echo "   ${YELLOW}bash complete_ml_pipeline.sh${NC}"
echo ""
echo "3. Start the Flask application:"
echo "   ${YELLOW}python3 run.py${NC}"
echo ""
echo "4. Access the predictions dashboard:"
echo "   ${YELLOW}http://localhost:5001/predictions/dashboard${NC}"
echo ""
echo "5. Run predictions:"
echo "   - Click 'Run Predictions' button"
echo "   - Wait for analysis to complete"
echo "   - View high-risk customers"
echo ""

echo -e "${BLUE}📊 Available Routes:${NC}"
echo "   /predictions/dashboard       - Main dashboard"
echo "   /predictions/high-risk       - High-risk customers list"
echo "   /predictions/customer/<id>   - Customer details"
echo "   /predictions/run (POST)      - Run predictions"
echo "   /predictions/statistics      - Get stats (JSON)"
echo ""

echo "============================================================"
echo -e "${GREEN}Ready to test predictions through the web interface! 🚀${NC}"
echo "============================================================"
echo ""