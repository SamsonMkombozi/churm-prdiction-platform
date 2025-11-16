"""
MINIMAL Disconnection-Based CRM Service (Conflict-Free)
=======================================================

This version works with your existing Customer model without SQLAlchemy conflicts.
It only adds the disconnection logic to your existing CRM service.

Author: Samson David - Mawingu Group  
Date: November 2024
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app.extensions import db
import traceback
import time
import logging
import json

logger = logging.getLogger(__name__)

class MinimalDisconnectionCRMService:
    """Minimal CRM Service with disconnection-based churn prediction - no model conflicts"""
    
    def __init__(self, company):
        self.company = company
        self.connection = None
        logger.info(f"Initializing MINIMAL Disconnection CRM Service for: {company.name}")
        
        self.sync_stats = {
            'start_time': None,
            'customers': {'updated': 0, 'errors': 0, 'disconnected_found': 0},
            'disconnection_analysis': {'total_with_real_dates': 0, 'placeholder_dates': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0},
            'total_records': 0,
            'sync_duration': 0
        }
    
    def test_postgresql_connection(self):
        """Test PostgreSQL connection and analyze disconnection data"""
        
        logger.info("Testing PostgreSQL connection for disconnection analysis")
        
        try:
            pg_config = self.company.get_postgresql_config()
            
            if not all([pg_config['host'], pg_config['database'], pg_config['username'], pg_config['password']]):
                return {'success': False, 'message': 'PostgreSQL configuration incomplete'}
            
            with psycopg2.connect(**{
                'host': pg_config['host'],
                'port': pg_config['port'], 
                'dbname': pg_config['database'],
                'user': pg_config['username'],
                'password': pg_config['password']
            }) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    
                    # Analyze disconnection data
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_customers,
                            COUNT(CASE WHEN churned_date = '0001-01-01 00:00:00' OR churned_date = '0001-01-01' THEN 1 END) as placeholder_dates,
                            COUNT(CASE WHEN churned_date != '0001-01-01 00:00:00' AND churned_date != '0001-01-01' AND churned_date IS NOT NULL THEN 1 END) as real_disconnections
                        FROM crm_customers
                        WHERE customer_name IS NOT NULL AND customer_name != ''
                    """)
                    
                    stats = cursor.fetchone()
                    
                    return {
                        'success': True,
                        'message': '✅ DISCONNECTION-BASED PostgreSQL connection successful!',
                        'database_version': version,
                        'disconnection_analysis': {
                            'total_customers': stats['total_customers'],
                            'placeholder_dates': stats['placeholder_dates'],
                            'real_disconnections': stats['real_disconnections'],
                            'active_percentage': f"{(stats['placeholder_dates']/stats['total_customers']*100):.1f}%" if stats['total_customers'] > 0 else '0%',
                            'disconnected_percentage': f"{(stats['real_disconnections']/stats['total_customers']*100):.1f}%" if stats['total_customers'] > 0 else '0%'
                        },
                        'enhanced_features': [
                            '🔥 DISCONNECTION-BASED: Uses actual churned_date from CRM',
                            '📊 BUSINESS LOGIC: 90/60 day disconnection rules', 
                            '⚡ CONFLICT-FREE: Works with existing models',
                            'Real vs placeholder date separation'
                        ]
                    }
                    
        except Exception as e:
            return {'success': False, 'message': f'PostgreSQL connection failed: {str(e)}'}
    
    def sync_customers_with_disconnection_analysis(self):
        """Sync customers with disconnection-based churn analysis"""
        
        self.sync_stats['start_time'] = time.time()
        logger.info("Starting disconnection-based customer sync")
        
        try:
            conn = self._get_postgresql_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get customers with disconnection analysis
            query = """
                SELECT 
                    c.id::text as crm_customer_id,
                    c.customer_name,
                    c.customer_phone,
                    c.customer_balance,
                    c.status,
                    c.churned_date,
                    c.date_installed,
                    c.created_at,
                    -- Analyze disconnection status
                    CASE 
                        WHEN c.churned_date = '0001-01-01 00:00:00' OR c.churned_date = '0001-01-01' OR c.churned_date IS NULL THEN 'ACTIVE'
                        ELSE 'DISCONNECTED'
                    END as disconnection_status,
                    -- Calculate days since disconnection for valid dates
                    CASE 
                        WHEN c.churned_date != '0001-01-01 00:00:00' AND c.churned_date != '0001-01-01' AND c.churned_date IS NOT NULL THEN
                            EXTRACT(DAY FROM CURRENT_DATE - c.churned_date::date)::INTEGER
                        ELSE 0
                    END as days_since_disconnection
                FROM crm_customers c
                WHERE c.customer_name IS NOT NULL 
                AND c.customer_name != ''
                AND c.customer_name NOT ILIKE 'test%'
                ORDER BY c.churned_date DESC NULLS LAST
                LIMIT 1000  -- Process in batches
            """
            
            cursor.execute(query)
            customers_data = cursor.fetchall()
            
            logger.info(f"Retrieved {len(customers_data)} customers for disconnection analysis")
            
            # Process customers and update with disconnection data
            for customer_row in customers_data:
                try:
                    customer_data = dict(customer_row)
                    self._process_customer_with_disconnection_analysis(customer_data)
                    self.sync_stats['customers']['updated'] += 1
                    
                except Exception as e:
                    logger.warning(f"Customer {customer_row.get('crm_customer_id')} processing error: {e}")
                    self.sync_stats['customers']['errors'] += 1
                    continue
            
            # Calculate stats
            elapsed_time = time.time() - self.sync_stats['start_time']
            self.sync_stats['sync_duration'] = round(elapsed_time, 2)
            self.sync_stats['total_records'] = len(customers_data)
            
            logger.info(f"Disconnection-based sync completed in {elapsed_time:.1f}s")
            
            return {
                'success': True,
                'message': f'Disconnection-based sync completed! Processed {len(customers_data)} customers',
                'stats': self.sync_stats,
                'disconnection_summary': self.sync_stats['disconnection_analysis']
            }
            
        except Exception as e:
            logger.error(f"Disconnection sync failed: {str(e)}")
            raise Exception(f"Disconnection sync failed: {str(e)}")
        
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def _process_customer_with_disconnection_analysis(self, customer_data):
        """Process individual customer with disconnection analysis"""
        
        try:
            # Import Customer model dynamically to avoid conflicts
            from app.models.customer import Customer
            
            crm_id = customer_data['crm_customer_id']
            
            # Find existing customer
            customer = Customer.query.filter_by(
                company_id=self.company.id,
                crm_customer_id=crm_id
            ).first()
            
            if not customer:
                # Create new customer if not exists
                customer = Customer(
                    company_id=self.company.id,
                    crm_customer_id=crm_id,
                    customer_name=customer_data.get('customer_name', 'Unknown'),
                    phone=customer_data.get('customer_phone'),
                    outstanding_balance=float(customer_data.get('customer_balance', 0) or 0),
                    status=customer_data.get('status', 'active'),
                    created_at=datetime.utcnow()
                )
                db.session.add(customer)
                db.session.flush()
            
            # Update customer with disconnection analysis
            self._update_customer_disconnection_fields(customer, customer_data)
            
            # Calculate churn risk based on disconnection
            churn_assessment = self._calculate_disconnection_churn_risk(customer_data)
            
            # Update customer with churn prediction
            customer.churn_risk = churn_assessment['risk_level']
            customer.churn_probability = churn_assessment['probability']
            
            # Update disconnection fields if they exist
            if hasattr(customer, 'disconnection_date'):
                disconnection_date = self._parse_disconnection_date(customer_data.get('churned_date'))
                customer.disconnection_date = disconnection_date
                customer.days_since_disconnection = customer_data.get('days_since_disconnection', 0)
            
            customer.updated_at = datetime.utcnow()
            
            # Track statistics
            if customer_data['disconnection_status'] == 'DISCONNECTED':
                self.sync_stats['customers']['disconnected_found'] += 1
                self.sync_stats['disconnection_analysis']['total_with_real_dates'] += 1
                
                # Track risk levels
                risk_level = churn_assessment['risk_level']
                self.sync_stats['disconnection_analysis'][f'{risk_level}_risk'] += 1
            else:
                self.sync_stats['disconnection_analysis']['placeholder_dates'] += 1
            
        except Exception as e:
            logger.error(f"Error processing customer {customer_data.get('crm_customer_id')}: {e}")
            raise
    
    def _update_customer_disconnection_fields(self, customer, customer_data):
        """Update customer with available disconnection fields"""
        
        # Update basic fields
        customer.customer_name = customer_data.get('customer_name', customer.customer_name)
        if hasattr(customer, 'phone'):
            customer.phone = customer_data.get('customer_phone', customer.phone)
        
        if hasattr(customer, 'outstanding_balance'):
            customer.outstanding_balance = float(customer_data.get('customer_balance', 0) or 0)
        
        # Update disconnection-specific fields if they exist
        if hasattr(customer, 'days_since_disconnection'):
            customer.days_since_disconnection = customer_data.get('days_since_disconnection', 0)
    
    def _calculate_disconnection_churn_risk(self, customer_data):
        """Calculate churn risk based on disconnection data"""
        
        disconnection_status = customer_data.get('disconnection_status', 'ACTIVE')
        days_disconnected = customer_data.get('days_since_disconnection', 0)
        
        if disconnection_status == 'ACTIVE':
            return {
                'risk_level': 'low',
                'probability': 0.1,
                'reasoning': 'Active customer (placeholder disconnection date)'
            }
        
        # Apply business logic for disconnected customers
        if days_disconnected >= 90:
            return {
                'risk_level': 'high',
                'probability': min(0.8 + (days_disconnected - 90) / 365, 0.95),
                'reasoning': f'Disconnected for {days_disconnected} days (>90 days = high risk)'
            }
        elif days_disconnected >= 60:
            return {
                'risk_level': 'medium',
                'probability': 0.5 + (days_disconnected - 60) / 300,
                'reasoning': f'Disconnected for {days_disconnected} days (60-89 days = medium risk)'
            }
        elif days_disconnected >= 30:
            return {
                'risk_level': 'low',
                'probability': 0.25,
                'reasoning': f'Disconnected for {days_disconnected} days (30-59 days = low risk)'
            }
        else:
            return {
                'risk_level': 'low',
                'probability': 0.15,
                'reasoning': f'Recently disconnected ({days_disconnected} days)'
            }
    
    def _parse_disconnection_date(self, churned_date_str):
        """Parse disconnection date from string"""
        
        if not churned_date_str or churned_date_str in ['0001-01-01 00:00:00', '0001-01-01']:
            return None
        
        try:
            # Try parsing common formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(churned_date_str, fmt)
                except ValueError:
                    continue
            
            # If no format worked, try basic parsing
            if len(churned_date_str) >= 10:
                return datetime.strptime(churned_date_str[:10], '%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"Could not parse disconnection date '{churned_date_str}': {e}")
        
        return None
    
    def _get_postgresql_connection(self):
        """Get PostgreSQL connection"""
        
        if self.connection and not self.connection.closed:
            return self.connection
        
        try:
            pg_config = self.company.get_postgresql_config()
            
            self.connection = psycopg2.connect(
                host=pg_config['host'],
                port=int(pg_config['port']),
                dbname=pg_config['database'],
                user=pg_config['username'],
                password=pg_config['password']
            )
            self.connection.autocommit = True
            return self.connection
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    # Compatibility methods for existing CRM service interface
    def sync_data_selective(self, sync_options=None):
        """Main sync method - compatible with existing interface"""
        return self.sync_customers_with_disconnection_analysis()
    
    def get_connection_info(self):
        """Get connection info"""
        return {
            'postgresql_configured': self.company.has_postgresql_config(),
            'preferred_method': 'postgresql',
            'disconnection_based_predictions': True,
            'minimal_version': True,
            'conflict_free': True
        }


# Maintain compatibility with existing imports
CRMService = MinimalDisconnectionCRMService
EnhancedCRMService = MinimalDisconnectionCRMService
DisconnectionBasedCRMService = MinimalDisconnectionCRMService