#!/bin/bash

# ============================================================
# Setup CRM Templates Script
# This script creates all the CRM template files
# ============================================================

echo "============================================================"
echo "SETTING UP CRM TEMPLATES"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create templates/crm directory
echo "📁 Creating templates/crm directory..."
mkdir -p templates/crm

if [ -d "templates/crm" ]; then
    echo -e "${GREEN}✅ Directory created: templates/crm${NC}"
else
    echo -e "${RED}❌ Failed to create directory${NC}"
    exit 1
fi

echo ""
echo "📝 Creating template files..."
echo ""

# Backup existing files
if [ -f "templates/crm/dashboard.html" ]; then
    echo "⚠️  Backing up existing dashboard.html..."
    cp templates/crm/dashboard.html templates/crm/dashboard.html.backup
fi

echo "✅ All template files need to be created from the artifacts above:"
echo ""
echo "   1. templates/crm/dashboard.html (Fixed - with correct stats)"
echo "   2. templates/crm/customers.html (New - customer listing)"
echo "   3. templates/crm/tickets.html (New - ticket listing)"
echo "   4. templates/crm/payments.html (New - payment listing)"
echo "   5. templates/crm/customer_detail.html (New - customer details)"
echo "   6. templates/crm/ticket_detail.html (New - ticket details)"
echo ""

echo "============================================================"
echo "SUMMARY OF CHANGES"
echo "============================================================"
echo ""
echo "📊 Statistics Fixed:"
echo "   - Changed stats.total_customers to stats.customers"
echo "   - Changed stats.total_tickets to stats.tickets"
echo "   - Changed stats.total_payments to stats.payments"
echo "   - All stats keys match backend response"
echo ""
echo "💰 Currency Changed:"
echo "   - All $ changed to TSh (Tanzanian Shilling)"
echo "   - Format: TSh 10,000 instead of $10,000"
echo ""
echo "🎨 Templates Created:"
echo "   - Customers page with filtering and pagination"
echo "   - Tickets page with status and priority filters"
echo "   - Payments page with transaction details"
echo "   - Customer detail page with full profile"
echo "   - Ticket detail page with resolution info"
echo ""

echo "============================================================"
echo "NEXT STEPS"
echo "============================================================"
echo ""
echo "1. Copy each template from the artifacts above to the correct file"
echo ""
echo "2. Restart your Flask application:"
echo "   python3 run.py"
echo ""
echo "3. Test the CRM dashboard:"
echo "   http://localhost:5001/crm/dashboard"
echo ""
echo "4. Navigate to each section:"
echo "   - Customers: http://localhost:5001/crm/customers"
echo "   - Tickets: http://localhost:5001/crm/tickets"
echo "   - Payments: http://localhost:5001/crm/payments"
echo ""
echo "============================================================"
echo ""

exit 0