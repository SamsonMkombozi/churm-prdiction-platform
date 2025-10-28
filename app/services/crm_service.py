"""
FIXED CRM Integration Service - Enhanced Error Handling
app/services/crm_service.py

✅ Fixes for your Habari CRM API:
- Better error handling for empty responses
- Enhanced debugging information
- Proper JSON validation
- Fallback for different response formats
"""
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging
from app.extensions import db
from app.models.company import Company
from app.repositories.customer_repository import CustomerRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.ticket_repository import TicketRepository

logger = logging.getLogger(__name__)


class CRMService:
    """Enhanced CRM service with better error handling"""
    
    # ✅ Use correct table names for your CRM
    CUSTOMER_TABLE = 'crm_customers'
    TICKET_TABLE = 'tickets_full'
    PAYMENT_TABLE = 'nav_mpesa_transaction'
    USAGE_TABLE = 'spl_statistics'
    
    def __init__(self, company: Company):
        """Initialize CRM service for a company"""
        self.company = company
        self.api_url = company.crm_api_url
        self.api_key = None  # Your CRM doesn't use API key
        self.timeout = 30
        
        # Initialize repositories
        self.customer_repo = CustomerRepository(company)
        self.payment_repo = PaymentRepository(company)
        self.ticket_repo = TicketRepository(company)
        
        # Customer ID mapping cache
        self.customer_mapping = {}
    
    def test_connection(self) -> Dict:
        """
        ✅ ENHANCED: Test CRM API connection with detailed debugging
        """
        try:
            # Test URL formation
            test_url = f"{self.api_url}?table={self.CUSTOMER_TABLE}&limit=1"
            logger.info(f"🔗 Testing connection to: {test_url}")
            
            # Make test request with detailed logging
            response = requests.get(test_url, timeout=10)
            
            # Log response details
            logger.info(f"📊 Response Status: {response.status_code}")
            logger.info(f"📊 Response Headers: {dict(response.headers)}")
            logger.info(f"📊 Response Length: {len(response.content)} bytes")
            
            # Check if response is empty
            if len(response.content) == 0:
                return {
                    'success': False,
                    'message': 'API returned empty response. Check if the API URL is correct and the server is running.',
                    'debug_info': {
                        'url': test_url,
                        'status_code': response.status_code,
                        'content_length': 0
                    }
                }
            
            # Log first 200 chars of response for debugging
            response_preview = response.text[:200]
            logger.info(f"📊 Response Preview: {response_preview}")
            
            # Check if response looks like HTML (common error)
            if response.text.strip().startswith('<!DOCTYPE') or response.text.strip().startswith('<html'):
                return {
                    'success': False,
                    'message': 'API returned HTML instead of JSON. This usually means the endpoint is incorrect or the server has an error.',
                    'debug_info': {
                        'url': test_url,
                        'response_preview': response_preview
                    }
                }
            
            # Try to parse JSON
            try:
                data = response.json()
                logger.info(f"✅ Successfully parsed JSON response")
                
                # Check if it's a successful response
                if isinstance(data, dict):
                    if 'error' in data:
                        return {
                            'success': False,
                            'message': f"API returned error: {data['error']}",
                            'debug_info': data
                        }
                    
                    # Extract data
                    records = self._extract_records_from_response(data)
                    
                    return {
                        'success': True,
                        'message': f'Connection successful - Found {len(records)} records',
                        'debug_info': {
                            'url': test_url,
                            'record_count': len(records),
                            'response_keys': list(data.keys()) if isinstance(data, dict) else 'list'
                        }
                    }
                
                elif isinstance(data, list):
                    return {
                        'success': True,
                        'message': f'Connection successful - Found {len(data)} records',
                        'debug_info': {
                            'url': test_url,
                            'record_count': len(data)
                        }
                    }
                
                else:
                    return {
                        'success': False,
                        'message': f'Unexpected response format: {type(data)}',
                        'debug_info': {
                            'response_type': str(type(data)),
                            'response_preview': str(data)[:100]
                        }
                    }
                    
            except ValueError as json_error:
                return {
                    'success': False,
                    'message': f'Invalid JSON response: {str(json_error)}',
                    'debug_info': {
                        'url': test_url,
                        'json_error': str(json_error),
                        'response_preview': response_preview,
                        'status_code': response.status_code
                    }
                }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Connection timeout - API server is not responding',
                'debug_info': {'error_type': 'timeout'}
            }
        
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to API server - check if the URL is correct and server is running',
                'debug_info': {'error_type': 'connection_error'}
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'debug_info': {'error_type': type(e).__name__, 'error_message': str(e)}
            }
    
    def _extract_records_from_response(self, data) -> List[Dict]:
        """
        ✅ ENHANCED: Extract records from API response with multiple format support
        """
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            # Try different common keys
            for key in ['data', 'records', 'results', 'items']:
                if key in data:
                    records = data[key]
                    return records if isinstance(records, list) else [records]
            
            # If no standard key found, return the dict as a single record
            return [data]
        
        return []
    
    def _fetch_data(self, table_name: str) -> List[Dict]:
        """
        ✅ ENHANCED: Fetch data with comprehensive error handling
        """
        try:
            url = f"{self.api_url}?table={table_name}"
            logger.info(f"🔄 Fetching from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            
            # Check HTTP status
            if response.status_code != 200:
                logger.error(f"❌ HTTP Error {response.status_code} for {table_name}")
                response.raise_for_status()
            
            # Check for empty response
            if len(response.content) == 0:
                logger.warning(f"⚠️ Empty response from {table_name}")
                return []
            
            # Log response details
            logger.debug(f"📊 Response length: {len(response.content)} bytes")
            
            # Check if response looks like HTML
            response_text = response.text.strip()
            if response_text.startswith('<!DOCTYPE') or response_text.startswith('<html'):
                logger.error(f"❌ Received HTML instead of JSON from {table_name}")
                logger.error(f"Response preview: {response_text[:200]}")
                raise Exception(f"API returned HTML instead of JSON for {table_name}")
            
            # Parse JSON
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"❌ JSON parsing failed for {table_name}: {str(e)}")
                logger.error(f"Response preview: {response_text[:200]}")
                raise Exception(f"Invalid JSON response from {table_name}: {str(e)}")
            
            # Extract records
            records = self._extract_records_from_response(data)
            
            logger.info(f"✅ Fetched {len(records)} records from {table_name}")
            return records
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout fetching {table_name}")
            raise Exception(f"Timeout fetching {table_name}")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Connection error fetching {table_name}")
            raise Exception(f"Cannot connect to CRM for {table_name}")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"🌐 HTTP error fetching {table_name}: {e}")
            raise Exception(f"HTTP error {response.status_code} fetching {table_name}")
        
        except Exception as e:
            logger.error(f"💥 Unexpected error fetching {table_name}: {e}")
            raise
    
    def sync_all_data(self) -> Dict:
        """
        ✅ ENHANCED: Sync all data with better error handling
        """
        logger.info(f"🚀 Starting CRM sync for company: {self.company.name}")
        
        # Update sync status
        self.company.sync_status = 'in_progress'
        self.company.sync_error = None
        db.session.commit()
        
        results = {
            'success': False,
            'customers': {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []},
            'usage': {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []},
            'payments': {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []},
            'tickets': {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []},
            'errors': [],
            'debug_info': {}
        }
        
        try:
            # Test connection first
            connection_test = self.test_connection()
            if not connection_test['success']:
                raise Exception(f"Connection test failed: {connection_test['message']}")
            
            results['debug_info']['connection_test'] = connection_test
            
            # Step 1: Sync customers first
            logger.info("👥 Syncing customers...")
            try:
                customer_results = self._sync_customers()
                results['customers'] = customer_results
            except Exception as e:
                error_msg = f"Customer sync failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results['customers']['errors'].append(error_msg)
            
            # Step 2: Build customer mapping
            logger.info("🗺️ Building customer ID mapping...")
            try:
                self._build_customer_mapping()
            except Exception as e:
                logger.warning(f"⚠️ Customer mapping failed: {str(e)}")
                results['errors'].append(f"Customer mapping failed: {str(e)}")
            
            # Step 3: Sync usage statistics
            logger.info("📊 Syncing usage statistics...")
            try:
                from app.repositories.usage_repository import UsageRepository
                self.usage_repo = UsageRepository(self.company)
                usage_results = self._sync_usage()
                results['usage'] = usage_results
            except Exception as e:
                error_msg = f"Usage sync failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results['usage']['errors'].append(error_msg)
            
            # Step 4: Sync payments
            logger.info("💰 Syncing payments...")
            try:
                payment_results = self._sync_payments()
                results['payments'] = payment_results
            except Exception as e:
                error_msg = f"Payment sync failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results['payments']['errors'].append(error_msg)
            
            # Step 5: Sync tickets
            logger.info("🎫 Syncing tickets...")
            try:
                ticket_results = self._sync_tickets()
                results['tickets'] = ticket_results
            except Exception as e:
                error_msg = f"Ticket sync failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results['tickets']['errors'].append(error_msg)
            
            # Determine if sync was successful
            total_new = (results['customers']['new'] + results['usage']['new'] + 
                        results['payments']['new'] + results['tickets']['new'])
            
            if total_new > 0 or len(results['errors']) == 0:
                results['success'] = True
                self.company.sync_status = 'completed'
                self.company.last_sync_at = datetime.utcnow()
                self.company.total_syncs = (self.company.total_syncs or 0) + 1
                logger.info(f"✅ Sync completed successfully: {total_new} new records")
            else:
                results['success'] = False
                self.company.sync_status = 'failed'
                self.company.sync_error = '; '.join(results['errors'][:3])  # Store first 3 errors
                logger.error(f"❌ Sync failed with {len(results['errors'])} errors")
            
        except Exception as e:
            logger.error(f"💥 Sync failed: {str(e)}", exc_info=True)
            results['success'] = False
            results['errors'].append(str(e))
            self.company.sync_status = 'failed'
            self.company.sync_error = str(e)
        
        finally:
            db.session.commit()
        
        return results
    
    def _sync_customers(self) -> Dict:
        """Sync customer data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            customers_data = self._fetch_data(self.CUSTOMER_TABLE)
            
            if not customers_data:
                logger.warning("⚠️ No customer data received from CRM")
                return result
            
            logger.info(f"📝 Processing {len(customers_data)} customers...")
            
            for customer_data in customers_data:
                try:
                    # Normalize customer data
                    normalized_data = self._normalize_customer_data(customer_data)
                    
                    # Create or update customer
                    was_created = self.customer_repo.create_or_update(normalized_data)
                    
                    if was_created:
                        result['new'] += 1
                    else:
                        result['updated'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync customer {customer_data.get('id')}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    result['skipped'] += 1
                    result['errors'].append(error_msg)
                    continue
            
            # Commit after all customers
            db.session.commit()
            logger.info(f"✅ Synced {result['new']} new, {result['updated']} updated customers")
            
        except Exception as e:
            logger.error(f"❌ Customer sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Customer sync failed: {str(e)}")
            raise
        
        return result
    
    def _sync_payments(self) -> Dict:
        """Sync payment data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            payments_data = self._fetch_data(self.PAYMENT_TABLE)
            
            if not payments_data:
                logger.warning("⚠️ No payment data received from CRM")
                return result
            
            logger.info(f"💳 Processing {len(payments_data)} payments...")
            
            for payment_data in payments_data:
                try:
                    # Normalize payment data
                    normalized_data = self._normalize_payment_data(payment_data)
                    
                    # Create or update payment
                    was_created = self.payment_repo.create_or_update(normalized_data)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:  # None = skipped
                        result['skipped'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync payment {payment_data.get('id')}: {str(e)}"
                    logger.debug(f"⚠️ {error_msg}")  # Use debug level for payment errors
                    result['skipped'] += 1
                    continue
            
            # Commit after all payments
            db.session.commit()
            logger.info(f"✅ Synced {result['new']} new, {result['updated']} updated payments, {result['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"❌ Payment sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Payment sync failed: {str(e)}")
            raise
        
        return result
    
    def _sync_tickets(self) -> Dict:
        """Sync ticket data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            tickets_data = self._fetch_data(self.TICKET_TABLE)
            
            if not tickets_data:
                logger.warning("⚠️ No ticket data received from CRM")
                return result
            
            logger.info(f"🎫 Processing {len(tickets_data)} tickets...")
            
            for ticket_data in tickets_data:
                try:
                    # Normalize ticket data
                    normalized_data = self._normalize_ticket_data(ticket_data)
                    
                    # Create or update ticket
                    was_created = self.ticket_repo.create_or_update(normalized_data)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:  # None = skipped
                        result['skipped'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync ticket {ticket_data.get('ticket_id')}: {str(e)}"
                    logger.debug(f"⚠️ {error_msg}")  # Use debug level for ticket errors
                    result['skipped'] += 1
                    continue
            
            # Commit after all tickets
            db.session.commit()
            logger.info(f"✅ Synced {result['new']} new, {result['updated']} updated tickets, {result['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"❌ Ticket sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Ticket sync failed: {str(e)}")
            raise
        
        return result
    
    def _sync_usage(self) -> Dict:
        """Sync usage statistics from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            usage_data = self._fetch_data(self.USAGE_TABLE)
            
            if not usage_data:
                logger.warning("⚠️ No usage data received from CRM")
                return result
            
            logger.info(f"📊 Processing {len(usage_data)} usage records...")
            
            for usage_record in usage_data:
                try:
                    # Create or update usage record
                    was_created = self.usage_repo.create_or_update(usage_record)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:  # None = skipped
                        result['skipped'] += 1
                        
                except Exception as e:
                    logger.debug(f"Failed to sync usage {usage_record.get('id')}: {str(e)}")
                    result['skipped'] += 1
                    continue
            
            # Commit after all usage records
            db.session.commit()
            logger.info(f"✅ Synced {result['new']} new, {result['updated']} updated usage records")
            
        except Exception as e:
            logger.error(f"❌ Usage sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Usage sync failed: {str(e)}")
            raise
        
        return result
    
    def _build_customer_mapping(self):
        """Build mapping between login IDs and customer IDs"""
        try:
            logger.info("🗺️ Fetching usage data to build customer mapping...")
            usage_data = self._fetch_data(self.USAGE_TABLE)
            
            if not usage_data:
                logger.warning("⚠️ No usage data available for mapping")
                return
            
            # Build mapping: login -> crm_customer_id
            for record in usage_data:
                login = record.get('login')
                customer_id = record.get('customer_id')
                
                if login and customer_id:
                    self.customer_mapping[login] = str(customer_id)
            
            logger.info(f"✅ Built mapping for {len(self.customer_mapping)} login IDs")
            
        except Exception as e:
            logger.warning(f"⚠️ Customer mapping failed: {str(e)}")
    
    # Normalization methods (same as before)
    def _normalize_customer_data(self, data: Dict) -> Dict:
        """Normalize customer data from CRM format to standard format"""
        return {
            'id': data.get('id'),
            'name': data.get('customer_name'),
            'email': data.get('customer_email'),
            'phone': data.get('customer_phone'),
            'address': data.get('address'),
            'status': data.get('connection_status') or data.get('status'),
            'account_type': data.get('classification'),
            'monthly_charges': self._parse_float(data.get('customer_balance')),
            'total_charges': 0.0,
            'outstanding_balance': self._parse_float(data.get('customer_balance')),
            'service_type': data.get('category'),
            'connection_type': data.get('routers'),
            'bandwidth_plan': data.get('package'),
            'signup_date': data.get('date_installed') or data.get('created_at'),
            'disconnection_date': data.get('disconnection_date'),
            'churned_date': data.get('churned_date'),
            'region': data.get('splynx_location'),
            'sector': data.get('sector'),
            'billing_frequency': data.get('billing_frequency')
        }
    
    def _normalize_payment_data(self, data: Dict) -> Dict:
        """Normalize payment data from CRM format to standard format"""
        account_no = data.get('account_no')
        customer_ref = account_no
        
        # Extract numeric part from CUST-XXX format
        if account_no and 'CUST-' in str(account_no):
            try:
                num = str(account_no).split('CUST-')[1]
                customer_ref = num.zfill(5)
            except:
                customer_ref = account_no
        
        return {
            'id': data.get('id'),
            'account_no': customer_ref,
            'payer': data.get('payer'),
            'transaction_id': data.get('mpesa_ref'),
            'transaction_amount': self._parse_float(data.get('tx_amount')),
            'transaction_time': data.get('tx_time'),
            'phone_number': data.get('phone_no'),
            'transaction_type': data.get('transaction_type') or 'payment',
            'status': 'completed' if data.get('posted_to_ledgers') == '1' else 'pending',
            'created_at': data.get('created_at')
        }
    
    def _normalize_ticket_data(self, data: Dict) -> Dict:
        """Normalize ticket data from CRM format to standard format"""
        customer_no = data.get('customer_no')
        
        if customer_no:
            try:
                customer_id = str(int(customer_no)).zfill(5)
            except (ValueError, TypeError):
                customer_id = customer_no
        else:
            customer_id = None
        
        return {
            'id': data.get('ticket_id'),
            'customer_no': customer_id,
            'subject': data.get('subject'),
            'message': data.get('message') or data.get('description'),
            'status': data.get('status'),
            'priority': data.get('priority'),
            'category_id': data.get('category_name'),
            'assigned_to': data.get('assigned_to'),
            'department_id': data.get('department_id'),
            'created_at': data.get('created_at'),
            'resolution_description': data.get('resolution_description'),
            'solutions_checklist': data.get('solutions_checklist')
        }
    
    @staticmethod
    def _parse_float(value) -> float:
        """Parse float value safely"""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0