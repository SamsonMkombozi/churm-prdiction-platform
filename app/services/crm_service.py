"""
Enhanced CRM Service with Robust JSON Error Handling
app/services/crm_service.py

✅ FIXES:
- Better JSON parsing with multiple fallback strategies
- Handles malformed JSON responses
- Graceful degradation on parse errors
- Detailed error logging
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
from app.repositories.usage_repository import UsageRepository

logger = logging.getLogger(__name__)


class CRMService:
    """Enhanced CRM service with selective sync capabilities"""
    
    # Table names for your CRM
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
        
        # Connection settings
        self.timeout = 120
        self.max_retries = 3
        self.retry_delay = 2
        self.batch_size = 50
        self.max_records_per_request = 500
        
        # Initialize repositories
        self.customer_repo = CustomerRepository(company)
        self.payment_repo = PaymentRepository(company)
        self.ticket_repo = TicketRepository(company)
        self.usage_repo = UsageRepository(company)
        
        logger.info(f"🔧 CRM Service initialized for {company.name}")
    
    def test_connection(self) -> Dict:
        """Test CRM connection with detailed diagnostics"""
        logger.info("🔍 Testing CRM connection...")
        
        result = {
            'success': False,
            'message': '',
            'debug_info': {},
            'api_url': self.api_url,
            'tables_tested': []
        }
        
        try:
            test_tables = [
                (self.CUSTOMER_TABLE, 'customers'),
                (self.PAYMENT_TABLE, 'payments'),
                (self.TICKET_TABLE, 'tickets'),
                (self.USAGE_TABLE, 'usage')
            ]
            
            for table_name, friendly_name in test_tables:
                logger.info(f"🧪 Testing {friendly_name} table: {table_name}")
                
                try:
                    test_data = self._fetch_data_batch(table_name, limit=1, offset=0)
                    
                    table_result = {
                        'accessible': True,
                        'record_count': len(test_data) if test_data else 0,
                        'sample_keys': list(test_data[0].keys()) if test_data and len(test_data) > 0 else [],
                        'error': None
                    }
                    
                    logger.info(f"✅ {friendly_name}: {table_result['record_count']} records")
                    
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
            
            accessible_tables = [
                table for table, info in result['debug_info'].items() 
                if info['accessible']
            ]
            
            if accessible_tables:
                result['success'] = True
                result['message'] = f"✅ Connection successful! Accessible tables: {', '.join(accessible_tables)}"
            else:
                result['success'] = False
                result['message'] = "❌ No tables are accessible. Check your CRM API configuration."
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"❌ Connection test failed: {str(e)}"
            result['debug_info']['connection_error'] = str(e)
        
        return result
    
    def _make_request(self, url: str, params: Dict = None) -> requests.Response:
        """Make HTTP request with retry logic"""
        if params is None:
            params = {}
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"🌐 Request attempt {attempt + 1}/{self.max_retries}: {url}")
                
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
                
                if response.status_code in [500, 504]:
                    logger.warning(f"⚠️ HTTP {response.status_code} error (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        response.raise_for_status()
                
                elif response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    response.raise_for_status()
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"⏱️ Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"🔌 Connection error (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.error(f"❌ Request failed (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException("All retry attempts failed")
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        ✅ ENHANCED: Clean response text to extract valid JSON with better error handling
        """
        if not response_text:
            return '[]'
        
        # Remove BOM and whitespace
        cleaned = response_text.strip().lstrip('\ufeff')
        
        # If response is very short and looks broken, return empty array
        if len(cleaned) < 3:
            logger.warning(f"⚠️ Response too short: '{cleaned}' - returning empty array")
            return '[]'
        
        # Check for common broken JSON patterns
        if cleaned in ['{}', '{', '}', '[', ']', '[]']:
            logger.warning(f"⚠️ Incomplete JSON: '{cleaned}' - returning empty array")
            return '[]'
        
        # If it starts with JSON, it's probably clean
        if cleaned.startswith('{') or cleaned.startswith('['):
            # Quick validation check
            try:
                json.loads(cleaned)
                return cleaned
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON validation failed: {e} - attempting cleanup")
                # Try to fix common issues
                return self._attempt_json_repair(cleaned)
        
        # Try to extract JSON from HTML or mixed content
        json_patterns = [
            r'(\[.*\])',  # Array
            r'(\{.*\})',  # Object
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                extracted = match.group(1)
                # Validate extracted JSON
                try:
                    json.loads(extracted)
                    return extracted
                except json.JSONDecodeError:
                    continue
        
        logger.warning(f"⚠️ Could not extract valid JSON - returning empty array")
        return '[]'
    
    def _attempt_json_repair(self, broken_json: str) -> str:
        """
        ✅ NEW: Attempt to repair broken JSON
        """
        try:
            # Common fixes
            repaired = broken_json
            
            # Fix trailing commas in arrays
            repaired = re.sub(r',\s*]', ']', repaired)
            
            # Fix trailing commas in objects
            repaired = re.sub(r',\s*}', '}', repaired)
            
            # Fix missing closing brackets
            open_brackets = repaired.count('[')
            close_brackets = repaired.count(']')
            if open_brackets > close_brackets:
                repaired += ']' * (open_brackets - close_brackets)
            
            # Fix missing closing braces
            open_braces = repaired.count('{')
            close_braces = repaired.count('}')
            if open_braces > close_braces:
                repaired += '}' * (open_braces - close_braces)
            
            # Validate repair
            json.loads(repaired)
            logger.info("✅ Successfully repaired JSON")
            return repaired
            
        except Exception as e:
            logger.warning(f"⚠️ JSON repair failed: {e}")
            return '[]'
    
    def _fetch_data_batch(self, table: str, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        ✅ ENHANCED: Fetch data in batches with robust error handling
        """
        try:
            params = {'table': table}
            
            if limit:
                params['limit'] = min(limit, self.max_records_per_request)
            
            if offset:
                params['offset'] = offset
            
            response = self._make_request(self.api_url, params)
            
            # ✅ ENHANCED: Better response validation
            if not response.text or len(response.text.strip()) == 0:
                logger.warning(f"⚠️ Empty response for {table} at offset {offset}")
                return []
            
            cleaned_content = self._clean_json_response(response.text)
            
            # Additional validation before parsing
            if cleaned_content == '[]':
                logger.debug(f"Empty result set for {table} at offset {offset}")
                return []
            
            try:
                data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error for {table}: {str(e)}")
                logger.error(f"Response preview: {response.text[:500]}")
                logger.error(f"Cleaned preview: {cleaned_content[:500]}")
                # Return empty array instead of failing
                return []
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'data' in data:
                    records = data['data']
                elif 'records' in data:
                    records = data['records']
                else:
                    records = [data]
            elif isinstance(data, list):
                records = data
            else:
                logger.warning(f"⚠️ Unexpected data format for {table}: {type(data)}")
                return []
            
            # Validate records is actually a list
            if not isinstance(records, list):
                logger.warning(f"⚠️ Records is not a list for {table}: {type(records)}")
                return []
            
            return records
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {table} batch at offset {offset}: {str(e)}")
            # Return empty array instead of raising exception
            return []
    
    def _fetch_data_progressive(self, table: str, max_errors: int = 3) -> List[Dict]:
        """
        ✅ ENHANCED: Progressively fetch all data with error tolerance
        """
        logger.info(f"📥 Starting progressive fetch for {table}")
        
        all_records = []
        offset = 0
        batch_size = self.batch_size
        consecutive_errors = 0
        consecutive_empty = 0
        
        while True:
            logger.info(f"📦 Fetching {table} batch: offset={offset}")
            
            try:
                batch = self._fetch_data_batch(table, limit=batch_size, offset=offset)
                
                if not batch:
                    consecutive_empty += 1
                    logger.info(f"⚠️ Empty batch for {table} at offset {offset} (consecutive: {consecutive_empty})")
                    
                    # If we get 2 consecutive empty batches, we're probably at the end
                    if consecutive_empty >= 2:
                        logger.info(f"✅ Reached end of {table} data (consecutive empty batches)")
                        break
                    
                    # Move to next batch anyway
                    offset += batch_size
                    continue
                
                # Reset consecutive empty counter
                consecutive_empty = 0
                
                # Reset consecutive error counter on success
                consecutive_errors = 0
                
                all_records.extend(batch)
                offset += len(batch)
                
                logger.info(f"📊 {table}: {len(batch)} records in batch, {len(all_records)} total")
                
                # If we got fewer records than requested, we've reached the end
                if len(batch) < batch_size:
                    logger.info(f"✅ Reached end of {table} data (partial batch)")
                    break
                
                # Small delay between batches
                time.sleep(0.5)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Error fetching {table} batch at offset {offset} (error {consecutive_errors}/{max_errors}): {str(e)}")
                
                # If we hit max consecutive errors, stop
                if consecutive_errors >= max_errors:
                    logger.error(f"❌ Max consecutive errors reached for {table}, stopping fetch")
                    break
                
                # Try next batch
                offset += batch_size
                time.sleep(1)  # Longer delay after error
                continue
        
        logger.info(f"✅ Progressive fetch complete for {table}: {len(all_records)} total records")
        return all_records
    
    def _has_data_changed(self, data_type: str, new_data: List[Dict]) -> bool:
        """Check if data has changed since last sync"""
        if not new_data:
            logger.info(f"📝 No data for {data_type}, skipping")
            return False
        
        # Get last sync timestamp
        last_sync = self.company.last_sync_at
        
        if not last_sync:
            logger.info(f"📝 First sync for {data_type}, syncing all data")
            return True
        
        # Check if any record is newer than last sync
        date_fields = {
            'customers': ['created_at', 'updated_at'],
            'payments': ['created_at', 'transaction_time'],
            'tickets': ['created_at', 'updated_at'],
            'usage': ['created_at', 'start_date']
        }
        
        check_fields = date_fields.get(data_type, ['created_at'])
        changed_records = 0
        
        for record in new_data:
            for field in check_fields:
                if field in record and record[field]:
                    try:
                        record_date = self._parse_datetime(record[field])
                        if record_date and record_date > last_sync:
                            changed_records += 1
                            break
                    except:
                        continue
        
        logger.info(f"📊 {data_type}: {changed_records}/{len(new_data)} records changed since last sync")
        return changed_records > 0
    
    def _parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_string:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_string), fmt)
            except:
                continue
        
        return None
    
    def sync_selective_data(self, sync_options: Dict = None) -> Dict:
        """
        Sync selected data types with smart update detection
        """
        logger.info(f"🚀 Starting selective CRM sync for company {self.company.id}")
        
        # Default to sync all if no options provided
        if sync_options is None:
            sync_options = {
                'customers': True,
                'payments': True,
                'tickets': True,
                'usage': True
            }
        
        # Update sync status
        self.company.update_sync_status('in_progress')
        
        start_time = time.time()
        overall_result = {
            'success': False,
            'message': '',
            'customers': {'new': 0, 'updated': 0, 'skipped': 0, 'synced': False},
            'payments': {'new': 0, 'updated': 0, 'skipped': 0, 'synced': False},
            'tickets': {'new': 0, 'updated': 0, 'skipped': 0, 'synced': False},
            'usage': {'new': 0, 'updated': 0, 'skipped': 0, 'synced': False},
            'errors': [],
            'sync_time': 0
        }
        
        try:
            # Sync customers first (required for other entities)
            if sync_options.get('customers', False):
                logger.info("🔄 Phase 1: Checking customers...")
                customers_data = self._fetch_data_progressive(self.CUSTOMER_TABLE)
                
                if self._has_data_changed('customers', customers_data):
                    logger.info("📝 Customer data has changed, syncing...")
                    customer_result = self._sync_customers_batch(customers_data)
                    overall_result['customers'] = {
                        'new': customer_result['new'],
                        'updated': customer_result['updated'],
                        'skipped': customer_result['skipped'],
                        'synced': True
                    }
                    overall_result['errors'].extend(customer_result.get('errors', []))
                else:
                    logger.info("✅ No changes in customer data, skipping")
                    overall_result['customers']['synced'] = False
            
            # Sync payments
            if sync_options.get('payments', False):
                logger.info("🔄 Phase 2: Checking payments...")
                payments_data = self._fetch_data_progressive(self.PAYMENT_TABLE)
                
                if self._has_data_changed('payments', payments_data):
                    logger.info("📝 Payment data has changed, syncing...")
                    payment_result = self._sync_payments_batch(payments_data)
                    overall_result['payments'] = {
                        'new': payment_result['new'],
                        'updated': payment_result['updated'],
                        'skipped': payment_result['skipped'],
                        'synced': True
                    }
                    overall_result['errors'].extend(payment_result.get('errors', []))
                else:
                    logger.info("✅ No changes in payment data, skipping")
                    overall_result['payments']['synced'] = False
            
            # Sync tickets
            if sync_options.get('tickets', False):
                logger.info("🔄 Phase 3: Checking tickets...")
                tickets_data = self._fetch_data_progressive(self.TICKET_TABLE)
                
                if self._has_data_changed('tickets', tickets_data):
                    logger.info("📝 Ticket data has changed, syncing...")
                    ticket_result = self._sync_tickets_batch(tickets_data)
                    overall_result['tickets'] = {
                        'new': ticket_result['new'],
                        'updated': ticket_result['updated'],
                        'skipped': ticket_result['skipped'],
                        'synced': True
                    }
                    overall_result['errors'].extend(ticket_result.get('errors', []))
                else:
                    logger.info("✅ No changes in ticket data, skipping")
                    overall_result['tickets']['synced'] = False
            
            # Sync usage statistics
            if sync_options.get('usage', False):
                logger.info("🔄 Phase 4: Checking usage statistics...")
                usage_data = self._fetch_data_progressive(self.USAGE_TABLE)
                
                if self._has_data_changed('usage', usage_data):
                    logger.info("📝 Usage data has changed, syncing...")
                    usage_result = self._sync_usage_batch(usage_data)
                    overall_result['usage'] = {
                        'new': usage_result['new'],
                        'updated': usage_result['updated'],
                        'skipped': usage_result['skipped'],
                        'synced': True
                    }
                    overall_result['errors'].extend(usage_result.get('errors', []))
                else:
                    logger.info("✅ No changes in usage data, skipping")
                    overall_result['usage']['synced'] = False
            
            # Calculate totals
            total_new = sum(overall_result[key]['new'] for key in ['customers', 'payments', 'tickets', 'usage'])
            total_updated = sum(overall_result[key]['updated'] for key in ['customers', 'payments', 'tickets', 'usage'])
            
            # Update sync status
            overall_result['sync_time'] = round(time.time() - start_time, 2)
            
            if len(overall_result['errors']) == 0:
                overall_result['success'] = True
                if total_new == 0 and total_updated == 0:
                    overall_result['message'] = f"✅ Sync completed! No changes detected in selected data."
                else:
                    overall_result['message'] = f"✅ Sync completed successfully! {total_new} new, {total_updated} updated records in {overall_result['sync_time']}s"
                self.company.update_sync_status('completed')
            else:
                overall_result['success'] = True
                overall_result['message'] = f"⚠️ Sync completed with {len(overall_result['errors'])} warnings. {total_new} new, {total_updated} updated records"
                self.company.update_sync_status('completed')
            
            logger.info(f"✅ Selective sync completed: {overall_result['message']}")
            
        except Exception as e:
            overall_result['success'] = False
            overall_result['message'] = f"❌ Sync failed: {str(e)}"
            overall_result['errors'].append(str(e))
            overall_result['sync_time'] = round(time.time() - start_time, 2)
            
            self.company.update_sync_status('failed', str(e))
            logger.error(f"❌ Selective sync failed: {str(e)}")
        
        return overall_result
    
    # Keep existing batch sync methods
    def _sync_customers_batch(self, customers_data: List[Dict]) -> Dict:
        """Sync customers with batch processing"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for i in range(0, len(customers_data), self.batch_size):
            batch = customers_data[i:i + self.batch_size]
            
            for customer_data in batch:
                try:
                    was_created = self.customer_repo.create_or_update(customer_data)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Customer {customer_data.get('id')}: {str(e)}")
                    result['skipped'] += 1
            
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"❌ Failed to commit customer batch: {str(e)}")
                db.session.rollback()
        
        return result
    
    def _sync_payments_batch(self, payments_data: List[Dict]) -> Dict:
        """Sync payments with batch processing"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for i in range(0, len(payments_data), self.batch_size):
            batch = payments_data[i:i + self.batch_size]
            
            for payment_data in batch:
                try:
                    was_created = self.payment_repo.create_or_update(payment_data)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Payment {payment_data.get('id')}: {str(e)}")
                    result['skipped'] += 1
            
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"❌ Failed to commit payment batch: {str(e)}")
                db.session.rollback()
        
        return result
    
    def _sync_tickets_batch(self, tickets_data: List[Dict]) -> Dict:
        """Sync tickets with batch processing"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for i in range(0, len(tickets_data), self.batch_size):
            batch = tickets_data[i:i + self.batch_size]
            
            for ticket_data in batch:
                try:
                    was_created = self.ticket_repo.create_or_update(ticket_data)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Ticket {ticket_data.get('id')}: {str(e)}")
                    result['skipped'] += 1
            
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"❌ Failed to commit ticket batch: {str(e)}")
                db.session.rollback()
        
        return result
    
    def _sync_usage_batch(self, usage_data: List[Dict]) -> Dict:
        """Sync usage statistics with batch processing"""
        result = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        for i in range(0, len(usage_data), self.batch_size):
            batch = usage_data[i:i + self.batch_size]
            
            for usage_record in batch:
                try:
                    was_created = self.usage_repo.create_or_update(usage_record)
                    
                    if was_created is True:
                        result['new'] += 1
                    elif was_created is False:
                        result['updated'] += 1
                    else:
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Usage {usage_record.get('id')}: {str(e)}")
                    result['skipped'] += 1
            
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"❌ Failed to commit usage batch: {str(e)}")
                db.session.rollback()
        
        return result
    
    # Keep backward compatibility
    def sync_all_data(self) -> Dict:
        """Sync all data types (backward compatible method)"""
        return self.sync_selective_data({
            'customers': True,
            'payments': True,
            'tickets': True,
            'usage': True
        })