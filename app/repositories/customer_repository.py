"""
Customer Repository - Data access layer for customers
app/repositories/customer_repository.py
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.extensions import db
from app.models.customer import Customer
from app.models.company import Company


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
        
        Args:
            customer_data: Dictionary with customer data
            
        Returns:
            Created customer instance
        """
        customer = Customer(
            company_id=self.company_id,
            crm_customer_id=customer_data.get('id'),
            customer_name=customer_data.get('name'),
            email=customer_data.get('email'),
            phone=customer_data.get('phone'),
            address=customer_data.get('address'),
            status=customer_data.get('status', 'active'),
            account_type=customer_data.get('account_type'),
            monthly_charges=customer_data.get('monthly_charges', 0.0),
            total_charges=customer_data.get('total_charges', 0.0),
            outstanding_balance=customer_data.get('outstanding_balance', 0.0),
            service_type=customer_data.get('service_type'),
            connection_type=customer_data.get('connection_type'),
            bandwidth_plan=customer_data.get('bandwidth_plan'),
            signup_date=self._parse_date(customer_data.get('signup_date')),
            synced_at=datetime.utcnow()
        )
        
        # Calculate tenure
        customer.calculate_tenure()
        
        db.session.add(customer)
        
        return customer
    
    def update(self, customer: Customer, customer_data: Dict) -> Customer:
        """
        Update existing customer from dictionary
        
        Args:
            customer: Customer instance to update
            customer_data: Dictionary with updated data
            
        Returns:
            Updated customer instance
        """
        # Update fields
        customer.customer_name = customer_data.get('name', customer.customer_name)
        customer.email = customer_data.get('email', customer.email)
        customer.phone = customer_data.get('phone', customer.phone)
        customer.address = customer_data.get('address', customer.address)
        customer.status = customer_data.get('status', customer.status)
        customer.account_type = customer_data.get('account_type', customer.account_type)
        customer.monthly_charges = customer_data.get('monthly_charges', customer.monthly_charges)
        customer.total_charges = customer_data.get('total_charges', customer.total_charges)
        customer.outstanding_balance = customer_data.get('outstanding_balance', customer.outstanding_balance)
        customer.service_type = customer_data.get('service_type', customer.service_type)
        customer.connection_type = customer_data.get('connection_type', customer.connection_type)
        customer.bandwidth_plan = customer_data.get('bandwidth_plan', customer.bandwidth_plan)
        
        # Update dates
        if 'signup_date' in customer_data:
            customer.signup_date = self._parse_date(customer_data['signup_date'])
        
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
        crm_id = customer_data.get('id')
        
        if not crm_id:
            raise ValueError("Customer data must have 'id' field")
        
        # Check if customer exists
        customer = self.get_by_crm_id(crm_id)
        
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
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None