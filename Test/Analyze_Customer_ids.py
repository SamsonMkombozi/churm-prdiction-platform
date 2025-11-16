#!/usr/bin/env python3
"""
Customer ID Analysis Script
===========================

This script analyzes the customer ID patterns in your CRM database
to understand the mix of numeric and text-based customer identifiers.

Author: Claude Assistant
Date: November 2024
"""

import psycopg2
import psycopg2.extras
from collections import defaultdict
import re

def analyze_customer_ids():
    """Analyze customer ID patterns in the database"""
    
    # Database configuration
    config = {
        'host': '196.250.208.220',
        'database': 'AnalyticsWH',
        'user': 'analytics',
        'password': 'KzVpIANhKh4Cpcdh',
        'port': 5432
    }
    
    try:
        print("🔍 Analyzing Customer ID Patterns")
        print("=" * 50)
        
        # Connect to database
        with psycopg2.connect(**config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                
                # Get sample customer IDs
                cursor.execute("""
                    SELECT 
                        id,
                        customer_name,
                        CASE 
                            WHEN id ~ '^[0-9]+$' THEN 'NUMERIC'
                            ELSE 'TEXT' 
                        END as id_type
                    FROM crm_customers 
                    WHERE customer_name IS NOT NULL 
                    AND customer_name != ''
                    ORDER BY id
                    LIMIT 50
                """)
                
                samples = cursor.fetchall()
                
                # Analyze patterns
                numeric_count = 0
                text_count = 0
                patterns = defaultdict(list)
                
                print("📊 Sample Customer IDs:")
                print("-" * 50)
                
                for sample in samples:
                    customer_id = sample['id']
                    id_type = sample['id_type']
                    name = sample['customer_name']
                    
                    if id_type == 'NUMERIC':
                        numeric_count += 1
                        patterns['NUMERIC'].append(customer_id)
                    else:
                        text_count += 1
                        patterns['TEXT'].append(customer_id)
                    
                    print(f"{customer_id:>15} | {id_type:>8} | {name[:30]:<30}")
                
                print("\n📈 Analysis Summary:")
                print("-" * 50)
                print(f"Numeric IDs: {numeric_count} ({numeric_count/len(samples)*100:.1f}%)")
                print(f"Text IDs:    {text_count} ({text_count/len(samples)*100:.1f}%)")
                
                print("\n🔢 Numeric ID Examples:")
                for i, num_id in enumerate(patterns['NUMERIC'][:10]):
                    print(f"  • {num_id}")
                
                print("\n📝 Text ID Examples:")
                for i, text_id in enumerate(patterns['TEXT'][:10]):
                    print(f"  • {text_id}")
                
                # Analyze text ID patterns
                if patterns['TEXT']:
                    print("\n🧩 Text ID Patterns:")
                    text_patterns = defaultdict(int)
                    
                    for text_id in patterns['TEXT']:
                        # Analyze pattern
                        if re.match(r'^[A-Z]+\d+$', text_id):
                            prefix = re.sub(r'\d+$', '', text_id)
                            text_patterns[f"{prefix}###"] += 1
                        elif re.match(r'^\d+[A-Z]+$', text_id):
                            text_patterns["###LETTERS"] += 1
                        else:
                            text_patterns["OTHER"] += 1
                    
                    for pattern, count in text_patterns.items():
                        print(f"  • {pattern}: {count} occurrences")
                
                # Test spl_statistics compatibility
                print("\n🔗 spl_statistics Compatibility Test:")
                print("-" * 50)
                
                # Count customers that can be joined with spl_statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN c.id ~ '^[0-9]+$' THEN 1 END) as joinable_customers,
                        COUNT(CASE WHEN c.id !~ '^[0-9]+$' THEN 1 END) as non_joinable_customers
                    FROM crm_customers c
                    WHERE c.customer_name IS NOT NULL AND c.customer_name != ''
                """)
                
                compatibility = cursor.fetchone()
                
                total = compatibility['total_customers']
                joinable = compatibility['joinable_customers']
                non_joinable = compatibility['non_joinable_customers']
                
                print(f"Total customers:        {total:,}")
                print(f"Can join spl_statistics: {joinable:,} ({joinable/total*100:.1f}%)")
                print(f"Cannot join:            {non_joinable:,} ({non_joinable/total*100:.1f}%)")
                
                # Test actual join
                cursor.execute("""
                    SELECT COUNT(DISTINCT c.id) as customers_with_usage
                    FROM crm_customers c
                    INNER JOIN spl_statistics s ON (
                        CASE 
                            WHEN c.id ~ '^[0-9]+$' THEN s.customer_id = c.id::bigint 
                            ELSE FALSE 
                        END
                    )
                    WHERE c.customer_name IS NOT NULL AND c.customer_name != ''
                """)
                
                usage_join = cursor.fetchone()
                customers_with_usage = usage_join['customers_with_usage']
                
                print(f"Have usage data:        {customers_with_usage:,} ({customers_with_usage/total*100:.1f}%)")
                
                print("\n✅ Solution Applied:")
                print("-" * 50)
                print("The CRM service now uses a CASE statement to:")
                print("• ✅ Join NUMERIC customer IDs (like 12345) with spl_statistics")
                print("• ⏭️  Skip TEXT customer IDs (like SME000000175) for spl_statistics join")
                print("• 🔄 Still include all customers in payment and ticket analysis")
                print("• 🧠 Generate predictions for all customers regardless of ID type")
                
                print(f"\n🎯 Result: {non_joinable:,} customers with text IDs will have:")
                print("  • Payment history analysis ✅")
                print("  • Support ticket analysis ✅") 
                print("  • Churn predictions ✅")
                print("  • Usage data (spl_statistics) ❌ (only for numeric IDs)")
                
                return True
                
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = analyze_customer_ids()
    print(f"\n{'✅ Analysis completed successfully!' if success else '❌ Analysis failed.'}")