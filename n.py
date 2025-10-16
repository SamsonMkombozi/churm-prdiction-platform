"""
CRM Data Diagnostic Script
diagnose_crm_data.py

Run this to diagnose customer ID mismatches between customers and payments
"""

import requests
import sys

CRM_API_URL = "https://palegreen-porpoise-596991.hostingersite.com/Web_CRM/api.php"

def fetch_data(table_name):
    """Fetch data from CRM API"""
    try:
        url = f"{CRM_API_URL}?table={table_name}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict):
            if 'error' in data:
                return []
            return data.get('data') or data.get('records') or [data]
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"Error fetching {table_name}: {e}")
        return []

def main():
    print("="*80)
    print("CRM DATA DIAGNOSTIC TOOL")
    print("="*80)
    
    # Fetch customers
    print("\n📊 Fetching customers...")
    customers = fetch_data('customers')
    print(f"   Found {len(customers)} customers")
    
    # Fetch payments
    print("\n💰 Fetching payments...")
    payments = fetch_data('payments')
    print(f"   Found {len(payments)} payments")
    
    if not customers:
        print("\n❌ No customers found - cannot diagnose")
        return
    
    if not payments:
        print("\n⚠️  No payments found - nothing to diagnose")
        return
    
    # Analyze customer IDs
    print("\n" + "="*80)
    print("CUSTOMER ID ANALYSIS")
    print("="*80)
    
    # Sample first customer
    sample_customer = customers[0]
    print("\n📝 Sample Customer Record:")
    print(f"   Keys: {list(sample_customer.keys())}")
    print(f"   Sample: {sample_customer}")
    
    # Extract all customer IDs
    customer_ids = set()
    for c in customers:
        cid = c.get('id') or c.get('customer_id') or c.get('account_no')
        if cid:
            customer_ids.add(str(cid))
    
    print(f"\n✅ Found {len(customer_ids)} unique customer IDs")
    print(f"   Sample IDs: {list(customer_ids)[:10]}")
    
    # Analyze payment customer references
    print("\n" + "="*80)
    print("PAYMENT CUSTOMER REFERENCE ANALYSIS")
    print("="*80)
    
    # Sample first payment
    sample_payment = payments[0]
    print("\n📝 Sample Payment Record:")
    print(f"   Keys: {list(sample_payment.keys())}")
    print(f"   Sample: {sample_payment}")
    
    # Check what field payments use for customer reference
    payment_customer_fields = [
        'account_no', 'payer', 'customer_id', 'customerId', 
        'customer_no', 'cust_id', 'account_number'
    ]
    
    print("\n🔍 Checking which field payments use for customer reference:")
    for field in payment_customer_fields:
        if field in sample_payment:
            print(f"   ✓ Found field: '{field}' = {sample_payment.get(field)}")
    
    # Extract payment customer IDs
    payment_customer_ids = set()
    payment_field_used = None
    
    for p in payments:
        for field in payment_customer_fields:
            val = p.get(field)
            if val:
                payment_customer_ids.add(str(val))
                if not payment_field_used:
                    payment_field_used = field
                break
    
    print(f"\n✅ Found {len(payment_customer_ids)} unique customer IDs in payments")
    print(f"   Primary field used: '{payment_field_used}'")
    print(f"   Sample IDs: {list(payment_customer_ids)[:10]}")
    
    # Find mismatches
    print("\n" + "="*80)
    print("MISMATCH ANALYSIS")
    print("="*80)
    
    missing_customers = payment_customer_ids - customer_ids
    
    print(f"\n❌ Payment customer IDs NOT found in customer table: {len(missing_customers)}")
    if missing_customers:
        print(f"   Sample missing IDs: {list(missing_customers)[:20]}")
    
    orphan_customers = customer_ids - payment_customer_ids
    print(f"\n⚠️  Customers with NO payments: {len(orphan_customers)}")
    if orphan_customers:
        print(f"   Sample IDs: {list(orphan_customers)[:20]}")
    
    # Analyze customer names
    print("\n" + "="*80)
    print("CUSTOMER NAME ANALYSIS")
    print("="*80)
    
    customers_without_names = 0
    name_fields_found = set()
    
    for c in customers:
        # Check what name fields exist
        for field in ['name', 'customer_name', 'full_name', 'account_name']:
            if field in c:
                name_fields_found.add(field)
        
        # Check if customer has a name
        has_name = False
        for field in name_fields_found:
            val = c.get(field)
            if val and str(val).strip() and str(val).strip() != 'None':
                has_name = True
                break
        
        if not has_name:
            customers_without_names += 1
    
    print(f"\n📝 Name fields found in customer data: {name_fields_found}")
    print(f"❌ Customers without names: {customers_without_names} ({customers_without_names/len(customers)*100:.1f}%)")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    print("\n✅ To fix the sync issues:")
    print(f"   1. Payment repository should use '{payment_field_used}' field to link customers")
    print(f"   2. Customer repository should handle {customers_without_names} customers without names")
    print(f"   3. Need to handle {len(missing_customers)} payments with non-existent customer IDs")
    
    if missing_customers:
        print("\n⚠️  CRITICAL: Many payments reference customers that don't exist!")
        print("   This suggests:")
        print("   - Customer IDs in payments don't match customer IDs in customer table")
        print("   - OR customers were deleted but payments remain")
        print("   - OR payments use a different ID format")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()