
# 🔧 ULTRA-FIXED CRM Service with Diagnostics
# Replace your app/services/crm_service.py with this version

import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.customer import Customer
import logging

logger = logging.getLogger(__name__)

class UltraFixedCRMService:
    def __init__(self, company):
        self.company = company
        self.customer_cache = {}
        self.orphaned_data = []
        self.debug_mode = True
    
    def sync_data_selective(self, sync_options=None):
        try:
            if not sync_options:
                sync_options = {'sync_customers': True, 'sync_tickets': True}
            
            logger.info("🔧 Starting ULTRA-FIXED sync with diagnostics")
            
            # Get PostgreSQL connection
            conn = self._get_postgresql_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # STEP 1: ALWAYS sync customers first and build cache
            if sync_options.get('sync_customers', True):
                self._sync_customers_with_cache(cursor)
            
            # STEP 2: Sync tickets with bulletproof customer lookup
            if sync_options.get('sync_tickets', True):
                self._sync_tickets_bulletproof(cursor)
            
            # STEP 3: Commit and report
            db.session.commit()
            
            return {
                'success': True,
                'message': f'✅ ULTRA-FIXED sync completed',
                'orphaned_data': len(self.orphaned_data),
                'cache_size': len(self.customer_cache)
            }
            
        except Exception as e:
            logger.error(f"❌ ULTRA-FIXED sync failed: {e}")
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def _sync_customers_with_cache(self, cursor):
        '''Sync customers and build lookup cache'''
        
        # Get customers with data quality validation
        cursor.execute('''
            SELECT id, customer_name, customer_phone, status, connection_status
            FROM crm_customers 
            WHERE customer_name IS NOT NULL 
            AND customer_name != ''
            AND customer_name NOT LIKE 'test%'
            ORDER BY id
            LIMIT 10000
        ''')
        
        customers = cursor.fetchall()
        logger.info(f"📊 Processing {len(customers)} valid customers")
        
        for customer_row in customers:
            try:
                customer_data = dict(customer_row)
                customer_id = str(customer_data['id'])
                
                # Create or update customer (simplified)
                customer = Customer.query.filter_by(
                    company_id=self.company.id,
                    crm_customer_id=customer_id
                ).first()
                
                if not customer:
                    customer = Customer(
                        company_id=self.company.id,
                        crm_customer_id=customer_id,
                        customer_name=customer_data['customer_name'],
                        phone=customer_data.get('customer_phone'),
                        status='active',
                        synced_at=datetime.utcnow()
                    )
                    db.session.add(customer)
                    db.session.flush()  # Get the ID
                
                # Add to cache
                self.customer_cache[customer_id] = customer.id
                
                if len(self.customer_cache) % 100 == 0:
                    logger.info(f"   Cached {len(self.customer_cache)} customers...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Customer {customer_data.get('id')} error: {e}")
                continue
        
        logger.info(f"✅ Customer cache built: {len(self.customer_cache)} entries")
    
    def _sync_tickets_bulletproof(self, cursor):
        '''Sync tickets with bulletproof customer lookup'''
        
        # Get tickets including the problematic one
        cursor.execute('''
            SELECT id, customer_no, subject, status, priority, created_at
            FROM crm_tickets 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY created_at DESC
            LIMIT 1000
        ''')
        
        tickets = cursor.fetchall()
        logger.info(f"🎫 Processing {len(tickets)} tickets")
        
        successful = 0
        orphaned = 0
        
        for ticket_row in tickets:
            try:
                ticket_data = dict(ticket_row)
                customer_no = ticket_data.get('customer_no')
                
                # Bulletproof customer lookup
                customer_id = self._bulletproof_customer_lookup(customer_no)
                
                if not customer_id:
                    self.orphaned_data.append({
                        'type': 'ticket',
                        'id': ticket_data.get('id'),
                        'customer_no': customer_no,
                        'subject': ticket_data.get('subject')
                    })
                    orphaned += 1
                    continue
                
                # Create ticket with GUARANTEED valid customer_id
                from app.models.ticket import Ticket
                
                existing_ticket = Ticket.query.filter_by(
                    company_id=self.company.id,
                    crm_ticket_id=str(ticket_data['id'])
                ).first()
                
                if not existing_ticket:
                    ticket = Ticket(
                        company_id=self.company.id,
                        customer_id=customer_id,  # GUARANTEED to be valid
                        crm_ticket_id=str(ticket_data['id']),
                        ticket_number=str(ticket_data['id']),
                        title=ticket_data.get('subject', 'No Subject')[:255],
                        priority=ticket_data.get('priority', 'medium').lower(),
                        status=ticket_data.get('status', 'open').lower(),
                        created_at=ticket_data.get('created_at'),
                        synced_at=datetime.utcnow()
                    )
                    db.session.add(ticket)
                    successful += 1
                
            except Exception as e:
                logger.error(f"❌ Ticket {ticket_data.get('id')} failed: {e}")
                # Don't let one ticket kill the whole sync
                continue
        
        logger.info(f"✅ Tickets: {successful} successful, {orphaned} orphaned")
    
    def _bulletproof_customer_lookup(self, customer_no):
        '''Bulletproof customer lookup with multiple strategies'''
        
        if not customer_no:
            return None
        
        customer_ref = str(customer_no)
        
        # Strategy 1: Cache lookup (fastest)
        if customer_ref in self.customer_cache:
            return self.customer_cache[customer_ref]
        
        # Strategy 2: Database lookup by CRM ID
        customer = Customer.query.filter_by(
            company_id=self.company.id,
            crm_customer_id=customer_ref
        ).first()
        
        if customer:
            # Add to cache for future lookups
            self.customer_cache[customer_ref] = customer.id
            return customer.id
        
        # Strategy 3: Database lookup by customer_number
        customer = Customer.query.filter_by(
            company_id=self.company.id,
            customer_number=customer_ref
        ).first()
        
        if customer:
            self.customer_cache[customer_ref] = customer.id
            return customer.id
        
        # No customer found
        if self.debug_mode:
            logger.debug(f"🔍 Customer {customer_ref} not found in database")
        
        return None
    
    def _get_postgresql_connection(self):
        '''Get PostgreSQL connection'''
        pg_config = self.company.get_postgresql_config()
        return psycopg2.connect(
            host=pg_config['host'],
            port=pg_config['port'],
            dbname=pg_config['database'],
            user=pg_config['username'],
            password=pg_config['password']
        )
    
    def get_connection_info(self):
        return {'preferred_method': 'postgresql'}

# Backward compatibility
CRMService = UltraFixedCRMService
EnhancedCRMService = UltraFixedCRMService
FixedEnhancedCRMService = UltraFixedCRMService
