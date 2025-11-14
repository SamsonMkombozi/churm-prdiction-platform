"""
Enhanced CRM Service with Integrated Payment-Based Churn Prediction
app/services/crm_service.py

This version integrates the payment-based churn prediction logic from n.py
and maps customers to all four tables: crm_customers, crm_tickets, nav_mpesa_transactions, spl_statistics
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.models.prediction import Prediction
from app.models.company import Company
from app.services.prediction_service import EnhancedChurnPredictionService
import traceback
import time
import logging
import json

logger = logging.getLogger(__name__)

class EnhancedCRMServiceWithPredictions:
    """Enhanced CRM Service with integrated payment-based churn prediction logic from n.py"""
    
    def __init__(self, company):
        self.company = company
        self.connection = None
        
        # Initialize prediction service
        self.prediction_service = EnhancedChurnPredictionService()
        
        logger.info(f"Initializing Enhanced CRM Service with Predictions for: {company.name}")
        
        # Customer lookup cache - the KEY to solving the problem
        self.customer_cache = {}  # {crm_customer_id: internal_customer_id}
        self.customer_name_cache = {}  # {crm_customer_id: customer_name}
        
        # Enhanced tracking for integrated predictions
        self.sync_stats = {
            'start_time': None,
            'customers': {'new': 0, 'updated': 0, 'cached': 0, 'errors': 0, 'with_predictions': 0},
            'payments': {'new': 0, 'updated': 0, 'skipped': 0, 'orphaned': 0},
            'tickets': {'new': 0, 'updated': 0, 'skipped': 0, 'orphaned': 0},
            'usage_stats': {'new': 0, 'updated': 0, 'skipped': 0, 'orphaned': 0},
            'predictions': {'generated': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0, 'errors': 0},
            'cache_performance': {'hits': 0, 'misses': 0, 'build_time': 0},
            'total_records': 0,
            'sync_duration': 0,
            'connection_method': 'postgresql_with_predictions'
        }
        
        # Track orphaned data for reporting
        self.orphaned_tickets = []
        self.orphaned_payments = []
        self.orphaned_usage = []
        
        # Enhanced customer data for predictions
        self.enhanced_customers = {}  # Store complete customer data for predictions
        
        # Debug mode for detailed logging
        self.debug_mode = True
    
    def get_connection_info(self):
        """Get connection info with prediction capabilities"""
        
        logger.info(f"=== ENHANCED CONNECTION INFO WITH PREDICTIONS ===")
        
        postgresql_configured = self.company.has_postgresql_config()
        api_configured = self.company.has_api_config()
        
        return {
            'postgresql_configured': postgresql_configured,
            'api_configured': api_configured,
            'preferred_method': 'postgresql' if postgresql_configured else 'api',
            'prediction_enabled': True,
            'payment_based_predictions': True,
            'integrated_churn_analysis': True,
            'tables_mapped': ['crm_customers', 'crm_tickets', 'nav_mpesa_transactions', 'spl_statistics']
        }
    
    def sync_data_selective(self, sync_options=None):
        """Enhanced selective sync with integrated predictions"""
        
        if sync_options is None:
            sync_options = {
                'sync_customers': True,
                'sync_payments': True,
                'sync_tickets': True,
                'sync_usage': True,
                'generate_predictions': True  # New option for predictions
            }
        
        # Default prediction generation to True if not specified
        if 'generate_predictions' not in sync_options:
            sync_options['generate_predictions'] = True
        
        self.sync_stats['start_time'] = time.time()
        
        logger.info(f"=== ENHANCED SYNC WITH PREDICTIONS STARTED ===")
        logger.info(f"Sync options: {sync_options}")
        
        try:
            # Clear any existing session issues
            self._safe_session_rollback()
            
            # Mark sync as started
            self.company.mark_sync_started()
            
            # Get PostgreSQL connection
            connection_info = self.get_connection_info()
            
            if connection_info['preferred_method'] == 'postgresql':
                return self._enhanced_postgresql_sync_with_predictions(sync_options)
            else:
                return {
                    'success': False,
                    'message': 'PostgreSQL required for enhanced sync with predictions',
                    'recommendation': 'Configure PostgreSQL connection in company settings'
                }
                
        except Exception as e:
            error_msg = f"Enhanced sync with predictions failed: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Safe rollback
            self._safe_session_rollback()
            self.company.mark_sync_failed(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'stats': self.sync_stats,
                'orphaned_data': {
                    'tickets': len(self.orphaned_tickets),
                    'payments': len(self.orphaned_payments),
                    'usage': len(self.orphaned_usage)
                }
            }
    
    def _enhanced_postgresql_sync_with_predictions(self, sync_options):
        """Enhanced PostgreSQL sync with integrated payment-based predictions"""
        
        logger.info("=== ENHANCED POSTGRESQL SYNC WITH PREDICTIONS ===")
        
        try:
            # Get connection
            conn = self._get_postgresql_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            logger.info("PostgreSQL connection established for enhanced sync")
            
            # CRITICAL: Build customer cache FIRST
            self._build_comprehensive_customer_cache()
            
            # STEP 1: Enhanced customer sync with payment history analysis
            if sync_options.get('sync_customers', True):
                logger.info("[1/5] Enhanced customer sync with payment analysis...")
                self._enhanced_sync_customers_with_payment_history(cursor)
            
            # STEP 2: Sync payments with enhanced tracking
            if sync_options.get('sync_payments', True):
                logger.info("[2/5] Enhanced payment sync...")
                self._enhanced_sync_payments(cursor)
            
            # STEP 3: Sync tickets with enhanced tracking
            if sync_options.get('sync_tickets', True):
                logger.info("[3/5] Enhanced ticket sync...")
                self._enhanced_sync_tickets(cursor)
            
            # STEP 4: Sync usage statistics
            if sync_options.get('sync_usage', True):
                logger.info("[4/5] Enhanced usage statistics sync...")
                self._enhanced_sync_usage_statistics(cursor)
            
            # STEP 5: Generate payment-based churn predictions
            if sync_options.get('generate_predictions', True):
                logger.info("[5/5] Generating payment-based churn predictions...")
                self._generate_payment_based_predictions()
            
            # Calculate final performance stats
            elapsed_time = time.time() - self.sync_stats['start_time']
            total_records = (
                self.sync_stats['customers']['new'] + self.sync_stats['customers']['updated'] +
                self.sync_stats['payments']['new'] + self.sync_stats['payments']['updated'] +
                self.sync_stats['tickets']['new'] + self.sync_stats['tickets']['updated'] +
                self.sync_stats['usage_stats']['new'] + self.sync_stats['usage_stats']['updated'] +
                self.sync_stats['predictions']['generated']
            )
            
            self.sync_stats.update({
                'sync_duration': round(elapsed_time, 2),
                'total_records': total_records,
                'records_per_second': round(total_records / elapsed_time, 2) if elapsed_time > 0 else 0
            })
            
            # Final commit
            self._safe_session_commit()
            self.company.mark_sync_completed()
            
            # Success report
            logger.info(f"=== ENHANCED SYNC WITH PREDICTIONS COMPLETED ===")
            logger.info(f"Total records: {total_records:,}")
            logger.info(f"Predictions generated: {self.sync_stats['predictions']['generated']:,}")
            logger.info(f"High risk customers: {self.sync_stats['predictions']['high_risk']:,}")
            logger.info(f"Duration: {elapsed_time:.1f}s")
            logger.info(f"Speed: {self.sync_stats['records_per_second']} records/sec")
            
            return {
                'success': True,
                'message': f'Enhanced sync with predictions completed! Processed {total_records:,} records and generated {self.sync_stats["predictions"]["generated"]:,} churn predictions',
                'stats': self.sync_stats,
                'performance': {
                    'sync_duration': self.sync_stats['sync_duration'],
                    'records_per_second': self.sync_stats['records_per_second'],
                    'customer_cache_size': len(self.customer_cache),
                    'predictions_generated': self.sync_stats['predictions']['generated'],
                    'high_risk_customers': self.sync_stats['predictions']['high_risk']
                },
                'prediction_summary': {
                    'total_predictions': self.sync_stats['predictions']['generated'],
                    'high_risk': self.sync_stats['predictions']['high_risk'],
                    'medium_risk': self.sync_stats['predictions']['medium_risk'],
                    'low_risk': self.sync_stats['predictions']['low_risk'],
                    'prediction_errors': self.sync_stats['predictions']['errors']
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced sync with predictions failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            self._safe_session_rollback()
            self.company.mark_sync_failed(str(e))
            
            raise Exception(f"Enhanced sync with predictions failed: {str(e)}")
        
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def _enhanced_sync_customers_with_payment_history(self, cursor):
        """Enhanced customer sync that includes payment history analysis from n.py logic"""
        
        try:
            # Get customers with enhanced data for predictions
            query = """
                SELECT 
                    c.id,
                    c.customer_name,
                    c.customer_phone,
                    c.customer_balance,
                    c.status,
                    c.connection_status,
                    c.date_installed,
                    c.created_at,
                    c.churned_date,
                    c.splynx_location,
                    -- Payment aggregations
                    COUNT(DISTINCT mp.id) as total_payments,
                    COUNT(DISTINCT CASE WHEN mp.posted_to_ledgers = 1 AND mp.is_refund = 0 THEN mp.id END) as successful_payments,
                    SUM(CASE WHEN mp.posted_to_ledgers = 1 AND mp.is_refund = 0 THEN mp.tx_amount ELSE 0 END) as total_paid_amount,
                    MAX(CASE WHEN mp.posted_to_ledgers = 1 AND mp.is_refund = 0 THEN mp.tx_time END) as last_payment_date,
                    -- Ticket aggregations
                    COUNT(DISTINCT t.id) as total_tickets,
                    COUNT(DISTINCT CASE WHEN t.status = 'open' THEN t.id END) as open_tickets,
                    -- Usage aggregations
                    COUNT(DISTINCT s.id) as usage_records,
                    AVG((COALESCE(s.in_bytes, 0) + COALESCE(s.out_bytes, 0)) / 1048576.0) as avg_mb_usage
                FROM crm_customers c
                LEFT JOIN nav_mpesa_transactions mp ON mp.account_no = c.id::text 
                    AND mp.tx_time >= CURRENT_DATE - INTERVAL '2 years'
                LEFT JOIN crm_tickets t ON t.customer_no = c.id::text 
                    AND t.created_at >= CURRENT_DATE - INTERVAL '2 years'
                LEFT JOIN spl_statistics s ON s.customer_id = c.id 
                    AND s.start_date >= CURRENT_DATE - INTERVAL '2 years'
                WHERE c.customer_name IS NOT NULL 
                AND c.customer_name != ''
                AND c.customer_name NOT ILIKE 'test%'
                AND c.customer_name != 'None'
                GROUP BY c.id, c.customer_name, c.customer_phone, c.customer_balance, 
                         c.status, c.connection_status, c.date_installed, c.created_at, 
                         c.churned_date, c.splynx_location
                ORDER BY c.id
            """
            
            cursor.execute(query)
            customers_data = cursor.fetchall()
            logger.info(f"Retrieved {len(customers_data):,} enhanced customers from PostgreSQL")
            
            # Process customers in batches
            batch_size = 50
            for i in range(0, len(customers_data), batch_size):
                batch = customers_data[i:i + batch_size]
                
                for customer_row in batch:
                    try:
                        customer_data = dict(customer_row)
                        crm_id = str(customer_data['id'])
                        
                        # Calculate enhanced metrics using n.py logic
                        enhanced_data = self._calculate_enhanced_customer_metrics(customer_data)
                        
                        # Check if customer exists
                        customer = Customer.query.filter_by(
                            company_id=self.company.id,
                            crm_customer_id=crm_id
                        ).first()
                        
                        if customer:
                            # Update existing customer with enhanced data
                            self._update_customer_with_enhanced_data(customer, enhanced_data)
                            self.sync_stats['customers']['updated'] += 1
                        else:
                            # Create new customer with enhanced data
                            customer = self._create_customer_with_enhanced_data(enhanced_data)
                            self.sync_stats['customers']['new'] += 1
                        
                        # Store enhanced customer data for predictions
                        self.enhanced_customers[crm_id] = enhanced_data
                        
                        # Update cache
                        self.customer_cache[crm_id] = customer.id
                        self.customer_name_cache[crm_id] = enhanced_data['customer_name']
                        self.sync_stats['customers']['cached'] += 1
                        
                    except Exception as e:
                        logger.warning(f"Enhanced customer {customer_row.get('id')} error: {e}")
                        self.sync_stats['customers']['errors'] += 1
                        continue
                
                # Commit batch
                try:
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Enhanced customer batch commit failed: {e}")
                    db.session.rollback()
                
                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"   Enhanced processed {i + len(batch):,} customers...")
            
            logger.info(f"Enhanced customer sync completed: {self.sync_stats['customers']}")
            
        except Exception as e:
            logger.error(f"Enhanced customer sync failed: {e}")
            raise
    
    def _calculate_enhanced_customer_metrics(self, customer_data):
        """Calculate enhanced customer metrics using n.py payment-based logic"""
        
        try:
            current_date = datetime.now()
            
            # Basic customer info
            crm_id = str(customer_data['id'])
            customer_name = customer_data.get('customer_name', 'Unknown Customer')
            phone = customer_data.get('customer_phone', '')
            balance = float(customer_data.get('customer_balance', 0) or 0)
            
            # Payment metrics
            total_payments = int(customer_data.get('total_payments', 0))
            successful_payments = int(customer_data.get('successful_payments', 0))
            failed_payments = total_payments - successful_payments
            total_paid_amount = float(customer_data.get('total_paid_amount', 0) or 0)
            last_payment_date = customer_data.get('last_payment_date')
            
            # Calculate payment consistency and timing
            payment_success_rate = successful_payments / max(total_payments, 1)
            avg_payment_amount = total_paid_amount / max(successful_payments, 1)
            
            # Calculate days since last payment (key metric from n.py)
            if last_payment_date:
                days_since_last_payment = (current_date - last_payment_date).days
            else:
                days_since_last_payment = 999  # No payments
            
            # Calculate tenure
            date_installed = customer_data.get('date_installed')
            tenure_months, signup_date = self._safe_date_calculation(date_installed, current_date)
            
            # Support metrics
            total_tickets = int(customer_data.get('total_tickets', 0))
            open_tickets = int(customer_data.get('open_tickets', 0))
            complaints_per_month = total_tickets / max(tenure_months, 1)
            
            # Usage metrics
            usage_records = int(customer_data.get('usage_records', 0))
            avg_mb_usage = float(customer_data.get('avg_mb_usage', 0) or 0)
            
            # Apply n.py churn risk assessment logic
            churn_assessment = self._assess_churn_risk_from_payments_npy_logic(
                days_since_last_payment, total_payments, payment_success_rate, current_date
            )
            
            # Create enhanced customer data structure
            enhanced_data = {
                # Basic info
                'customer_id': crm_id,
                'id': crm_id,
                'crm_customer_id': crm_id,
                'customer_name': customer_name,
                'phone': phone,
                'email': '',
                'address': customer_data.get('splynx_location', ''),
                'signup_date': signup_date,
                'tenure_months': tenure_months,
                'outstanding_balance': abs(balance),
                
                # Payment history (n.py logic)
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'total_paid_amount': total_paid_amount,
                'avg_payment_amount': avg_payment_amount,
                'payment_consistency_score': payment_success_rate,
                'last_payment_date': last_payment_date.strftime('%Y-%m-%d') if last_payment_date else None,
                'days_since_last_payment': days_since_last_payment,
                
                # Support metrics
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'complaint_tickets': total_tickets,
                'number_of_complaints_per_month': complaints_per_month,
                
                # Usage metrics
                'usage_records': usage_records,
                'avg_data_usage': avg_mb_usage,
                'avg_download_usage': avg_mb_usage * 0.7,
                'avg_upload_usage': avg_mb_usage * 0.3,
                'active_days_last_6_months': min(usage_records, 180),
                
                # Service status
                'status': 'active' if balance >= -1000 and churn_assessment['risk_level'] != 'high' else 'at_risk',
                'service_plan': 'Standard',
                'monthly_charges': 50000.0,  # Default
                'total_charges': max(abs(balance) + total_paid_amount, 600000),
                
                # Churn prediction fields (n.py logic)
                'churn_risk_assessment': churn_assessment,
                'predicted_churn_risk': churn_assessment['risk_level'],
                'churn_probability': churn_assessment['probability'],
                'risk_reasoning': churn_assessment['reasoning'],
                'days_since_disconnection': 0 if churn_assessment['risk_level'] != 'high' else days_since_last_payment,
                
                # ML model compatibility fields
                'months_stayed': tenure_months,
                'number_of_payments': successful_payments,
                'missed_payments': failed_payments,
                'customer_number': crm_id,
                
                # Business categorization
                'payment_behavior': self._categorize_payment_behavior(days_since_last_payment, total_payments),
                'usage_category': self._categorize_usage(avg_mb_usage)
            }
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error calculating enhanced metrics for customer {customer_data.get('id')}: {e}")
            # Return basic fallback data
            return {
                'customer_id': str(customer_data.get('id', 'unknown')),
                'customer_name': customer_data.get('customer_name', 'Unknown'),
                'churn_probability': 0.5,
                'predicted_churn_risk': 'medium',
                'risk_reasoning': ['Unable to calculate enhanced metrics']
            }
    
    def _assess_churn_risk_from_payments_npy_logic(self, days_since_last, total_payments, success_rate, current_date):
        """Apply the exact n.py churn risk assessment logic"""
        
        # Initialize risk assessment
        risk_assessment = {
            'risk_level': 'low',
            'probability': 0.1,
            'reasoning': [],
            'estimated_disconnection_date': None
        }
        
        # HIGH RISK: No payments in last 90 days (3 months) - n.py logic
        if days_since_last >= 90:
            risk_assessment['risk_level'] = 'high'
            risk_assessment['probability'] = min(0.7 + (days_since_last - 90) / 1000, 0.95)
            risk_assessment['reasoning'].append(f"No payments for {days_since_last} days (>90 days)")
            
            # Estimate disconnection date
            if days_since_last >= 120:
                estimated_disc_date = current_date - timedelta(days=days_since_last-30)
                risk_assessment['estimated_disconnection_date'] = estimated_disc_date.strftime('%Y-%m-%d')
        
        # MEDIUM RISK: No payments in last 60 days (2 months) OR payment issues - n.py logic
        elif days_since_last >= 60:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['probability'] = 0.4 + (days_since_last - 60) / 300
            risk_assessment['reasoning'].append(f"No payments for {days_since_last} days (60-90 days)")
            
        # MEDIUM RISK: Payment inconsistency issues - n.py logic
        elif total_payments > 0 and success_rate < 0.7:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['probability'] = 0.35 + (0.7 - success_rate)
            risk_assessment['reasoning'].append(f"Poor payment success rate ({success_rate:.1%})")
            
        # MEDIUM RISK: Very few payments relative to tenure - n.py logic
        elif total_payments > 0 and total_payments < 3:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['probability'] = 0.3
            risk_assessment['reasoning'].append(f"Very few payments ({total_payments} total)")
        
        # LOW RISK: Recent payments and good payment behavior - n.py logic
        else:
            risk_assessment['risk_level'] = 'low'
            
            if days_since_last <= 30:
                risk_assessment['probability'] = 0.05
                risk_assessment['reasoning'].append(f"Recent payment ({days_since_last} days ago)")
            elif days_since_last <= 60:
                risk_assessment['probability'] = 0.15
                risk_assessment['reasoning'].append(f"Somewhat recent payment ({days_since_last} days ago)")
            
            if success_rate > 0.8:
                risk_assessment['reasoning'].append(f"Good payment reliability ({success_rate:.1%})")
            
            if total_payments >= 5:
                risk_assessment['reasoning'].append(f"Regular payment history ({total_payments} payments)")
        
        # Special case: No payments at all - n.py logic
        if total_payments == 0:
            risk_assessment['risk_level'] = 'high'
            risk_assessment['probability'] = 0.8
            risk_assessment['reasoning'] = ["No payment history - potential non-paying customer"]
        
        return risk_assessment
    
    def _generate_payment_based_predictions(self):
        """Generate payment-based churn predictions for all enhanced customers"""
        
        try:
            logger.info(f"Generating payment-based predictions for {len(self.enhanced_customers)} customers...")
            
            predictions_generated = 0
            prediction_errors = 0
            
            for crm_id, enhanced_data in self.enhanced_customers.items():
                try:
                    # Get internal customer ID
                    internal_customer_id = self.customer_cache.get(crm_id)
                    if not internal_customer_id:
                        continue
                    
                    # Generate prediction using enhanced service
                    prediction_result = self.prediction_service.predict_customer_churn(enhanced_data)
                    
                    if prediction_result:
                        # Create prediction record
                        prediction = Prediction.create_prediction(
                            company_id=self.company.id,
                            customer_id=crm_id,
                            prediction_result=prediction_result
                        )
                        
                        if prediction:
                            predictions_generated += 1
                            
                            # Update risk counters
                            risk_level = prediction_result.get('churn_risk', 'medium')
                            self.sync_stats['predictions'][f'{risk_level}_risk'] += 1
                            
                            # Update customer record with prediction
                            customer = Customer.query.filter_by(
                                company_id=self.company.id,
                                crm_customer_id=crm_id
                            ).first()
                            
                            if customer:
                                customer.churn_risk = risk_level
                                customer.churn_probability = prediction_result.get('churn_probability', 0.5)
                                customer.last_prediction_date = datetime.utcnow()
                        
                except Exception as e:
                    logger.warning(f"Prediction error for customer {crm_id}: {e}")
                    prediction_errors += 1
                    continue
            
            # Update stats
            self.sync_stats['predictions']['generated'] = predictions_generated
            self.sync_stats['predictions']['errors'] = prediction_errors
            
            # Final commit for predictions
            try:
                db.session.commit()
                logger.info(f"✅ Generated {predictions_generated} payment-based predictions")
                logger.info(f"   High risk: {self.sync_stats['predictions']['high_risk']}")
                logger.info(f"   Medium risk: {self.sync_stats['predictions']['medium_risk']}")
                logger.info(f"   Low risk: {self.sync_stats['predictions']['low_risk']}")
                logger.info(f"   Errors: {prediction_errors}")
            except Exception as e:
                logger.error(f"Failed to commit predictions: {e}")
                db.session.rollback()
            
        except Exception as e:
            logger.error(f"Payment-based prediction generation failed: {e}")
            raise
    
    # Helper methods from original service (preserved)
    
    def _safe_date_calculation(self, created_at, current_date):
        """Safely calculate tenure from created_at field with multiple format support"""
        try:
            if created_at is None:
                return 12.0, '2023-01-01'
            
            # Handle different data types
            if isinstance(created_at, datetime):
                created_dt = created_at
            elif isinstance(created_at, str):
                # Try different date formats
                date_formats = [
                    '%d/%m/%Y %H:%M:%S',  # 18/06/2024 13:20:23
                    '%d/%m/%Y',           # 18/06/2024
                    '%Y-%m-%d %H:%M:%S',  # 2024-06-18 13:20:23
                    '%Y-%m-%d',           # 2024-06-18
                    '%m/%d/%Y %H:%M:%S',  # 06/18/2024 13:20:23
                    '%m/%d/%Y'            # 06/18/2024
                ]
                
                created_dt = None
                for date_format in date_formats:
                    try:
                        created_dt = datetime.strptime(created_at, date_format)
                        break
                    except ValueError:
                        continue
                
                if created_dt is None:
                    logger.warning(f"⚠️ Could not parse date: {created_at}")
                    return 12.0, '2023-01-01'
            else:
                logger.warning(f"⚠️ Unknown date type: {type(created_at)}")
                return 12.0, '2023-01-01'
            
            # Calculate tenure
            tenure_months = (current_date - created_dt).days / 30.44
            signup_date = created_dt.strftime('%Y-%m-%d')
            
            return max(tenure_months, 0.1), signup_date
            
        except Exception as e:
            logger.warning(f"⚠️ Date calculation error: {e}")
            return 12.0, '2023-01-01'
    
    def _categorize_payment_behavior(self, days_since_payment, total_payments):
        """Categorize payment behavior for business analysis"""
        if days_since_payment >= 90:
            return 'poor_payer'
        elif days_since_payment >= 60:
            return 'moderate_payer'
        elif total_payments == 0:
            return 'no_payments'
        else:
            return 'good_payer'
    
    def _categorize_usage(self, avg_usage):
        """Categorize usage for business analysis"""
        if avg_usage < 100:
            return 'low_usage'
        elif avg_usage < 1000:
            return 'medium_usage'
        else:
            return 'high_usage'
    
    def _update_customer_with_enhanced_data(self, customer, enhanced_data):
        """Update existing customer with enhanced data"""
        customer.customer_name = enhanced_data.get('customer_name', customer.customer_name)
        customer.phone = enhanced_data.get('phone', customer.phone)
        customer.outstanding_balance = enhanced_data.get('outstanding_balance', customer.outstanding_balance)
        customer.address = enhanced_data.get('address', customer.address)
        customer.total_payments = enhanced_data.get('total_payments', customer.total_payments or 0)
        customer.total_tickets = enhanced_data.get('total_tickets', customer.total_tickets or 0)
        customer.tenure_months = enhanced_data.get('tenure_months', customer.tenure_months)
        customer.updated_at = datetime.utcnow()
        customer.synced_at = datetime.utcnow()
    
    def _create_customer_with_enhanced_data(self, enhanced_data):
        """Create new customer with enhanced data"""
        customer = Customer(
            company_id=self.company.id,
            crm_customer_id=enhanced_data['crm_customer_id'],
            customer_name=enhanced_data['customer_name'],
            phone=enhanced_data.get('phone'),
            email=enhanced_data.get('email'),
            address=enhanced_data.get('address'),
            outstanding_balance=enhanced_data.get('outstanding_balance', 0),
            status=enhanced_data.get('status', 'active'),
            signup_date=self._parse_date(enhanced_data.get('signup_date')),
            tenure_months=enhanced_data.get('tenure_months', 0),
            total_payments=enhanced_data.get('total_payments', 0),
            total_tickets=enhanced_data.get('total_tickets', 0),
            created_at=datetime.utcnow(),
            synced_at=datetime.utcnow()
        )
        db.session.add(customer)
        db.session.flush()  # Get the ID immediately
        return customer
    
    # Preserve all other methods from UltraFixedCRMService
    def _build_comprehensive_customer_cache(self):
        """Build comprehensive customer cache from existing database"""
        cache_start = time.time()
        logger.info("Building comprehensive customer cache...")
        
        try:
            customers = Customer.query.filter_by(company_id=self.company.id).all()
            
            for customer in customers:
                if customer.crm_customer_id:
                    self.customer_cache[customer.crm_customer_id] = customer.id
                    self.customer_name_cache[customer.crm_customer_id] = customer.customer_name
                
                self.customer_cache[str(customer.id)] = customer.id
            
            cache_time = time.time() - cache_start
            self.sync_stats['cache_performance']['build_time'] = cache_time
            
            logger.info(f"Customer cache built: {len(self.customer_cache)} entries in {cache_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to build customer cache: {e}")
            raise
    
    def _enhanced_sync_payments(self, cursor):
        """Enhanced payment sync (placeholder for now)"""
        logger.info("Enhanced payment sync - using existing payment data from customer analysis")
        # Payment data already included in enhanced customer sync
    
    def _enhanced_sync_tickets(self, cursor):
        """Enhanced ticket sync (placeholder for now)"""
        logger.info("Enhanced ticket sync - using existing ticket data from customer analysis") 
        # Ticket data already included in enhanced customer sync
    
    def _enhanced_sync_usage_statistics(self, cursor):
        """Enhanced usage statistics sync (placeholder for now)"""
        logger.info("Enhanced usage sync - using existing usage data from customer analysis")
        # Usage data already included in enhanced customer sync
    
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
            
            logger.info("PostgreSQL connection established for enhanced sync")
            return self.connection
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def _safe_session_commit(self):
        """Safely commit database session"""
        try:
            db.session.commit()
        except Exception as e:
            logger.warning(f"Session commit failed: {e}")
            db.session.rollback()
            raise
    
    def _safe_session_rollback(self):
        """Safely rollback database session"""
        try:
            db.session.rollback()
        except Exception as e:
            logger.warning(f"Session rollback warning: {e}")
    
    @staticmethod
    def _parse_date(date_string):
        """Parse date string to datetime"""
        if not date_string:
            return None
        
        date_str = str(date_string).strip()
        
        # Skip invalid dates
        if date_str in ['0000-00-00', '0000-00-00 00:00:00', 'None', '']:
            return None
        
        try:
            # ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # MySQL datetime format
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                try:
                    # Date only
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, AttributeError):
                    return None
    
    def test_postgresql_connection(self):
        """Test PostgreSQL connection with enhanced capabilities"""
        logger.info(f"Testing Enhanced PostgreSQL connection with prediction capabilities")
        
        try:
            pg_config = self.company.get_postgresql_config()
            
            if not all([pg_config['host'], pg_config['database'], pg_config['username'], pg_config['password']]):
                return {
                    'success': False,
                    'message': 'PostgreSQL configuration incomplete'
                }
            
            # Test connection and analyze all four tables
            pg_config_fixed = {
                'host': pg_config['host'],
                'port': pg_config['port'], 
                'dbname': pg_config['database'],
                'user': pg_config['username'],
                'password': pg_config['password']
            }
            
            with psycopg2.connect(**pg_config_fixed) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    
                    # Check all four tables
                    table_info = {}
                    tables = ['crm_customers', 'crm_tickets', 'nav_mpesa_transactions', 'spl_statistics']
                    
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                            count = cursor.fetchone()['count']
                            table_info[table] = {'count': count, 'available': True}
                        except Exception as e:
                            table_info[table] = {'count': 0, 'available': False, 'error': str(e)}
                    
                    return {
                        'success': True,
                        'message': 'Enhanced PostgreSQL connection successful with prediction capabilities!',
                        'database_version': version,
                        'tables': table_info,
                        'enhanced_features': [
                            'Payment-based churn prediction integration',
                            'Multi-table customer mapping',
                            'Real-time risk assessment',
                            'Comprehensive customer analytics',
                            'n.py logic integration'
                        ],
                        'prediction_ready': all(info['available'] for info in table_info.values())
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'Enhanced PostgreSQL connection failed: {str(e)}'
            }


# Maintain backward compatibility
UltraFixedCRMService = EnhancedCRMServiceWithPredictions
CRMService = EnhancedCRMServiceWithPredictions
EnhancedCRMService = EnhancedCRMServiceWithPredictions