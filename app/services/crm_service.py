"""
CRM Integration Service - FIXED for Your CRM API
app/services/crm_service.py

✅ Uses correct table names:
   - crm_customers (not customers)
   - tickets_full (not tickets)  
   - nav_mpesa_transaction (not payments)
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
    """Service for integrating with Habari CRM API"""
    
    # ✅ FIXED: Use correct table names for your CRM
    CUSTOMER_TABLE = 'crm_customers'  # Not 'customers'
    TICKET_TABLE = 'tickets_full'     # Not 'tickets'
    PAYMENT_TABLE = 'nav_mpesa_transaction'  # Not 'payments'
    USAGE_TABLE = 'spl_statistics'    # ✅ NEW: Usage statistics
    
    def __init__(self, company: Company):
        """
        Initialize CRM service for a company
        
        Args:
            company: Company instance with CRM configuration
        """
        self.company = company
        self.api_url = company.crm_api_url
        # ✅ Your CRM doesn't use API key - it's an open API
        self.api_key = None
        self.timeout = 30
        
        # Initialize repositories
        self.customer_repo = CustomerRepository(company)
        self.payment_repo = PaymentRepository(company)
        self.ticket_repo = TicketRepository(company)
        from app.repositories.usage_repository import UsageRepository
        self.usage_repo = UsageRepository(company)
        
        # Customer ID mapping cache (login -> customer_id)
        self.customer_mapping = {}
    
    def sync_all_data(self) -> Dict:
        """
        Sync all data from CRM
        
        Returns:
            Dictionary with sync results
        """
        logger.info(f"Starting CRM sync for company: {self.company.name}")
        
        # Update sync status
        self.company.sync_status = 'in_progress'
        self.company.sync_error = None
        db.session.commit()
        
        results = {
            'success': False,
            'customers': {'new': 0, 'updated': 0, 'skipped': 0},
            'usage': {'new': 0, 'updated': 0, 'skipped': 0},
            'payments': {'new': 0, 'updated': 0, 'skipped': 0},
            'tickets': {'new': 0, 'updated': 0, 'skipped': 0},
            'errors': []
        }
        
        try:
            # Step 1: Sync customers first (everything depends on them)
            logger.info("Syncing customers...")
            customer_results = self._sync_customers()
            results['customers'] = customer_results
            
            # Step 2: Build customer mapping from usage data
            logger.info("Building customer ID mapping...")
            self._build_customer_mapping()
            
            # Step 3: Sync usage statistics
            logger.info("Syncing usage statistics...")
            usage_results = self._sync_usage()
            results['usage'] = usage_results
            
            # Step 4: Sync payments (uses mapping for better matching)
            logger.info("Syncing payments...")
            payment_results = self._sync_payments()
            results['payments'] = payment_results
            
            # Step 5: Sync tickets
            logger.info("Syncing tickets...")
            ticket_results = self._sync_tickets()
            results['tickets'] = ticket_results
            
            # Mark as successful
            results['success'] = True
            self.company.sync_status = 'completed'
            self.company.last_sync_at = datetime.utcnow()
            self.company.total_syncs = (self.company.total_syncs or 0) + 1
            
            logger.info(f"Sync completed successfully: {results}")
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}", exc_info=True)
            results['success'] = False
            results['errors'].append(str(e))
            self.company.sync_status = 'failed'
            self.company.sync_error = str(e)
        
        finally:
            db.session.commit()
        
        return results
    
    def _sync_customers(self) -> Dict:
        """Sync customer data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0}
        
        # ✅ Fetch from correct table
        customers_data = self._fetch_data(self.CUSTOMER_TABLE)
        
        if not customers_data:
            logger.warning("No customer data received from CRM")
            return result
        
        logger.info(f"Processing {len(customers_data)} customers...")
        
        for customer_data in customers_data:
            try:
                # ✅ Map your CRM fields to standard fields
                normalized_data = self._normalize_customer_data(customer_data)
                
                # Create or update customer
                was_created = self.customer_repo.create_or_update(normalized_data)
                
                if was_created:
                    result['new'] += 1
                else:
                    result['updated'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to sync customer {customer_data.get('id')}: {str(e)}")
                result['skipped'] += 1
                continue
        
        # Commit after all customers
        try:
            db.session.commit()
            logger.info(f"Synced {result['new']} new, {result['updated']} updated customers")
        except Exception as e:
            logger.error(f"Failed to commit customers: {str(e)}")
            db.session.rollback()
            raise
        
        return result
    
    def _sync_payments(self) -> Dict:
        """Sync payment data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0}
        
        # ✅ Fetch from correct table
        payments_data = self._fetch_data(self.PAYMENT_TABLE)
        
        if not payments_data:
            logger.warning("No payment data received from CRM")
            return result
        
        logger.info(f"Processing {len(payments_data)} payments...")
        
        for payment_data in payments_data:
            try:
                # ✅ Map your CRM fields to standard fields
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
                logger.error(f"Failed to sync payment {payment_data.get('id')}: {str(e)}")
                result['skipped'] += 1
                continue
        
        # Commit after all payments
        try:
            db.session.commit()
            logger.info(f"Synced {result['new']} new, {result['updated']} updated, {result['skipped']} skipped (customers not found)")
        except Exception as e:
            logger.error(f"Failed to commit payments: {str(e)}")
            db.session.rollback()
            raise
        
        return result
    
    def _build_customer_mapping(self):
        """
        Build mapping between login IDs (SHO000XXX, CUST-XXX) and customer IDs
        Uses spl_statistics table which has both customer_id and login
        """
        logger.info("Fetching usage data to build customer mapping...")
        usage_data = self._fetch_data(self.USAGE_TABLE)
        
        if not usage_data:
            logger.warning("No usage data available for mapping")
            return
        
        # Build mapping: login -> crm_customer_id
        for record in usage_data:
            login = record.get('login')
            customer_id = record.get('customer_id')
            
            if login and customer_id:
                self.customer_mapping[login] = str(customer_id)
        
        logger.info(f"Built mapping for {len(self.customer_mapping)} login IDs")
    
    def _sync_usage(self) -> Dict:
        """Sync usage statistics from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0}
        
        # ✅ Fetch from correct table
        usage_data = self._fetch_data(self.USAGE_TABLE)
        
        if not usage_data:
            logger.warning("No usage data received from CRM")
            return result
        
        logger.info(f"Processing {len(usage_data)} usage records...")
        
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
        try:
            db.session.commit()
            logger.info(f"Synced {result['new']} new, {result['updated']} updated usage records")
        except Exception as e:
            logger.error(f"Failed to commit usage: {str(e)}")
            db.session.rollback()
            raise
        
        return result
    
    def _sync_tickets(self) -> Dict:
        """Sync ticket data from CRM"""
        result = {'new': 0, 'updated': 0, 'skipped': 0}
        
        # ✅ Fetch from correct table
        tickets_data = self._fetch_data(self.TICKET_TABLE)
        
        if not tickets_data:
            logger.warning("No ticket data received from CRM")
            return result
        
        logger.info(f"Processing {len(tickets_data)} tickets...")
        
        for ticket_data in tickets_data:
            try:
                # ✅ Map your CRM fields to standard fields
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
                logger.error(f"Failed to sync ticket {ticket_data.get('ticket_id')}: {str(e)}")
                result['skipped'] += 1
                continue
        
        # Commit after all tickets
        try:
            db.session.commit()
            logger.info(f"Synced {result['new']} new, {result['updated']} updated, {result['skipped']} skipped (customers not found)")
        except Exception as e:
            logger.error(f"Failed to commit tickets: {str(e)}")
            db.session.rollback()
            raise
        
        return result
    
    def _fetch_data(self, table_name: str) -> List[Dict]:
        """
        Fetch data from CRM API
        
        Args:
            table_name: Name of the table to fetch
            
        Returns:
            List of records
        """
        try:
            url = f"{self.api_url}?table={table_name}"
            
            logger.info(f"Fetching from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'error' in data:
                    logger.error(f"API error: {data['error']}")
                    return []
                
                # Try different keys
                records = data.get('data') or data.get('records') or [data]
            elif isinstance(data, list):
                records = data
            else:
                logger.warning(f"Unexpected response format for {table_name}")
                return []
            
            logger.info(f"Fetched {len(records)} records from {table_name}")
            return records
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {table_name}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {table_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {table_name}: {e}")
            raise
    
    # ✅ NORMALIZATION METHODS - Map your CRM fields to standard fields
    
    def _normalize_customer_data(self, data: Dict) -> Dict:
        """
        Normalize customer data from your CRM format to standard format
        
        Your CRM fields → Standard fields
        """
        return {
            'id': data.get('id'),
            'name': data.get('customer_name'),  # ✅ Your CRM uses 'customer_name'
            'email': data.get('customer_email'),
            'phone': data.get('customer_phone'),
            'address': data.get('address'),
            'status': data.get('connection_status') or data.get('status'),  # ✅ Your CRM has both
            'account_type': data.get('classification'),  # ✅ Your CRM uses 'classification'
            'monthly_charges': self._parse_float(data.get('customer_balance')),
            'total_charges': 0.0,  # Not available in your CRM
            'outstanding_balance': self._parse_float(data.get('customer_balance')),
            'service_type': data.get('category'),  # ✅ Your CRM uses 'category'
            'connection_type': data.get('routers'),  # ✅ Your CRM uses 'routers'
            'bandwidth_plan': data.get('package'),  # ✅ Your CRM uses 'package'
            'signup_date': data.get('date_installed') or data.get('created_at'),  # ✅ Use install date
            'disconnection_date': data.get('disconnection_date'),
            'churned_date': data.get('churned_date'),
            'region': data.get('splynx_location'),  # ✅ Your CRM has location
            'sector': data.get('sector'),
            'billing_frequency': data.get('billing_frequency')
        }
    
    def _normalize_payment_data(self, data: Dict) -> Dict:
        """
        Normalize payment data from your CRM format to standard format
        
        Your CRM fields → Standard fields
        """
        # ✅ Extract customer reference from account_no
        account_no = data.get('account_no')
        
        # Your payments have formats like:
        # - "CUST-885" (needs to extract just "885")
        # - "1014000001" (numeric)
        # - "SHO000000208" (alphanumeric)
        customer_ref = account_no
        
        # Try to extract numeric part from CUST-XXX format
        if account_no and 'CUST-' in str(account_no):
            try:
                # Extract number after CUST-, pad to 5 digits
                num = str(account_no).split('CUST-')[1]
                customer_ref = num.zfill(5)  # e.g., "885" -> "00885"
            except:
                customer_ref = account_no
        
        return {
            'id': data.get('id'),
            'account_no': customer_ref,  # ✅ Normalized customer reference
            'payer': data.get('payer'),  # ✅ Backup field (payer name)
            'transaction_id': data.get('mpesa_ref'),  # ✅ Your CRM uses 'mpesa_ref'
            'transaction_amount': self._parse_float(data.get('tx_amount')),  # ✅ Your CRM uses 'tx_amount'
            'transaction_time': data.get('tx_time'),  # ✅ Your CRM uses 'tx_time'
            'phone_number': data.get('phone_no'),  # ✅ Your CRM uses 'phone_no'
            'transaction_type': data.get('transaction_type') or 'payment',
            'status': 'completed' if data.get('posted_to_ledgers') == '1' else 'pending',  # ✅ Your CRM logic
            'created_at': data.get('created_at')
        }
    
    def _normalize_ticket_data(self, data: Dict) -> Dict:
        """
        Normalize ticket data from your CRM format to standard format
        
        Your CRM fields → Standard fields
        """
        # ✅ CRITICAL: Convert customer_no (e.g., "03505") to match customer ID format
        customer_no = data.get('customer_no')
        
        # Your CRM customers have IDs like "00001", tickets have "03505"
        # We need to pad/format to match
        if customer_no:
            # Remove leading zeros and re-pad to 5 digits to match customer ID format
            try:
                customer_id = str(int(customer_no)).zfill(5)
            except (ValueError, TypeError):
                customer_id = customer_no
        else:
            customer_id = None
        
        return {
            'id': data.get('ticket_id'),  # ✅ Your CRM uses 'ticket_id'
            'customer_no': customer_id,  # ✅ Normalized customer reference
            'subject': data.get('subject'),
            'message': data.get('message') or data.get('description'),
            'status': data.get('status'),
            'priority': data.get('priority'),
            'category_id': data.get('category_name'),  # ✅ Your CRM has category info
            'assigned_to': data.get('assigned_to'),
            'department_id': data.get('department_id'),
            'created_at': data.get('created_at'),
            'resolution_description': data.get('resolution_description'),
            'solutions_checklist': data.get('solutions_checklist')
        }
    
    # Helper methods
    
    @staticmethod
    def _parse_float(value) -> float:
        """Parse float value safely"""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def test_connection(self) -> Dict:
        """
        Test CRM API connection
        
        Returns:
            Dictionary with test results
        """
        try:
            # Try to fetch a small amount of customer data
            url = f"{self.api_url}?table={self.CUSTOMER_TABLE}&limit=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'message': 'Connection successful',
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }