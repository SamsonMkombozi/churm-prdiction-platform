"""
CRM Service - Habari CRM Integration
app/services/crm_service.py

Handles all communication with Habari CRM API
"""
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app
from app.extensions import db
from app.models.company import Company
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class CRMService:
    """Service for Habari CRM integration"""
    
    def __init__(self, company: Company):
        """
        Initialize CRM service for a company
        
        Args:
            company: Company instance with CRM configuration
        """
        self.company = company
        self.api_url = company.crm_api_url
        self.timeout = current_app.config.get('CRM_API_TIMEOUT', 30)
        
        # Validate configuration
        if not self.api_url:
            raise ValueError("CRM API URL not configured for this company")
        
        try:
            self.api_key = company.api_key
        except Exception as e:
            raise ValueError(f"Failed to decrypt CRM API key: {e}")
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Dict = None, data: Dict = None) -> Dict:
        """
        Make authenticated request to CRM API
        
        Args:
            endpoint: API endpoint (e.g., 'customers', 'tickets')
            method: HTTP method
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"CRM API Request: {method} {url}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"CRM API timeout: {url}")
            raise Exception("CRM API request timed out")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"CRM API HTTP error: {e}")
            raise Exception(f"CRM API error: {e.response.status_code}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"CRM API request failed: {e}")
            raise Exception(f"Failed to connect to CRM: {str(e)}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to CRM API
        
        Returns:
            (success, message) tuple
        """
        try:
            # Try to fetch a simple endpoint
            response = self._make_request('status')
            
            if response.get('status') == 'ok':
                return True, "Connection successful"
            else:
                return False, "Unexpected response from CRM"
                
        except Exception as e:
            return False, str(e)
    
    def fetch_customers(self, limit: int = 1000, 
                       since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch customers from CRM
        
        Args:
            limit: Maximum number of customers to fetch
            since: Only fetch customers updated since this date
            
        Returns:
            List of customer dictionaries
        """
        params = {'limit': limit}
        
        if since:
            params['since'] = since.isoformat()
        
        try:
            response = self._make_request('customers', params=params)
            customers = response.get('data', [])
            
            logger.info(f"Fetched {len(customers)} customers from CRM")
            return customers
            
        except Exception as e:
            logger.error(f"Failed to fetch customers: {e}")
            raise
    
    def fetch_tickets(self, limit: int = 1000, 
                     since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch support tickets from CRM
        
        Args:
            limit: Maximum number of tickets to fetch
            since: Only fetch tickets updated since this date
            
        Returns:
            List of ticket dictionaries
        """
        params = {'limit': limit}
        
        if since:
            params['since'] = since.isoformat()
        
        try:
            response = self._make_request('tickets', params=params)
            tickets = response.get('data', [])
            
            logger.info(f"Fetched {len(tickets)} tickets from CRM")
            return tickets
            
        except Exception as e:
            logger.error(f"Failed to fetch tickets: {e}")
            raise
    
    def fetch_payments(self, limit: int = 1000, 
                      since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch payment transactions from CRM
        
        Args:
            limit: Maximum number of payments to fetch
            since: Only fetch payments since this date
            
        Returns:
            List of payment dictionaries
        """
        params = {'limit': limit}
        
        if since:
            params['since'] = since.isoformat()
        
        try:
            response = self._make_request('payments', params=params)
            payments = response.get('data', [])
            
            logger.info(f"Fetched {len(payments)} payments from CRM")
            return payments
            
        except Exception as e:
            logger.error(f"Failed to fetch payments: {e}")
            raise
    
    def sync_customers(self) -> Dict:
        """
        Sync customers from CRM to database
        
        Returns:
            Dictionary with sync results
        """
        from app.repositories.customer_repository import CustomerRepository
        
        try:
            # Fetch customers from CRM
            customers_data = self.fetch_customers()
            
            repo = CustomerRepository(self.company)
            
            created = 0
            updated = 0
            errors = 0
            
            for customer_data in customers_data:
                try:
                    is_new = repo.create_or_update(customer_data)
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync customer {customer_data.get('id')}: {e}")
                    errors += 1
            
            # Commit all changes
            db.session.commit()
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(customers_data)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Customer sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_tickets(self) -> Dict:
        """
        Sync support tickets from CRM to database
        
        Returns:
            Dictionary with sync results
        """
        from app.repositories.ticket_repository import TicketRepository
        
        try:
            # Fetch tickets from CRM
            tickets_data = self.fetch_tickets()
            
            repo = TicketRepository(self.company)
            
            created = 0
            updated = 0
            errors = 0
            
            for ticket_data in tickets_data:
                try:
                    is_new = repo.create_or_update(ticket_data)
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync ticket {ticket_data.get('id')}: {e}")
                    errors += 1
            
            # Commit all changes
            db.session.commit()
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(tickets_data)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ticket sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_payments(self) -> Dict:
        """
        Sync payment transactions from CRM to database
        
        Returns:
            Dictionary with sync results
        """
        from app.repositories.payment_repository import PaymentRepository
        
        try:
            # Fetch payments from CRM
            payments_data = self.fetch_payments()
            
            repo = PaymentRepository(self.company)
            
            created = 0
            updated = 0
            errors = 0
            
            for payment_data in payments_data:
                try:
                    is_new = repo.create_or_update(payment_data)
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync payment {payment_data.get('id')}: {e}")
                    errors += 1
            
            # Commit all changes
            db.session.commit()
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(payments_data)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Payment sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_data(self, full_sync: bool = True) -> Dict:
        """
        Perform complete data synchronization
        
        Args:
            full_sync: If True, sync all data. If False, only recent changes.
            
        Returns:
            Dictionary with comprehensive sync results
        """
        logger.info(f"Starting {'full' if full_sync else 'incremental'} sync for company {self.company.id}")
        
        # Update sync status to in_progress
        self.company.update_sync_status('in_progress')
        
        results = {
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat(),
            'customers': {},
            'tickets': {},
            'payments': {}
        }
        
        try:
            # Sync customers
            logger.info("Syncing customers...")
            results['customers'] = self.sync_customers()
            
            # Sync tickets
            logger.info("Syncing tickets...")
            results['tickets'] = self.sync_tickets()
            
            # Sync payments
            logger.info("Syncing payments...")
            results['payments'] = self.sync_payments()
            
            # Calculate totals
            total_created = (
                results['customers'].get('created', 0) +
                results['tickets'].get('created', 0) +
                results['payments'].get('created', 0)
            )
            
            total_updated = (
                results['customers'].get('updated', 0) +
                results['tickets'].get('updated', 0) +
                results['payments'].get('updated', 0)
            )
            
            # Update company sync status
            self.company.update_sync_status('completed')
            
            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()
            results['summary'] = {
                'total_created': total_created,
                'total_updated': total_updated,
                'message': f'Successfully synced {total_created} new and {total_updated} updated records'
            }
            
            logger.info(f"Sync completed successfully: {results['summary']['message']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Sync failed with error: {e}")
            
            # Update company sync status to failed
            self.company.update_sync_status('failed', error=str(e))
            
            results['status'] = 'error'
            results['error'] = str(e)
            results['message'] = f'Sync failed: {str(e)}'
            
            return results
    
    def sync_incremental(self) -> Dict:
        """
        Sync only recent changes (since last sync)
        
        Returns:
            Dictionary with sync results
        """
        # Get last sync time
        since = self.company.last_sync_at
        
        if not since:
            # No previous sync, do full sync
            return self.sync_data(full_sync=True)
        
        logger.info(f"Incremental sync since {since}")
        
        # Perform incremental sync
        return self.sync_data(full_sync=False)


# Utility functions for background sync tasks

def sync_company_data(company_id: int) -> Dict:
    """
    Sync data for a specific company (can be used as background task)
    
    Args:
        company_id: Company ID to sync
        
    Returns:
        Sync results dictionary
    """
    company = Company.query.get(company_id)
    
    if not company:
        return {'status': 'error', 'message': 'Company not found'}
    
    if not company.is_active:
        return {'status': 'error', 'message': 'Company is inactive'}
    
    try:
        crm_service = CRMService(company)
        return crm_service.sync_data()
        
    except Exception as e:
        logger.error(f"Failed to sync company {company_id}: {e}")
        return {'status': 'error', 'message': str(e)}


def sync_all_companies() -> Dict:
    """
    Sync data for all active companies
    
    Returns:
        Summary of sync results for all companies
    """
    companies = Company.query.filter_by(is_active=True).all()
    
    results = {
        'total_companies': len(companies),
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    for company in companies:
        logger.info(f"Syncing company: {company.name}")
        
        try:
            sync_result = sync_company_data(company.id)
            
            if sync_result.get('status') == 'completed':
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'company_id': company.id,
                'company_name': company.name,
                'result': sync_result
            })
            
        except Exception as e:
            logger.error(f"Failed to sync {company.name}: {e}")
            results['failed'] += 1
            results['details'].append({
                'company_id': company.id,
                'company_name': company.name,
                'error': str(e)
            })
    
    return results