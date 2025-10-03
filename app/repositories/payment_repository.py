"""
Payment Repository - Data access layer for payment transactions
app/repositories/payment_repository.py
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.extensions import db
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.company import Company


class PaymentRepository:
    """Repository for payment data operations"""
    
    def __init__(self, company: Company):
        """
        Initialize repository for a specific company
        
        Args:
            company: Company instance
        """
        self.company = company
        self.company_id = company.id
    
    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID within company"""
        return Payment.query.filter_by(
            id=payment_id,
            company_id=self.company_id
        ).first()
    
    def get_by_crm_id(self, crm_payment_id: str) -> Optional[Payment]:
        """Get payment by CRM ID"""
        return Payment.query.filter_by(
            company_id=self.company_id,
            crm_payment_id=crm_payment_id
        ).first()
    
    def get_all(self, limit: int = None) -> List[Payment]:
        """Get all payments for company"""
        query = Payment.query.filter_by(company_id=self.company_id)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_customer(self, customer_id: int) -> List[Payment]:
        """Get all payments for a customer"""
        return Payment.query.filter_by(
            company_id=self.company_id,
            customer_id=customer_id
        ).order_by(Payment.payment_date.desc()).all()
    
    def get_by_status(self, status: str) -> List[Payment]:
        """Get payments by status"""
        return Payment.query.filter_by(
            company_id=self.company_id,
            status=status
        ).all()
    
    def get_recent(self, limit: int = 10) -> List[Payment]:
        """Get recent payments"""
        return Payment.query.filter_by(
            company_id=self.company_id
        ).order_by(Payment.payment_date.desc()).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, 
                          end_date: datetime) -> List[Payment]:
        """Get payments within date range"""
        return Payment.query.filter(
            Payment.company_id == self.company_id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        ).all()
    
    def create(self, payment_data: Dict) -> Payment:
        """
        Create new payment from dictionary
        
        Args:
            payment_data: Dictionary with payment data
            
        Returns:
            Created payment instance
        """
        # Find customer by CRM ID
        customer = None
        if 'customer_id' in payment_data:
            customer = Customer.find_by_crm_id(
                self.company_id,
                payment_data['customer_id']
            )
        
        payment = Payment(
            company_id=self.company_id,
            customer_id=customer.id if customer else None,
            crm_payment_id=payment_data.get('id'),
            transaction_id=payment_data.get('transaction_id'),
            amount=payment_data.get('amount', 0.0),
            currency=payment_data.get('currency', 'USD'),
            payment_method=payment_data.get('payment_method'),
            payment_date=self._parse_date(payment_data.get('payment_date')) or datetime.utcnow(),
            status=payment_data.get('status', 'completed'),
            description=payment_data.get('description'),
            reference_number=payment_data.get('reference_number'),
            invoice_number=payment_data.get('invoice_number'),
            synced_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        
        return payment
    
    def update(self, payment: Payment, payment_data: Dict) -> Payment:
        """
        Update existing payment from dictionary
        
        Args:
            payment: Payment instance to update
            payment_data: Dictionary with updated data
            
        Returns:
            Updated payment instance
        """
        # Update fields
        payment.transaction_id = payment_data.get('transaction_id', payment.transaction_id)
        payment.amount = payment_data.get('amount', payment.amount)
        payment.currency = payment_data.get('currency', payment.currency)
        payment.payment_method = payment_data.get('payment_method', payment.payment_method)
        payment.status = payment_data.get('status', payment.status)
        payment.description = payment_data.get('description', payment.description)
        payment.reference_number = payment_data.get('reference_number', payment.reference_number)
        payment.invoice_number = payment_data.get('invoice_number', payment.invoice_number)
        
        # Update dates
        if 'payment_date' in payment_data:
            payment.payment_date = self._parse_date(payment_data['payment_date']) or payment.payment_date
        
        payment.updated_at = datetime.utcnow()
        payment.synced_at = datetime.utcnow()
        
        return payment
    
    def create_or_update(self, payment_data: Dict) -> bool:
        """
        Create new payment or update existing one
        
        Args:
            payment_data: Dictionary with payment data
            
        Returns:
            True if created, False if updated
        """
        crm_id = payment_data.get('id')
        
        if not crm_id:
            raise ValueError("Payment data must have 'id' field")
        
        # Check if payment exists
        payment = self.get_by_crm_id(crm_id)
        
        if payment:
            # Update existing
            self.update(payment, payment_data)
            return False
        else:
            # Create new
            self.create(payment_data)
            return True
    
    def delete(self, payment: Payment):
        """Delete payment"""
        db.session.delete(payment)
    
    def count(self) -> int:
        """Get total payment count"""
        return Payment.query.filter_by(company_id=self.company_id).count()
    
    def count_by_status(self, status: str) -> int:
        """Count payments by status"""
        return Payment.query.filter_by(
            company_id=self.company_id,
            status=status
        ).count()
    
    def get_total_revenue(self, start_date: datetime = None,
                         end_date: datetime = None) -> float:
        """
        Calculate total revenue
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Total revenue amount
        """
        query = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.company_id == self.company_id,
            Payment.status == 'completed'
        )
        
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        
        return query.scalar() or 0.0
    
    def get_paginated(self, page: int = 1, per_page: int = 20,
                     status: str = None):
        """
        Get paginated payments with optional filters
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            status: Filter by status
            
        Returns:
            Pagination object
        """
        query = Payment.query.filter_by(company_id=self.company_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Payment.payment_date.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def get_revenue_by_month(self, year: int) -> Dict:
        """
        Get monthly revenue for a year
        
        Args:
            year: Year to analyze
            
        Returns:
            Dictionary with monthly revenue
        """
        monthly_revenue = {}
        
        for month in range(1, 13):
            start_date = datetime(year, month, 1)
            
            # Calculate end date
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            revenue = self.get_total_revenue(start_date, end_date)
            monthly_revenue[month] = revenue
        
        return monthly_revenue
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None