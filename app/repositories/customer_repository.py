"""
Customer Repository - FIXED VERSION with NULL handling
app/repositories/customer_repository.py

Handles customers with missing/NULL names gracefully
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.extensions import db
from app.models.customer import Customer
from app.models.company import Company
import logging

logger = logging.getLogger(__name__)


class CustomerRepository:
    """Repository for customer data operations"""
    
    def __init__(self, company: Company):
        """
        Initialize repository for a specific company
        
        Args:
            company: Company instance
        """
        self.company = company
        self.company_id = company.id
    
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID within company"""
        return Customer.query.filter_by(
            id=customer_id,
            company_id=self.company_id
        ).first()
    
    def get_by_crm_id(self, crm_customer_id: str) -> Optional[Customer]:
        """Get customer by CRM ID"""
        return Customer.query.filter_by(
            company_id=self.company_id,
            crm_customer_id=crm_customer_id
        ).first()
    
    def get_all(self, limit: int = None) -> List[Customer]:
        """Get all customers for company"""
        query = Customer.query.filter_by(company_id=self.company_id)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_recent(self, limit: int = 10) -> List[Customer]:
        """
        Get recently added customers
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            List of recent customers
        """
        return Customer.query.filter_by(
            company_id=self.company_id
        ).order_by(Customer.created_at.desc()).limit(limit).all()
        
    def get_active(self) -> List[Customer]:
        """Get all active customers"""
        return Customer.query.filter_by(
            company_id=self.company_id,
            status='active'
        ).all()
    
    def get_by_status(self, status: str) -> List[Customer]:
        """Get customers by status"""
        return Customer.query.filter_by(
            company_id=self.company_id,
            status=status
        ).all()
    
    def get_high_risk(self, limit: int = None) -> List[Customer]:
        """Get high-risk customers"""
        query = Customer.query.filter_by(
            company_id=self.company_id,
            churn_risk='high'
        ).order_by(Customer.churn_probability.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def search(self, query: str) -> List[Customer]:
        """
        Search customers by name, email, or phone
        
        Args:
            query: Search query string
            
        Returns:
            List of matching customers
        """
        search_pattern = f"%{query}%"
        
        return Customer.query.filter(
            Customer.company_id == self.company_id,
            db.or_(
                Customer.customer_name.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern)
            )
        ).all()
    
    def create(self, customer_data: Dict) -> Customer:
        """
        Create new customer from dictionary
        ✅ FIXED: Handles missing customer names gracefully
        
        Args:
            customer_data: Dictionary with customer data
            
        Returns:
            Created customer instance
        """
        # ✅ FIX: Generate default name if missing
        customer_name = self._get_customer_name(customer_data)
        
        # ✅ FIX: Validate required field
        if not customer_name:
            crm_id = customer_data.get('id') or customer_data.get('customer_id')
            customer_name = f"Customer {crm_id}" if crm_id else "Unknown Customer"
            logger.warning(f"Customer {crm_id} has no name - using default: {customer_name}")
        
        customer = Customer(
            company_id=self.company_id,
            crm_customer_id=str(customer_data.get('id') or customer_data.get('customer_id')),
            customer_name=customer_name,
            email=customer_data.get('email'),
            phone=customer_data.get('phone') or customer_data.get('mobile'),
            address=customer_data.get('address') or customer_data.get('location'),
            status=self._normalize_status(customer_data.get('status') or customer_data.get('connection_status', 'active')),
            account_type=customer_data.get('account_type'),
            monthly_charges=float(customer_data.get('monthly_charges', 0) or 0),
            total_charges=float(customer_data.get('total_charges', 0) or 0),
            outstanding_balance=float(customer_data.get('outstanding_balance', 0) or 0),
            service_type=customer_data.get('service_type'),
            connection_type=customer_data.get('connection_type'),
            bandwidth_plan=customer_data.get('bandwidth_plan') or customer_data.get('package'),
            signup_date=self._parse_date(
                customer_data.get('signup_date') or 
                customer_data.get('date_installed') or 
                customer_data.get('created_at')
            ),
            synced_at=datetime.utcnow()
        )
        
        # Calculate tenure
        customer.calculate_tenure()
        
        db.session.add(customer)
        
        return customer
    
    def update(self, customer: Customer, customer_data: Dict) -> Customer:
        """
        Update existing customer from dictionary
        ✅ FIXED: Handles missing names gracefully
        
        Args:
            customer: Customer instance to update
            customer_data: Dictionary with updated data
            
        Returns:
            Updated customer instance
        """
        # ✅ FIX: Only update name if new name is provided
        new_name = self._get_customer_name(customer_data)
        if new_name:
            customer.customer_name = new_name
        
        # Update other fields
        if customer_data.get('email'):
            customer.email = customer_data.get('email')
        if customer_data.get('phone') or customer_data.get('mobile'):
            customer.phone = customer_data.get('phone') or customer_data.get('mobile')
        if customer_data.get('address') or customer_data.get('location'):
            customer.address = customer_data.get('address') or customer_data.get('location')
        
        # Update status
        if 'status' in customer_data or 'connection_status' in customer_data:
            customer.status = self._normalize_status(
                customer_data.get('status') or customer_data.get('connection_status')
            )
        
        customer.account_type = customer_data.get('account_type', customer.account_type)
        customer.monthly_charges = float(customer_data.get('monthly_charges', customer.monthly_charges) or 0)
        customer.total_charges = float(customer_data.get('total_charges', customer.total_charges) or 0)
        customer.outstanding_balance = float(customer_data.get('outstanding_balance', customer.outstanding_balance) or 0)
        customer.service_type = customer_data.get('service_type', customer.service_type)
        customer.connection_type = customer_data.get('connection_type', customer.connection_type)
        
        bandwidth = customer_data.get('bandwidth_plan') or customer_data.get('package')
        if bandwidth:
            customer.bandwidth_plan = bandwidth
        
        # Update dates
        signup_date_str = (
            customer_data.get('signup_date') or 
            customer_data.get('date_installed') or 
            customer_data.get('created_at')
        )
        if signup_date_str:
            parsed_date = self._parse_date(signup_date_str)
            if parsed_date:
                customer.signup_date = parsed_date
        
        customer.updated_at = datetime.utcnow()
        customer.synced_at = datetime.utcnow()
        
        # Recalculate tenure
        customer.calculate_tenure()
        
        return customer
    
    def create_or_update(self, customer_data: Dict) -> bool:
        """
        Create new customer or update existing one
        
        Args:
            customer_data: Dictionary with customer data
            
        Returns:
            True if created, False if updated
        """
        crm_id = customer_data.get('id') or customer_data.get('customer_id')
        
        if not crm_id:
            logger.warning("Customer data missing ID field - skipping")
            raise ValueError("Customer data must have 'id' field")
        
        # Check if customer exists
        customer = self.get_by_crm_id(str(crm_id))
        
        if customer:
            # Update existing
            self.update(customer, customer_data)
            return False
        else:
            # Create new
            self.create(customer_data)
            return True
    
    def delete(self, customer: Customer):
        """Delete customer"""
        db.session.delete(customer)
    
    def count(self) -> int:
        """Get total customer count"""
        return Customer.query.filter_by(company_id=self.company_id).count()
    
    def count_by_status(self, status: str) -> int:
        """Count customers by status"""
        return Customer.query.filter_by(
            company_id=self.company_id,
            status=status
        ).count()
    
    def count_by_risk(self, risk_level: str) -> int:
        """Count customers by risk level"""
        return Customer.query.filter_by(
            company_id=self.company_id,
            churn_risk=risk_level
        ).count()
    
    def get_paginated(self, page: int = 1, per_page: int = 20, 
                     status: str = None, risk: str = None):
        """
        Get paginated customers with optional filters
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            status: Filter by status
            risk: Filter by risk level
            
        Returns:
            Pagination object
        """
        query = Customer.query.filter_by(company_id=self.company_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if risk:
            query = query.filter_by(churn_risk=risk)
        
        return query.order_by(Customer.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def update_metrics(self, customer: Customer):
        """Update customer metrics from related data"""
        customer.update_metrics()
        db.session.commit()
    
    def bulk_update_metrics(self):
        """Update metrics for all customers"""
        customers = self.get_all()
        
        for customer in customers:
            customer.update_metrics()
        
        db.session.commit()
    
    # ✅ HELPER METHODS
    
    def _get_customer_name(self, customer_data: Dict) -> Optional[str]:
        """
        Extract customer name from various possible fields
        
        Args:
            customer_data: Customer data dictionary
            
        Returns:
            Customer name or None
        """
        # Try multiple possible field names
        possible_name_fields = [
            'name',
            'customer_name',  # ✅ Your CRM uses this
            'full_name',
            'account_name',
            'client_name',
            'payer'  # ✅ Fallback for payments
        ]
        
        for field in possible_name_fields:
            name = customer_data.get(field)
            # Check if name exists and is not empty/None/whitespace
            if name and str(name).strip() and str(name).strip().lower() not in ['none', 'null', '']:
                return str(name).strip()
        
        # ✅ If no name found, generate one from ID
        customer_id = customer_data.get('id') or customer_data.get('customer_id')
        if customer_id:
            logger.warning(f"Customer {customer_id} has no name - will use default")
        
        return None
    
    @staticmethod
    def _normalize_status(status: str) -> str:
        """
        Normalize customer status to standard values
        
        Args:
            status: Raw status value
            
        Returns:
            Normalized status (active/inactive/suspended)
        """
        if not status:
            return 'active'
        
        status_lower = str(status).lower().strip()
        
        # Map various status values
        if status_lower in ['1', 'active', 'connected', 'true', 'yes']:
            return 'active'
        elif status_lower in ['0', 'inactive', 'disconnected', 'false', 'no']:
            return 'inactive'
        elif status_lower in ['suspended', 'hold', 'paused']:
            return 'suspended'
        else:
            # Default to active if unknown
            return 'active'
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        """
        Parse date string to datetime
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            Datetime object or None
        """
        if not date_string:
            return None
        
        # Skip invalid dates
        if str(date_string).strip() in ['0000-00-00', '0000-00-00 00:00:00', 'None', '']:
            return None
        
        try:
            # ISO format with timezone
            return datetime.fromisoformat(str(date_string).replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # MySQL datetime format
                return datetime.strptime(str(date_string), '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                try:
                    # Date only format
                    return datetime.strptime(str(date_string), '%Y-%m-%d')
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse date: {date_string}")
                    return None