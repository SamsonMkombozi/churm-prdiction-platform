"""
Direct Table Name Fix Script
fix_table_names.py

Replace incorrect table names in your current CRM service file
"""

import os
import re

def fix_crm_service_table_names():
    """Fix table names in the CRM service file"""
    
    crm_service_path = "app/services/crm_service.py"
    
    if not os.path.exists(crm_service_path):
        print(f"❌ CRM service file not found: {crm_service_path}")
        return False
    
    try:
        # Read the current file
        with open(crm_service_path, 'r') as f:
            content = f.read()
        
        print("🔍 Current file read successfully")
        
        # Apply table name fixes
        fixes = [
            # Fix customer table name
            (r'FROM customers\b', 'FROM crm_customers'),
            (r'FROM "customers"', 'FROM "crm_customers"'),
            (r'FROM `customers`', 'FROM `crm_customers`'),
            
            # Fix payment table name  
            (r'FROM payments\b', 'FROM nav_mpesa_transactions'),
            (r'FROM "payments"', 'FROM "nav_mpesa_transactions"'),
            (r'FROM `payments`', 'FROM `nav_mpesa_transactions`'),
            
            # Fix ticket table name
            (r'FROM tickets\b', 'FROM crm_tickets'),
            (r'FROM "tickets"', 'FROM "crm_tickets"'),
            (r'FROM `tickets`', 'FROM `crm_tickets`'),
            
            # Note: spl_statistics is already correct
        ]
        
        # Apply each fix
        for old_pattern, new_pattern in fixes:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
                print(f"✅ Fixed: {old_pattern} → {new_pattern}")
        
        # Special fix for MPESA transaction field mapping
        mpesa_field_fixes = [
            # Map payment fields to MPESA fields  
            (r'tx_amount,', '"TransAmount" as tx_amount,'),
            (r'account_no,', '"BillRefNumber" as account_no,'),
            (r'phone_no,', '"MSISDN" as phone_no,'),
            (r'payer,', '"FirstName" as payer,'),
            (r'created_at,', '"TransTime" as created_at,'),
            (r'transaction_time,', '"TransTime" as transaction_time,'),
            (r'mpesa_reference,', '"TransID" as mpesa_reference,'),
        ]
        
        # Check if MPESA field mapping is needed
        if 'nav_mpesa_transactions' in content and '"TransAmount"' not in content:
            print("🔧 Applying MPESA field mapping...")
            # Add proper MPESA field mapping
            mpesa_select = '''
                SELECT 
                    "TransID" as id, 
                    "TransAmount" as tx_amount, 
                    "BillRefNumber" as account_no,
                    "MSISDN" as phone_no, 
                    "FirstName" as payer, 
                    "TransTime" as created_at,
                    "TransTime" as transaction_time, 
                    "TransID" as mpesa_reference,
                    TRUE as posted_to_ledgers,
                    FALSE as is_refund,
                    'completed' as status
                FROM nav_mpesa_transactions'''
            
            # Replace the generic payment select
            payment_select_pattern = r'SELECT\s+[^F]*FROM nav_mpesa_transactions'
            content = re.sub(payment_select_pattern, mpesa_select, content, flags=re.DOTALL)
            print("✅ Applied MPESA field mapping")
        
        # Write the fixed content back
        with open(crm_service_path, 'w') as f:
            f.write(content)
        
        print("✅ CRM service file updated with correct table names!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing CRM service: {e}")
        return False

def verify_table_names():
    """Verify the table names have been fixed"""
    
    crm_service_path = "app/services/crm_service.py"
    
    try:
        with open(crm_service_path, 'r') as f:
            content = f.read()
        
        print("\n🔍 Verifying table names in CRM service:")
        
        # Check for old incorrect table names
        incorrect_tables = ['FROM customers', 'FROM payments', 'FROM tickets']
        correct_tables = ['FROM crm_customers', 'FROM nav_mpesa_transactions', 'FROM crm_tickets']
        
        issues_found = []
        for incorrect in incorrect_tables:
            if incorrect in content:
                issues_found.append(incorrect)
        
        fixes_found = []
        for correct in correct_tables:
            if correct in content:
                fixes_found.append(correct)
        
        if issues_found:
            print("❌ Still found incorrect table names:")
            for issue in issues_found:
                print(f"   • {issue}")
        else:
            print("✅ No incorrect table names found")
        
        if fixes_found:
            print("✅ Found correct table names:")
            for fix in fixes_found:
                print(f"   • {fix}")
        
        return len(issues_found) == 0 and len(fixes_found) > 0
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False

def main():
    """Main function"""
    
    print("🔧 === FIXING CRM TABLE NAMES ===")
    
    # Step 1: Fix table names
    print("📝 Step 1: Applying table name fixes...")
    fix_success = fix_crm_service_table_names()
    
    # Step 2: Verify fixes
    print("🔍 Step 2: Verifying fixes...")
    verify_success = verify_table_names()
    
    # Summary
    print(f"\n📋 === SUMMARY ===")
    print(f"Table name fixes: {'✅ APPLIED' if fix_success else '❌ FAILED'}")
    print(f"Verification: {'✅ PASSED' if verify_success else '❌ FAILED'}")
    
    if fix_success and verify_success:
        print(f"\n🎉 SUCCESS! Table names have been fixed!")
        print(f"\nNext steps:")
        print(f"1. ✅ Table names updated in CRM service")
        print(f"2. 🔄 Restart your Flask application")
        print(f"3. 🧪 Test the CRM sync button")
        print(f"4. 🚀 Enjoy lightning-fast PostgreSQL sync!")
    else:
        print(f"\n❌ Table name fix failed. Manual intervention needed.")
        print(f"\nManual fix:")
        print(f"1. Edit app/services/crm_service.py")
        print(f"2. Replace 'FROM customers' with 'FROM crm_customers'")
        print(f"3. Replace 'FROM payments' with 'FROM nav_mpesa_transactions'")
        print(f"4. Replace 'FROM tickets' with 'FROM crm_tickets'")
    
    return fix_success and verify_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)