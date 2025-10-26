"""
Database Migration - Add will_churn column
migrate_will_churn.py

Run this to add the will_churn column to existing predictions table
"""

def migrate_will_churn_column():
    """Add will_churn column to predictions table"""
    try:
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Migrating predictions table to add will_churn column...")
            
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('predictions')]
            
            if 'will_churn' in columns:
                print("✅ will_churn column already exists!")
                return
            
            print("📝 Adding will_churn column...")
            
            # Add the column
            with db.engine.connect() as conn:
                # SQLite syntax for adding column
                conn.execute(db.text(
                    "ALTER TABLE predictions ADD COLUMN will_churn BOOLEAN DEFAULT 0"
                ))
                conn.commit()
            
            print("✅ will_churn column added successfully!")
            
            # Update existing records based on churn_probability
            print("🔄 Updating existing predictions...")
            
            with db.engine.connect() as conn:
                # Set will_churn = 1 where churn_probability > 0.5
                result = conn.execute(db.text(
                    "UPDATE predictions SET will_churn = 1 WHERE churn_probability > 0.5"
                ))
                
                # Set will_churn = 0 where churn_probability <= 0.5
                conn.execute(db.text(
                    "UPDATE predictions SET will_churn = 0 WHERE churn_probability <= 0.5"
                ))
                
                conn.commit()
                
                print(f"✅ Updated {result.rowcount} existing prediction records")
            
            print("🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

def verify_migration():
    """Verify the migration worked"""
    try:
        from app import create_app
        from app.models.prediction import Prediction
        
        app = create_app()
        
        with app.app_context():
            print("\n🔍 Verifying migration...")
            
            # Count predictions by will_churn value
            total = Prediction.query.count()
            will_churn_true = Prediction.query.filter_by(will_churn=True).count()
            will_churn_false = Prediction.query.filter_by(will_churn=False).count()
            
            print(f"   Total predictions: {total}")
            print(f"   Will churn (True): {will_churn_true}")
            print(f"   Will not churn (False): {will_churn_false}")
            
            if will_churn_true + will_churn_false == total:
                print("✅ Migration verification successful!")
            else:
                print("⚠️ Migration verification found inconsistencies")
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    print("🗄️ Database Migration: Adding will_churn column")
    print("=" * 50)
    
    migrate_will_churn_column()
    verify_migration()
    
    print("\n📋 Next Steps:")
    print("1. Replace your prediction model with prediction_model_fixed.py")
    print("2. Restart your Flask application")
    print("3. Test the prediction functionality")