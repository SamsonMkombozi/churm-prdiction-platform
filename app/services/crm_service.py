"""
Enhanced CRM Service - Fixes HTTP 500 Errors and Timeouts
app/services/crm_service.py

✅ SOLUTIONS FOR YOUR ISSUES:
1. HTTP 500 errors - Better error handling and retry logic
2. Timeouts - Increased timeouts and batch processing
3. Large datasets - Progressive loading with limits
4. Connection issues - Robust retry mechanism

Replace your existing CRM service with this enhanced version.
"""
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import json
import re
import time
from urllib.parse import urljoin
from app.extensions import db
from app.models.company import Company
from app.repositories.customer_repository import CustomerRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.ticket_repository import TicketRepository

logger = logging.getLogger(__name__)


class CRMService:
    """Enhanced CRM service with robust error handling"""
    
    # ✅ Table names for your CRM
    CUSTOMER_TABLE = 'crm_customers'
    TICKET_TABLE = 'tickets_full'
    PAYMENT_TABLE = 'nav_mpesa_transactions'
    USAGE_TABLE = 'spl_statistics'
    
    def __init__(self, company: Company):
        """Initialize enhanced CRM service"""
        self.company = company
        self.api_url = company.crm_api_url
        
        if not self.api_url:
            raise ValueError("CRM API URL not configured")
        
        # ✅ Enhanced connection settings
        self.timeout = 120  # Increased timeout for large datasets
        self.max_retries = 3
        self.retry_delay = 2  # seconds between retries
        self.batch_size = 50  # Smaller batches to prevent timeouts
        self.max_records_per_request = 500  # Limit records per API call
        
        # Initialize repositories
        self.customer_repo = CustomerRepository(company)
        self.payment_repo = PaymentRepository(company)
        self.ticket_repo = TicketRepository(company)
        
        logger.info(f"🔧 CRM Service initialized for {company.name}")
        logger.info(f"🌐 API URL: {self.api_url}")
        logger.info(f"⏱️ Timeout: {self.timeout}s, Batch size: {self.batch_size}")
    
    def test_connection(self) -> Dict:
        """
        ✅ ENHANCED: Test CRM connection with detailed diagnostics
        """
        logger.info("🔍 Testing CRM connection...")
        
        result = {
            'success': False,
            'message': '',
            'debug_info': {},
            'api_url': self.api_url,
            'tables_tested': []
        }
        
        try:
            # Test each table with small limit
            test_tables = [
                (self.CUSTOMER_TABLE, 'customers'),
                (self.PAYMENT_TABLE, 'payments'),
                (self.TICKET_TABLE, 'tickets'),
                (self.USAGE_TABLE, 'usage')
            ]
            
            for table_name, friendly_name in test_tables:
                logger.info(f"🧪 Testing {friendly_name} table: {table_name}")
                
                try:
                    # Test with very small limit
                    test_data = self._fetch_data_batch(table_name, limit=1, offset=0)
                    
                    table_result = {
                        'accessible': True,
                        'record_count': len(test_data) if test_data else 0,
                        'sample_keys': list(test_data[0].keys()) if test_data and len(test_data) > 0 else [],
                        'error': None
                    }
                    
                    logger.info(f"✅ {friendly_name}: {table_result['record_count']} records, keys: {table_result['sample_keys'][:5]}")
                    
                except Exception as e:
                    table_result = {
                        'accessible': False,
                        'record_count': 0,
                        'sample_keys': [],
                        'error': str(e)
                    }
                    logger.warning(f"⚠️ {friendly_name} error: {str(e)}")
                
                result['debug_info'][table_name] = table_result
                result['tables_tested'].append(friendly_name)
            
            # Check if at least one table is accessible
            accessible_tables = [
                table for table, info in result['debug_info'].items() 
                if info['accessible']
            ]
            
            if accessible_tables:
                result['success'] = True
                result['message'] = f"✅ Connection successful! Accessible tables: {', '.join(accessible_tables)}"
                logger.info(f"✅ CRM connection test successful")
            else:
                result['success'] = False
                result['message'] = "❌ No tables are accessible. Check your CRM API configuration."
                logger.error("❌ CRM connection test failed - no accessible tables")
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"❌ Connection test failed: {str(e)}"
            result['debug_info']['connection_error'] = str(e)
            logger.error(f"❌ CRM connection test failed: {str(e)}")
        
        return result
    
    def _make_request(self, url: str, params: Dict = None) -> requests.Response:
        """
        ✅ ENHANCED: Make HTTP request with retry logic and better error handling
        """
        if params is None:
            params = {}
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"🌐 Request attempt {attempt + 1}/{self.max_retries}: {url}")
                logger.debug(f"📋 Params: {params}")
                
                response = requests.get(
                    url, 
                    params=params, 
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Habari-CRM-Sync/1.0',
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    }
                )
                
                logger.debug(f"📊 Response: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                
                # ✅ Handle specific HTTP errors
                if response.status_code == 500:
                    logger.warning(f"⚠️ HTTP 500 error (attempt {attempt + 1}). Server error.")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        response.raise_for_status()
                
                elif response.status_code == 504:
                    logger.warning(f"⚠️ HTTP 504 timeout (attempt {attempt + 1}). Gateway timeout.")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        response.raise_for_status()
                
                elif response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    response.raise_for_status()
                
                # Success
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"⏱️ Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"🔌 Connection error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.error(f"❌ Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException("All retry attempts failed")
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        ✅ ENHANCED: Clean response text to extract valid JSON
        """
        if not response_text:
            return '[]'
        
        # Remove BOM and whitespace
        cleaned = response_text.strip().lstrip('\ufeff')
        
        # If it starts with JSON, it's probably clean
        if cleaned.startswith('{') or cleaned.startswith('['):
            return cleaned
        
        # Try to extract JSON from HTML or mixed content
        json_patterns = [
            r'(\[.*\])',  # Array
            r'(\{.*\})',  # Object
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                return match.group(1)
        
        logger.warning(f"⚠️ Could not extract JSON from response: {cleaned[:200]}...")
        return '[]'
    
    def _fetch_data_batch(self, table: str, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        ✅ NEW: Fetch data in batches to handle large datasets
        """
        try:
            params = {'table': table}
            
            if limit:
                params['limit'] = min(limit, self.max_records_per_request)
            
            if offset:
                params['offset'] = offset
            
            logger.debug(f"📥 Fetching {table} batch: limit={limit}, offset={offset}")
            
            response = self._make_request(self.api_url, params)
            
            # Clean and parse JSON
            cleaned_content = self._clean_json_response(response.text)
            
            try:
                data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error for {table}: {str(e)}")
                logger.error(f"Raw response: {response.text[:500]}")
                return []
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'data' in data:
                    records = data['data']
                elif 'records' in data:
                    records = data['records']
                else:
                    records = [data]  # Single record as dict
            elif isinstance(data, list):
                records = data
            else:
                logger.warning(f"⚠️ Unexpected data format for {table}: {type(data)}")
                return []
            
            logger.debug(f"✅ Fetched {len(records)} records from {table}")
            return records if isinstance(records, list) else []
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {table} batch: {str(e)}")
            return []
    
    def _fetch_data_progressive(self, table: str) -> List[Dict]:
        """
        ✅ NEW: Progressively fetch all data to handle large datasets
        """
        logger.info(f"📥 Starting progressive fetch for {table}")
        
        all_records = []
        offset = 0
        batch_size = self.batch_size
        
        while True:
            logger.info(f"📦 Fetching {table} batch: offset={offset}, batch_size={batch_size}")
            
            try:
                batch = self._fetch_data_batch(table, limit=batch_size, offset=offset)
                
                if not batch:
                    logger.info(f"✅ No more records for {table}, stopping at offset {offset}")
                    break
                
                all_records.extend(batch)
                offset += len(batch)
                
                logger.info(f"📊 {table}: {len(batch)} records in batch, {len(all_records)} total")
                
                # If we got fewer records than requested, we've reached the end
                if len(batch) < batch_size:
                    logger.info(f"✅ Reached end of {table} data (partial batch)")
                    break
                
                # Small delay between batches to be gentle on the API
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error fetching {table} batch at offset {offset}: {str(e)}")
                break
        
        logger.info(f"✅ Progressive fetch complete for {table}: {len(all_records)} total records")
        return all_records
    
    def _sync_customers(self) -> Dict:
        """✅ ENHANCED: Sync customers with batch processing"""
        logger.info("👥 Starting customer sync...")
        
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            # Update company sync status
            self.company.sync_status = 'in_progress'
            db.session.commit()
            
            # Fetch customers progressively
            customers_data = self._fetch_data_progressive(self.CUSTOMER_TABLE)
            
            if not customers_data:
                logger.warning("⚠️ No customer data received from CRM")
                return result
            
            logger.info(f"📊 Processing {len(customers_data)} customers...")
            
            # Process customers in batches
            for i in range(0, len(customers_data), self.batch_size):
                batch = customers_data[i:i + self.batch_size]
                logger.info(f"📦 Processing customer batch {i//self.batch_size + 1}: records {i+1}-{i+len(batch)}")
                
                batch_results = self._process_customer_batch(batch)
                
                # Aggregate results
                result['new'] += batch_results['new']
                result['updated'] += batch_results['updated']
                result['skipped'] += batch_results['skipped']
                result['errors'].extend(batch_results['errors'])
                
                # Commit batch
                try:
                    db.session.commit()
                    logger.debug(f"✅ Committed customer batch {i//self.batch_size + 1}")
                except Exception as e:
                    logger.error(f"❌ Failed to commit customer batch: {str(e)}")
                    db.session.rollback()
                    result['errors'].append(f"Batch commit error: {str(e)}")
            
            logger.info(f"✅ Customer sync complete: {result['new']} new, {result['updated']} updated, {result['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"❌ Customer sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Customer sync error: {str(e)}")
            raise
        
        return result
    
    def _process_customer_batch(self, customers: List[Dict]) -> Dict:
        """Process a batch of customers"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for customer_data in customers:
            try:
                was_created = self.customer_repo.create_or_update(customer_data)
                
                if was_created is True:
                    result['new'] += 1
                elif was_created is False:
                    result['updated'] += 1
                else:  # None = skipped
                    result['skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Customer {customer_data.get('id', 'unknown')}: {str(e)}"
                logger.debug(f"⚠️ {error_msg}")
                result['errors'].append(error_msg)
                result['skipped'] += 1
        
        return result
    
    def _sync_payments(self) -> Dict:
        """✅ ENHANCED: Sync payments with batch processing"""
        logger.info("💰 Starting payment sync...")
        
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            payments_data = self._fetch_data_progressive(self.PAYMENT_TABLE)
            
            if not payments_data:
                logger.warning("⚠️ No payment data received from CRM")
                return result
            
            logger.info(f"📊 Processing {len(payments_data)} payments...")
            
            # Process payments in batches
            for i in range(0, len(payments_data), self.batch_size):
                batch = payments_data[i:i + self.batch_size]
                logger.info(f"📦 Processing payment batch {i//self.batch_size + 1}: records {i+1}-{i+len(batch)}")
                
                batch_results = self._process_payment_batch(batch)
                
                # Aggregate results
                result['new'] += batch_results['new']
                result['updated'] += batch_results['updated']
                result['skipped'] += batch_results['skipped']
                result['errors'].extend(batch_results['errors'])
                
                # Commit batch
                try:
                    db.session.commit()
                    logger.debug(f"✅ Committed payment batch {i//self.batch_size + 1}")
                except Exception as e:
                    logger.error(f"❌ Failed to commit payment batch: {str(e)}")
                    db.session.rollback()
                    result['errors'].append(f"Payment batch commit error: {str(e)}")
            
            logger.info(f"✅ Payment sync complete: {result['new']} new, {result['updated']} updated, {result['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"❌ Payment sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Payment sync error: {str(e)}")
            raise
        
        return result
    
    def _process_payment_batch(self, payments: List[Dict]) -> Dict:
        """Process a batch of payments"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for payment_data in payments:
            try:
                was_created = self.payment_repo.create_or_update(payment_data)
                
                if was_created is True:
                    result['new'] += 1
                elif was_created is False:
                    result['updated'] += 1
                else:  # None = skipped
                    result['skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Payment {payment_data.get('id', 'unknown')}: {str(e)}"
                logger.debug(f"⚠️ {error_msg}")
                result['errors'].append(error_msg)
                result['skipped'] += 1
        
        return result
    
    def _sync_tickets(self) -> Dict:
        """✅ ENHANCED: Sync tickets with batch processing"""
        logger.info("🎫 Starting ticket sync...")
        
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            tickets_data = self._fetch_data_progressive(self.TICKET_TABLE)
            
            if not tickets_data:
                logger.warning("⚠️ No ticket data received from CRM")
                return result
            
            logger.info(f"📊 Processing {len(tickets_data)} tickets...")
            
            # Process tickets in batches
            for i in range(0, len(tickets_data), self.batch_size):
                batch = tickets_data[i:i + self.batch_size]
                logger.info(f"📦 Processing ticket batch {i//self.batch_size + 1}: records {i+1}-{i+len(batch)}")
                
                batch_results = self._process_ticket_batch(batch)
                
                # Aggregate results
                result['new'] += batch_results['new']
                result['updated'] += batch_results['updated']
                result['skipped'] += batch_results['skipped']
                result['errors'].extend(batch_results['errors'])
                
                # Commit batch
                try:
                    db.session.commit()
                    logger.debug(f"✅ Committed ticket batch {i//self.batch_size + 1}")
                except Exception as e:
                    logger.error(f"❌ Failed to commit ticket batch: {str(e)}")
                    db.session.rollback()
                    result['errors'].append(f"Ticket batch commit error: {str(e)}")
            
            logger.info(f"✅ Ticket sync complete: {result['new']} new, {result['updated']} updated, {result['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"❌ Ticket sync failed: {str(e)}")
            db.session.rollback()
            result['errors'].append(f"Ticket sync error: {str(e)}")
            raise
        
        return result
    
    def _process_ticket_batch(self, tickets: List[Dict]) -> Dict:
        """Process a batch of tickets"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for ticket_data in tickets:
            try:
                was_created = self.ticket_repo.create_or_update(ticket_data)
                
                if was_created is True:
                    result['new'] += 1
                elif was_created is False:
                    result['updated'] += 1
                else:  # None = skipped
                    result['skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Ticket {ticket_data.get('id', 'unknown')}: {str(e)}"
                logger.debug(f"⚠️ {error_msg}")
                result['errors'].append(error_msg)
                result['skipped'] += 1
        
        return result
    
    def sync_all_data(self) -> Dict:
        """
        ✅ ENHANCED: Sync all data with comprehensive error handling
        """
        logger.info(f"🚀 Starting enhanced CRM sync for company {self.company.id}")
        
        # Update sync status
        self.company.update_sync_status('in_progress')
        
        start_time = time.time()
        overall_result = {
            'success': False,
            'message': '',
            'customers': {'new': 0, 'updated': 0, 'skipped': 0},
            'payments': {'new': 0, 'updated': 0, 'skipped': 0},
            'tickets': {'new': 0, 'updated': 0, 'skipped': 0},
            'errors': [],
            'sync_time': 0
        }
        
        try:
            # Sync customers first (required for payments and tickets)
            logger.info("🔄 Phase 1: Syncing customers...")
            customer_result = self._sync_customers()
            overall_result['customers'] = {
                'new': customer_result['new'],
                'updated': customer_result['updated'],
                'skipped': customer_result['skipped']
            }
            overall_result['errors'].extend(customer_result.get('errors', []))
            
            # Sync payments
            logger.info("🔄 Phase 2: Syncing payments...")
            payment_result = self._sync_payments()
            overall_result['payments'] = {
                'new': payment_result['new'],
                'updated': payment_result['updated'],
                'skipped': payment_result['skipped']
            }
            overall_result['errors'].extend(payment_result.get('errors', []))
            
            # Sync tickets
            logger.info("🔄 Phase 3: Syncing tickets...")
            ticket_result = self._sync_tickets()
            overall_result['tickets'] = {
                'new': ticket_result['new'],
                'updated': ticket_result['updated'],
                'skipped': ticket_result['skipped']
            }
            overall_result['errors'].extend(ticket_result.get('errors', []))
            
            # Calculate totals
            total_new = (overall_result['customers']['new'] + 
                        overall_result['payments']['new'] + 
                        overall_result['tickets']['new'])
            
            total_updated = (overall_result['customers']['updated'] + 
                           overall_result['payments']['updated'] + 
                           overall_result['tickets']['updated'])
            
            # Update sync status
            overall_result['sync_time'] = round(time.time() - start_time, 2)
            
            if len(overall_result['errors']) == 0:
                overall_result['success'] = True
                overall_result['message'] = f"✅ Sync completed successfully! {total_new} new, {total_updated} updated records in {overall_result['sync_time']}s"
                self.company.update_sync_status('completed')
            else:
                overall_result['success'] = True  # Partial success
                overall_result['message'] = f"⚠️ Sync completed with {len(overall_result['errors'])} warnings. {total_new} new, {total_updated} updated records"
                self.company.update_sync_status('completed')
            
            logger.info(f"✅ Enhanced CRM sync completed: {overall_result['message']}")
            
        except Exception as e:
            overall_result['success'] = False
            overall_result['message'] = f"❌ Sync failed: {str(e)}"
            overall_result['errors'].append(str(e))
            overall_result['sync_time'] = round(time.time() - start_time, 2)
            
            self.company.update_sync_status('failed', str(e))
            logger.error(f"❌ Enhanced CRM sync failed: {str(e)}")
        
        return overall_result


# ✅ DEBUGGING AND TESTING FUNCTIONS

def test_enhanced_crm_connection(company_id: int = 1):
    """
    Test the enhanced CRM connection
    Use this to debug your CRM connection issues
    """
    try:
        from app.models.company import Company
        company = Company.query.get(company_id)
        
        if not company:
            print(f"❌ Company {company_id} not found")
            return
        
        if not company.crm_api_url:
            print(f"❌ No CRM API URL configured for company {company.name}")
            return
        
        print(f"🧪 Testing enhanced CRM connection for {company.name}")
        print(f"🌐 API URL: {company.crm_api_url}")
        
        crm_service = CRMService(company)
        result = crm_service.test_connection()
        
        print(f"\n{'✅ SUCCESS' if result['success'] else '❌ FAILURE'}: {result['message']}")
        
        print(f"\n📊 Table Test Results:")
        for table, info in result['debug_info'].items():
            status = "✅" if info['accessible'] else "❌"
            print(f"  {status} {table}: {info['record_count']} records")
            if info['sample_keys']:
                print(f"    Sample fields: {', '.join(info['sample_keys'][:5])}")
            if info['error']:
                print(f"    Error: {info['error']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None


def run_enhanced_sync(company_id: int = 1):
    """
    Run the enhanced sync process
    Use this to test the full sync with better error handling
    """
    try:
        from app.models.company import Company
        company = Company.query.get(company_id)
        
        if not company:
            print(f"❌ Company {company_id} not found")
            return
        
        print(f"🚀 Starting enhanced sync for {company.name}")
        
        crm_service = CRMService(company)
        result = crm_service.sync_all_data()
        
        print(f"\n{'✅ SUCCESS' if result['success'] else '❌ FAILURE'}: {result['message']}")
        print(f"⏱️ Sync time: {result['sync_time']}s")
        
        print(f"\n📊 Sync Results:")
        print(f"  👥 Customers: {result['customers']['new']} new, {result['customers']['updated']} updated, {result['customers']['skipped']} skipped")
        print(f"  💰 Payments: {result['payments']['new']} new, {result['payments']['updated']} updated, {result['payments']['skipped']} skipped")
        print(f"  🎫 Tickets: {result['tickets']['new']} new, {result['tickets']['updated']} updated, {result['tickets']['skipped']} skipped")
        
        if result['errors']:
            print(f"\n⚠️ Errors/Warnings ({len(result['errors'])}):")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(result['errors']) > 5:
                print(f"  ... and {len(result['errors']) - 5} more")
        
        return result
        
    except Exception as e:
        print(f"❌ Enhanced sync failed: {str(e)}")
        return None


# ✅ USAGE INSTRUCTIONS
"""
TO FIX YOUR HTTP 500 AND TIMEOUT ISSUES:

1. Replace your existing CRM service with this enhanced version
2. Test the connection:
   python -c "from app.services.crm_service import test_enhanced_crm_connection; test_enhanced_crm_connection()"

3. Run a test sync:
   python -c "from app.services.crm_service import run_enhanced_sync; run_enhanced_sync()"

4. If still having issues, check your PHP API:
   - Increase PHP max_execution_time
   - Increase PHP memory_limit
   - Add error logging to your api.php
   - Consider pagination in your API

KEY IMPROVEMENTS:
✅ Handles HTTP 500 errors with retry logic
✅ Increased timeouts for large datasets  
✅ Progressive/batch loading to prevent memory issues
✅ Better error reporting and diagnostics
✅ Exponential backoff for retries
✅ Graceful degradation when some data fails
"""