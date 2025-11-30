#!/usr/bin/env python3
"""
Database Verification Script
============================

Tests that all required tables and columns exist for churn prediction.

Usage:
    python verify_database.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import inspect
from datetime import datetime


class DatabaseVerifier:
    """Verify database schema for churn prediction"""
    
    # Define required columns for each table
    REQUIRED_SCHEMA = {
        'companies': [
            'id', 'name', 'postgres_host', 'postgres_database', 
            'postgres_username', 'postgres_password', 'sync_enabled',
            'last_sync', 'created_at'
        ],
        'users': [
            'id', 'company_id', 'email', 'password_hash', 
            'full_name', 'role', 'is_active', 'created_at'
        ],
        'customers': [
            # Core fields
            'id', 'company_id', 'crm_customer_id', 'customer_no',
            'customer_name', 'email', 'phone', 'status',
            
            # Critical churn fields
            'date_installed', 'disconnection_date', 'churned_date',
            'days_since_disconnection', 'months_stayed', 'tenure_months',
            
            # Payment metrics
            'total_payments', 'number_of_payments', 'missed_payments',
            'last_payment_date', 'average_payment_amount',
            
            # Ticket metrics
            'total_tickets', 'complaint_tickets', 'complaints_per_month',
            
            # Usage metrics
            'total_data_usage_gb', 'average_monthly_usage_gb',
            
            # Prediction results
            'churn_probability', 'risk_level', 'churn_score',
            
            # Timestamps
            'created_at', 'updated_at', 'synced_at'
        ],
        'payments': [
            'id', 'company_id', 'customer_id', 'crm_payment_id',
            'amount', 'payment_date', 'mpesa_ref', 'account_no',
            'status', 'is_refund', 'posted_to_ledgers',
            'created_at', 'synced_at'
        ],
        'tickets': [
            'id', 'company_id', 'customer_id', 'crm_ticket_id',
            'ticket_number', 'title', 'status', 'priority',
            'is_complaint', 'resolved_at', 'resolution_time_hours',
            'created_at', 'synced_at'
        ],
        'usage_stats': [
            'id', 'company_id', 'customer_id', 'crm_usage_id',
            'in_bytes', 'out_bytes', 'total_bytes', 
            'start_date', 'end_date', 'session_duration_minutes',
            'created_at', 'synced_at'
        ],
        'predictions': [
            'id', 'company_id', 'customer_id', 'churn_probability',
            'risk_level', 'confidence_score', 'model_version',
            'prediction_date', 'is_latest', 'key_factors',
            'created_at'
        ]
    }
    
    def __init__(self, app):
        self.app = app
        self.inspector = inspect(db.engine)
        self.results = {
            'tables': {},
            'missing_tables': [],
            'missing_columns': {},
            'success': True
        }
    
    def verify_all(self):
        """Run complete verification"""
        
        print("\n" + "=" * 80)
        print("🔍 VERIFYING CHURN PREDICTION DATABASE SCHEMA")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {db.engine.url}")
        print("=" * 80)
        
        # Get all existing tables
        existing_tables = self.inspector.get_table_names()
        
        print(f"\n📊 Found {len(existing_tables)} tables in database")
        
        # Verify each required table
        for table_name, required_cols in self.REQUIRED_SCHEMA.items():
            self._verify_table(table_name, required_cols, existing_tables)
        
        # Print summary
        self._print_summary()
        
        return self.results['success']
    
    def _verify_table(self, table_name, required_cols, existing_tables):
        """Verify a single table"""
        
        print(f"\n📋 Checking table: {table_name.upper()}")
        print("-" * 80)
        
        if table_name not in existing_tables:
            print(f"❌ Table '{table_name}' DOES NOT EXIST")
            self.results['missing_tables'].append(table_name)
            self.results['success'] = False
            return
        
        # Get existing columns
        existing_cols = [col['name'] for col in self.inspector.get_columns(table_name)]
        
        print(f"✅ Table exists with {len(existing_cols)} columns")
        
        # Check required columns
        missing_cols = []
        for col in required_cols:
            if col in existing_cols:
                print(f"  ✓ {col}")
            else:
                print(f"  ❌ MISSING: {col}")
                missing_cols.append(col)
        
        if missing_cols:
            self.results['missing_columns'][table_name] = missing_cols
            self.results['success'] = False
        
        # Store results
        self.results['tables'][table_name] = {
            'exists': True,
            'column_count': len(existing_cols),
            'required_columns': len(required_cols),
            'missing_columns': missing_cols,
            'status': 'complete' if not missing_cols else 'incomplete'
        }
    
    def _print_summary(self):
        """Print verification summary"""
        
        print("\n" + "=" * 80)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 80)
        
        # Table summary
        total_tables = len(self.REQUIRED_SCHEMA)
        existing_tables = len([t for t in self.results['tables'].values() if t['exists']])
        
        print(f"\n📋 Tables: {existing_tables}/{total_tables}")
        
        if self.results['missing_tables']:
            print(f"\n❌ Missing Tables ({len(self.results['missing_tables'])}):")
            for table in self.results['missing_tables']:
                print(f"  • {table}")
        
        # Column summary
        if self.results['missing_columns']:
            print(f"\n❌ Tables with Missing Columns ({len(self.results['missing_columns'])}):")
            for table, cols in self.results['missing_columns'].items():
                print(f"\n  📋 {table}:")
                for col in cols:
                    print(f"    • {col}")
        
        # Overall status
        print("\n" + "=" * 80)
        if self.results['success']:
            print("✅ DATABASE VERIFICATION PASSED")
            print("   All required tables and columns are present!")
        else:
            print("❌ DATABASE VERIFICATION FAILED")
            print("   Some tables or columns are missing.")
            print("\n💡 To fix, run the database initialization:")
            print("   python -c 'from app import create_app; from app.utils.database_init import initialize_database; app = create_app(); initialize_database(app)'")
        
        print("=" * 80 + "\n")
    
    def get_column_details(self, table_name):
        """Get detailed column information for a table"""
        
        if table_name not in self.inspector.get_table_names():
            return None
        
        columns = self.inspector.get_columns(table_name)
        
        print(f"\n📋 Detailed Schema for: {table_name.upper()}")
        print("=" * 80)
        print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10}")
        print("-" * 80)
        
        for col in columns:
            nullable = "YES" if col['nullable'] else "NO"
            print(f"{col['name']:<30} {str(col['type']):<20} {nullable:<10}")
        
        print("=" * 80)


def main():
    """Main verification function"""
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Create verifier
        verifier = DatabaseVerifier(app)
        
        # Run verification
        success = verifier.verify_all()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()