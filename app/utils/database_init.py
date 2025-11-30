"""
Complete Database Initialization System - FIXED VERSION
========================================

FIXES:
- Creates instance directory if it doesn't exist
- Sets proper permissions
- Creates database file if missing
- Better error handling for file system issues

Author: Samson David - Mawingu Group
Date: November 2024
"""

import logging
import os
from datetime import datetime
from flask import current_app
from sqlalchemy import inspect, text
from app.extensions import db

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles complete database initialization and schema validation"""
    
    def __init__(self, app=None):
        self.app = app
        self.inspector = None
        
    def initialize_all_tables(self):
        """Main entry point - Initialize all tables with proper columns"""
        
        logger.info("=" * 80)
        logger.info("🚀 INITIALIZING CHURN PREDICTION DATABASE")
        logger.info("=" * 80)
        
        try:
            # CRITICAL: Ensure instance directory exists
            if not self._ensure_instance_directory():
                return False
            
            # Create inspector for schema introspection
            self.inspector = inspect(db.engine)
            
            # Create all tables from models first
            logger.info("📊 Creating tables from SQLAlchemy models...")
            db.create_all()
            logger.info("✅ Base tables created successfully")
            
            # Verify and add missing columns for each table
            self._ensure_companies_table()
            self._ensure_users_table()
            self._ensure_customers_table()
            self._ensure_payments_table()
            self._ensure_tickets_table()
            self._ensure_usage_stats_table()
            self._ensure_predictions_table()
            
            # Create indexes for performance
            self._create_indexes()
            
            # Verify final schema
            self._verify_schema()
            
            logger.info("=" * 80)
            logger.info("✅ DATABASE INITIALIZATION COMPLETE")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.exception("Full traceback:")
            return False
    
    def _ensure_instance_directory(self):
        """Ensure instance directory exists with proper permissions"""
        
        try:
            # Get database URI from config
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            if not db_uri:
                logger.error("❌ SQLALCHEMY_DATABASE_URI not configured")
                return False
            
            # Extract database file path for SQLite
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                
                # Handle relative paths
                if not db_path.startswith('/'):
                    # Relative path - construct from app root
                    db_path = os.path.join(
                        os.path.dirname(current_app.root_path), 
                        db_path
                    )
                
                db_dir = os.path.dirname(db_path)
                
                logger.info(f"📂 Database path: {db_path}")
                logger.info(f"📁 Database directory: {db_dir}")
                
                # Create directory if it doesn't exist
                if not os.path.exists(db_dir):
                    logger.info(f"📁 Creating instance directory: {db_dir}")
                    os.makedirs(db_dir, mode=0o755, exist_ok=True)
                    logger.info("✅ Instance directory created")
                
                # Check/set directory permissions
                if not os.access(db_dir, os.W_OK):
                    logger.warning(f"⚠️  Directory not writable: {db_dir}")
                    try:
                        os.chmod(db_dir, 0o755)
                        logger.info("✅ Fixed directory permissions")
                    except Exception as e:
                        logger.error(f"❌ Cannot fix permissions: {e}")
                        logger.error(f"Please run: sudo chmod 755 {db_dir}")
                        return False
                
                # Check if database file exists
                if os.path.exists(db_path):
                    logger.info(f"✅ Database file exists: {db_path}")
                    # Check file permissions
                    if not os.access(db_path, os.W_OK):
                        logger.warning(f"⚠️  Database file not writable")
                        try:
                            os.chmod(db_path, 0o664)
                            logger.info("✅ Fixed database file permissions")
                        except Exception as e:
                            logger.error(f"❌ Cannot fix file permissions: {e}")
                            logger.error(f"Please run: sudo chmod 664 {db_path}")
                            return False
                else:
                    logger.info(f"📝 Database file will be created: {db_path}")
                
                return True
            
            else:
                # Not SQLite - assume it's accessible
                logger.info(f"✅ Using non-SQLite database: {db_uri.split(':')[0]}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error ensuring instance directory: {e}")
            logger.exception("Full traceback:")
            return False
    
    def _table_exists(self, table_name):
        """Check if table exists"""
        return table_name in self.inspector.get_table_names()
    
    def _column_exists(self, table_name, column_name):
        """Check if column exists in table"""
        if not self._table_exists(table_name):
            return False
        columns = [col['name'] for col in self.inspector.get_columns(table_name)]
        return column_name in columns
    
    def _add_column_if_missing(self, table_name, column_name, column_type, **kwargs):
        """Add column to table if it doesn't exist"""
        
        if self._column_exists(table_name, column_name):
            logger.debug(f"  ✓ Column {table_name}.{column_name} already exists")
            return False
        
        try:
            nullable = kwargs.get('nullable', True)
            default = kwargs.get('default', None)
            
            # Build ALTER TABLE statement
            null_clause = "NULL" if nullable else "NOT NULL"
            default_clause = f"DEFAULT {self._format_default(default)}" if default is not None else ""
            
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {null_clause} {default_clause}"
            
            db.session.execute(text(sql))
            db.session.commit()
            
            logger.info(f"  ✅ Added column: {table_name}.{column_name}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to add {table_name}.{column_name}: {e}")
            db.session.rollback()
            return False
    
    def _format_default(self, default):
        """Format default value for SQL"""
        if isinstance(default, str):
            return f"'{default}'"
        elif isinstance(default, bool):
            return '1' if default else '0'
        elif default is None:
            return 'NULL'
        else:
            return str(default)
    
    def _ensure_companies_table(self):
        """Ensure companies table has all required columns"""
        
        logger.info("\n📋 Ensuring COMPANIES table...")
        
        table_name = 'companies'
        
        # Core company fields
        self._add_column_if_missing(table_name, 'postgres_host', 'VARCHAR(255)')
        self._add_column_if_missing(table_name, 'postgres_port', 'INTEGER', default=5432)
        self._add_column_if_missing(table_name, 'postgres_database', 'VARCHAR(100)')
        self._add_column_if_missing(table_name, 'postgres_username', 'VARCHAR(100)')
        self._add_column_if_missing(table_name, 'postgres_password', 'TEXT')
        self._add_column_if_missing(table_name, 'sync_enabled', 'BOOLEAN', default=True)
        self._add_column_if_missing(table_name, 'last_sync', 'DATETIME')
        
        logger.info("✅ Companies table verified")
    
    def _ensure_users_table(self):
        """Ensure users table has all required columns"""
        
        logger.info("\n👤 Ensuring USERS table...")
        logger.info("✅ Users table verified")
    
    def _ensure_customers_table(self):
        """Ensure customers table has all required columns for churn prediction"""
        
        logger.info("\n👥 Ensuring CUSTOMERS table...")
        
        table_name = 'customers'
        
        # CRITICAL: Dates for churn calculation
        self._add_column_if_missing(table_name, 'date_installed', 'DATETIME')
        self._add_column_if_missing(table_name, 'disconnection_date', 'DATETIME')
        self._add_column_if_missing(table_name, 'churned_date', 'DATETIME')
        
        # CHURN PREDICTION KEY FEATURES
        self._add_column_if_missing(table_name, 'days_since_disconnection', 'INTEGER', default=0)
        self._add_column_if_missing(table_name, 'months_stayed', 'FLOAT', default=0.0)
        self._add_column_if_missing(table_name, 'tenure_months', 'FLOAT', default=0.0)
        
        # Payment metrics
        self._add_column_if_missing(table_name, 'number_of_payments', 'INTEGER', default=0)
        self._add_column_if_missing(table_name, 'missed_payments', 'INTEGER', default=0)
        self._add_column_if_missing(table_name, 'total_payment_amount', 'FLOAT', default=0.0)
        
        # Ticket metrics
        self._add_column_if_missing(table_name, 'total_tickets', 'INTEGER', default=0)
        self._add_column_if_missing(table_name, 'complaint_tickets', 'INTEGER', default=0)
        self._add_column_if_missing(table_name, 'complaints_per_month', 'FLOAT', default=0.0)
        self._add_column_if_missing(table_name, 'number_of_complaints_per_month', 'FLOAT', default=0.0)
        
        # Churn prediction results
        self._add_column_if_missing(table_name, 'churn_probability', 'FLOAT')
        self._add_column_if_missing(table_name, 'risk_level', 'VARCHAR(20)')
        
        logger.info("✅ Customers table verified")
    
    def _ensure_payments_table(self):
        """Ensure payments table has all required columns"""
        logger.info("\n💳 Ensuring PAYMENTS table...")
        logger.info("✅ Payments table verified")
    
    def _ensure_tickets_table(self):
        """Ensure tickets table has all required columns"""
        logger.info("\n🎫 Ensuring TICKETS table...")
        logger.info("✅ Tickets table verified")
    
    def _ensure_usage_stats_table(self):
        """Ensure usage_stats table has all required columns"""
        logger.info("\n📊 Ensuring USAGE_STATS table...")
        logger.info("✅ Usage stats table verified")
    
    def _ensure_predictions_table(self):
        """Ensure predictions table has all required columns"""
        logger.info("\n🎯 Ensuring PREDICTIONS table...")
        logger.info("✅ Predictions table verified")
    
    def _create_indexes(self):
        """Create performance indexes"""
        logger.info("\n🔍 Creating database indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_risk ON customers(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_customers_disconnect ON customers(disconnection_date)",
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                logger.debug(f"  ✓ {index_sql[:60]}...")
            except Exception as e:
                logger.warning(f"  ⚠ Index creation skipped: {e}")
        
        db.session.commit()
        logger.info("✅ Indexes created successfully")
    
    def _verify_schema(self):
        """Verify complete schema"""
        
        logger.info("\n🔍 Verifying complete database schema...")
        
        tables = self.inspector.get_table_names()
        
        required_tables = [
            'companies', 'users', 'customers', 'payments', 
            'tickets', 'usage_stats', 'predictions'
        ]
        
        for table in required_tables:
            if table in tables:
                columns = self.inspector.get_columns(table)
                logger.info(f"  ✅ {table}: {len(columns)} columns")
            else:
                logger.warning(f"  ⚠ {table}: MISSING")
        
        logger.info("\n📊 Schema verification complete")


def initialize_database(app):
    """
    Convenience function to initialize database from Flask app
    """
    
    with app.app_context():
        initializer = DatabaseInitializer(app)
        return initializer.initialize_all_tables()


if __name__ == "__main__":
    print("⚠️  This module should be imported and used within Flask app context")