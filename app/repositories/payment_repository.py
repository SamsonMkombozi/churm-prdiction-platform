"""
Payment Repository - FIXED VERSION
app/repositories/payment_repository.py
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.extensions import db
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.company import Company
import logging

logger = logging.getLogger(__name__)


class PaymentRepository:
    """Repository for payment data operations"""
    
    def __init__(self, company: Company):
        self.company = company
        self.company_id = company.id
    
    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        return Payment.query.filter_by(id=payment_id, company_id=self.company_id).first()
    
    def get_by_crm_id(self, crm_payment_id: str) -> Optional[Payment]:
        return Payment.query.filter_by(company_id=self.company_id, crm_payment_id=crm_payment_id).first()
    
    def get_all(self, limit: int = None) -> List[Payment]:
        query = Payment.query.filter_by(company_id=self.company_id)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_by_customer(self, customer_id: int) -> List[Payment]:
        return Payment.query.filter_by(company_id=self.company_id, customer_id=customer_id).order_by(Payment.payment_date.desc()).all()
    
    def get_by_status(self, status: str) -> List[Payment]:
        return Payment.query.filter_by(company_id=self.company_id, status=status).all()
    
    def get_recent(self, limit: int = 10) -> List[Payment]:
        return Payment.query.filter_by(company_id=self.company_id).order_by(Payment.payment_date.desc()).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Payment]:
        return Payment.query.filter(Payment.company_id == self.company_id, Payment.payment_date >= start_date, Payment.payment_date <= end_date).all()
    
    def create(self, payment_data: Dict) -> Optional[Payment]:
        """✅ FIXED: Returns None if customer not found"""
        customer = None
        customer_crm_id = payment_data.get('customer_id')
        
        if customer_crm_id:
            customer = Customer.query.filter_by(company_id=self.company_id, crm_customer_id=str(customer_crm_id)).first()
            
            if not customer:
                logger.warning(f"Skipping payment {payment_data.get('id')} - Customer {customer_crm_id} not found")
                return None
        else:
            logger.warning(f"Skipping payment {payment_data.get('id')} - No customer_id provided")
            return None
        
        payment = Payment(
            company_id=self.company_id,
            customer_id=customer.id,
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
        payment.transaction_id = payment_data.get('transaction_id', payment.transaction_id)
        payment.amount = payment_data.get('amount', payment.amount)
        payment.currency = payment_data.get('currency', payment.currency)
        payment.payment_method = payment_data.get('payment_method', payment.payment_method)
        payment.status = payment_data.get('status', payment.status)
        payment.description = payment_data.get('description', payment.description)
        payment.reference_number = payment_data.get('reference_number', payment.reference_number)
        payment.invoice_number = payment_data.get('invoice_number', payment.invoice_number)
        
        if 'payment_date' in payment_data:
            payment.payment_date = self._parse_date(payment_data['payment_date']) or payment.payment_date
        
        payment.updated_at = datetime.utcnow()
        payment.synced_at = datetime.utcnow()
        return payment
    
    def create_or_update(self, payment_data: Dict) -> Optional[bool]:
        """✅ FIXED: Returns None if payment skipped"""
        crm_id = payment_data.get('id')
        
        if not crm_id:
            logger.warning("Payment data missing 'id' field - skipping")
            return None
        
        payment = self.get_by_crm_id(str(crm_id))
        
        if payment:
            self.update(payment, payment_data)
            return False
        else:
            created_payment = self.create(payment_data)
            return True if created_payment else None
    
    def delete(self, payment: Payment):
        db.session.delete(payment)
    
    def count(self) -> int:
        return Payment.query.filter_by(company_id=self.company_id).count()
    
    def count_by_status(self, status: str) -> int:
        return Payment.query.filter_by(company_id=self.company_id, status=status).count()
    
    def get_total_revenue(self, start_date: datetime = None, end_date: datetime = None) -> float:
        query = db.session.query(db.func.sum(Payment.amount)).filter(Payment.company_id == self.company_id, Payment.status == 'completed')
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        return query.scalar() or 0.0
    
    def get_paginated(self, page: int = 1, per_page: int = 20, status: str = None):
        query = Payment.query.filter_by(company_id=self.company_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Payment.payment_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    def get_revenue_by_month(self, year: int) -> Dict:
        monthly_revenue = {}
        for month in range(1, 13):
            start_date = datetime(year, month, 1)
            end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
            revenue = self.get_total_revenue(start_date, end_date)
            monthly_revenue[month] = revenue
        return monthly_revenue
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
