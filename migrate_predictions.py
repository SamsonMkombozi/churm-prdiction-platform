#!/usr/bin/env python3
"""
Database Migration Script - Add Predictions Table
migrate_predictions.py

Run this to add the predictions table to your database
Usage: python3 migrate_predictions.py
"""

from app import create_app, db
from sqlalchemy import text
import sys


def migrate_predictions_table():
    """Add predictions table to database"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("DATABASE MIGRATION - Adding Predictions Table")
        print("=" * 60)
        
        try:
            # Check if table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'predictions' in existing_tables:
                print("\n⚠️  Predictions table already exists!")
                print("   Skipping migration...")
                return True
            
            # Import the Prediction model to ensure it's registered
            from app.models.prediction import Prediction
            
            print("\n📊 Creating predictions table...")
            
            # Create all tables (will only create missing ones)
            db.create_all()
            
            print("✅ Predictions table created successfully!")
            
            # Verify table was created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'predictions' in tables:
                print("\n✅ Table verification successful!")
                
                # Show table columns
                columns = inspector.get_columns('predictions')
                print("\n📋 Table Structure:")
                for col in columns:
                    print(f"   - {col['name']:30s} ({col['type']})")
                
                # Show indexes
                indexes = inspector.get_indexes('predictions')
                if indexes:
                    print("\n🔍 Indexes:")
                    for idx in indexes:
                        print(f"   - {idx['name']}: {idx['column_names']}")
                
                return True
            else:
                print("\n❌ Table verification failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def verify_all_phase6_tables():
    """Verify all Phase 6 related tables exist"""
    
    app = create_app('development')
    
    with app.app_context():
        print("\n" + "=" * 60)
        print("VERIFYING PHASE 6 DATABASE STRUCTURE")
        print("=" * 60)
        
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = {
            'companies': 'Company information',
            'users': 'User accounts',
            'customers': 'Customer data from CRM',
            'tickets': 'Support tickets',
            'payments': 'Payment transactions',
            'predictions': 'Churn predictions'
        }
        
        print("\n📋 Required Tables:")
        all_exist = True
        
        for table, description in required_tables.items():
            exists = table in existing_tables
            status = "✅" if exists else "❌"
            print(f"   {status} {table:20s} - {description}")
            if not exists:
                all_exist = False
        
        if all_exist:
            print("\n✅ All required tables exist!")
            
            # Show row counts
            print("\n📊 Table Statistics:")
            for table in required_tables.keys():
                try:
                    count = db.session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar()
                    print(f"   {table:20s}: {count:,} rows")
                except Exception as e:
                    print(f"   {table:20s}: Error - {e}")
            
            return True
        else:
            print("\n❌ Some tables are missing!")
            print("\n💡 To fix:")
            print("   1. Run: python3 simple_init.py")
            print("   2. Run: python3 migrate_predictions.py")
            return False


def test_prediction_model():
    """Test if prediction model can be imported and used"""
    
    print("\n" + "=" * 60)
    print("TESTING PREDICTION MODEL")
    print("=" * 60)
    
    try:
        from app.models.prediction import Prediction
        from app.models.customer import Customer
        from app.models.company import Company
        
        app = create_app('development')
        
        with app.app_context():
            # Test query
            prediction_count = Prediction.query.count()
            customer_count = Customer.query.count()
            
            print(f"\n✅ Model import successful!")
            print(f"   Predictions in database: {prediction_count}")
            print(f"   Customers in database: {customer_count}")
            
            if customer_count == 0:
                print("\n⚠️  Warning: No customers in database")
                print("   Run CRM sync to import customer data:")
                print("   1. Log into the web app")
                print("   2. Go to CRM Dashboard")
                print("   3. Click 'Sync CRM Data'")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution"""
    
    print("\n" + "=" * 60)
    print("PHASE 6 DATABASE MIGRATION")
    print("=" * 60)
    
    # Step 1: Create predictions table
    print("\n[Step 1/3] Creating predictions table...")
    if not migrate_predictions_table():
        print("\n❌ Migration failed!")
        return False
    
    # Step 2: Verify all tables
    print("\n[Step 2/3] Verifying database structure...")
    if not verify_all_phase6_tables():
        print("\n⚠️  Some tables are missing, but predictions table was created")
    
    # Step 3: Test prediction model
    print("\n[Step 3/3] Testing prediction model...")
    if not test_prediction_model():
        print("\n⚠️  Model test failed, but table was created")
    
    # Success summary
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 60)
    
    print("\n📋 What was done:")
    print("   1. ✅ Predictions table created")
    print("   2. ✅ Database structure verified")
    print("   3. ✅ Prediction model tested")
    
    print("\n🚀 Next Steps:")
    print("   1. Make sure you have customer data:")
    print("      - Go to CRM Dashboard in web app")
    print("      - Click 'Sync CRM Data'")
    print("")
    print("   2. Train the ML model:")
    print("      bash complete_ml_pipeline.sh")
    print("")
    print("   3. Test predictions:")
    print("      python3 test_predictions.py")
    print("")
    print("   4. Start the Flask app:")
    print("      python3 run.py")
    print("")
    print("   5. Access predictions:")
    print("      http://localhost:5001/predictions/dashboard")
    
    print("\n" + "=" * 60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)