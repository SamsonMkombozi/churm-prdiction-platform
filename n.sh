#!/bin/bash

# ============================================================
# Apply CRM Field Name Fixes
# This script fixes the field mapping for your CRM API
# ============================================================

echo "============================================================"
echo "APPLYING CRM FIELD NAME FIXES"
echo "============================================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Backup original files
echo "📁 Creating backups..."
cp app/repositories/payment_repository.py app/repositories/payment_repository.py.backup_$(date +%Y%m%d_%H%M%S)
cp app/repositories/ticket_repository.py app/repositories/ticket_repository.py.backup_$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}✅ Backups created${NC}"
echo ""

echo "⚠️  ACTION REQUIRED:"
echo ""
echo "1. Replace app/repositories/payment_repository.py"
echo "   with the code from: 'Final Fixed Payment Repository'"
echo ""
echo "2. Replace app/repositories/ticket_repository.py"
echo "   with the code from: 'Final Fixed Ticket Repository'"
echo ""
echo "3. Restart Flask:"
echo "   python3 run.py"
echo ""
echo "4. Sync CRM data again:"
echo "   Go to CRM Dashboard → Click 'Sync CRM Data'"
echo ""

echo "============================================================"
echo "KEY FIELD MAPPINGS FOR YOUR CRM:"
echo "============================================================"
echo ""
echo "Customers:"
echo "  ✅ id: '1014000001'"
echo ""
echo "Payments:"
echo "  ✅ account_no: '1014000001' (links to customer)"
echo "  ✅ transaction_amount: payment amount"
echo "  ✅ transaction_time: payment date"
echo "  ✅ mpesa_reference: transaction ID"
echo ""
echo "Tickets:"
echo "  ✅ customer_no: '1014005949' (links to customer)"
echo "  ✅ subject: ticket title"
echo "  ✅ message: ticket description"
echo "  ✅ priority: ticket priority"
echo "  ✅ status: ticket status"
echo ""
echo "============================================================"