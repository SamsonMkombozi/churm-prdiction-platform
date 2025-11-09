#!/bin/bash

# 🚨 CRM SERVICE DIAGNOSTIC AND FIX SCRIPT
# This script will help you find and fix the PostgreSQL table name issue

echo "🔍 === CRM SERVICE DIAGNOSTIC SCRIPT ==="
echo

# Step 1: Find all crm_service.py files
echo "📁 Step 1: Locating all crm_service.py files..."
find /var/www/html/churn-prediction-platform -name "*crm_service*" -type f 2>/dev/null
echo

# Step 2: Check the problematic line in current files
echo "🔍 Step 2: Checking for the problematic 'FROM customers' line..."
grep -n "FROM customers" /var/www/html/churn-prediction-platform/app/services/crm_service.py 2>/dev/null || echo "✅ No 'FROM customers' found in main file"
echo

# Step 3: Search for any file containing the problematic query
echo "🔍 Step 3: Searching for ANY file with 'FROM customers' query..."
find /var/www/html/churn-prediction-platform -name "*.py" -exec grep -l "FROM customers" {} \; 2>/dev/null
echo

# Step 4: Check current file content
echo "📄 Step 4: Current crm_service.py file info..."
if [ -f "/var/www/html/churn-prediction-platform/app/services/crm_service.py" ]; then
    echo "File exists. Size: $(wc -l < /var/www/html/churn-prediction-platform/app/services/crm_service.py) lines"
    echo "Last modified: $(stat -c %y /var/www/html/churn-prediction-platform/app/services/crm_service.py)"
    echo "First few lines containing 'customers':"
    grep -n "customers" /var/www/html/churn-prediction-platform/app/services/crm_service.py | head -5 2>/dev/null || echo "No 'customers' references found"
else
    echo "❌ File not found!"
fi
echo

# Step 5: Check if there's a compiled Python cache
echo "🗂️ Step 5: Checking for Python cache files..."
find /var/www/html/churn-prediction-platform -name "__pycache__" -type d
find /var/www/html/churn-prediction-platform -name "*.pyc" -type f | head -5
echo

echo "🔧 === RECOMMENDED ACTIONS ==="
echo "1. If any .pyc files found, delete them: find . -name '*.pyc' -delete"
echo "2. If __pycache__ folders found, delete them: find . -name '__pycache__' -exec rm -rf {} +"
echo "3. Replace crm_service.py with the fixed version"
echo "4. Restart your Flask application completely"
echo

echo "🚀 QUICK FIX COMMANDS:"
echo "cd /var/www/html/churn-prediction-platform"
echo "find . -name '*.pyc' -delete"
echo "find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null"
echo "# Then replace the crm_service.py file and restart Flask"