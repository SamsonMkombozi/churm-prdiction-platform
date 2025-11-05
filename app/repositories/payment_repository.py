"""
Payment Repository - ENHANCED VERSION with tx_amount and account_no
app/repositories/payment_repository.py

✅ FIXES:
1. Uses 'tx_amount' field for transaction amount
2. Uses 'account_no' field for customer linking
3. Better error handling
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
        """
        Create new payment from dictionary
        ✅ ENHANCED: Uses 'tx_amount' and 'account_no' fields
        
        Sample data from your CRM:
        {
            "id": "123",
            "tx_amount": "2500",
            "account_no": "SHO000004481",
            "phone_no": "254725815558",
            "payer": "NOBERT GACHANJA SHAYO",
            "created_at": "2021-10-18 06:10:32",
            "transaction_time": "2021-10-18 09:10:30",
            "mpesa_reference": "ABC123XYZ",
            "posted_to_ledgers": 1,
            "is_refund": 0
        }
        """
        # ✅ FIX 1: Get customer ID from 'account_no' field
        customer_account_no = (
            payment_data.get('account_no') or      # Primary field in your CRM
            payment_data.get('payer') or           # Backup: use payer name
            payment_data.get('customer_id')        # Standard fallback
        )
        
        customer = None
        if customer_account_no:
            # Try to find customer by CRM customer ID (which matches account_no)
            customer = Customer.query.filter_by(
                company_id=self.company_id,
                crm_customer_id=str(customer_account_no)
            ).first()
            
            if not customer:
                logger.warning(
                    f"Skipping payment {payment_data.get('id')} - "
                    f"Customer with account_no {customer_account_no} not found in database"
                )
                return None
        else:
            logger.warning(
                f"Skipping payment {payment_data.get('id')} - "
                f"No account_no or payer provided"
            )
            return None
        
        # ✅ FIX 2: Use 'tx_amount' field for amount
        # Parse amount from tx_amount field
        try:
            amount = float(payment_data.get('tx_amount', 0) or 
                          payment_data.get('transaction_amount', 0) or 
                          payment_data.get('amount', 0) or 0)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount for payment {payment_data.get('id')}, using 0")
            amount = 0.0
        
        # Parse payment date - try transaction_time first, then created_at
        payment_date = self._parse_date(
            payment_data.get('transaction_time') or 
            payment_data.get('created_at')
        ) or datetime.utcnow()
        
        # Get MPESA reference or transaction ID
        transaction_id = (
            payment_data.get('mpesa_reference') or 
            payment_data.get('transaction_id') or
            payment_data.get('id')
        )
        
        # Determine payment status
        is_refund = payment_data.get('is_refund', 0)
        posted_to_ledgers = payment_data.get('posted_to_ledgers', 0)
        
        if is_refund:
            status = 'refunded'
        elif posted_to_ledgers:
            status = 'completed'
        else:
            status = payment_data.get('status', 'pending')
        
        # Get payer name
        payer_name = payment_data.get('payer', '')
        
        # Create payment with valid customer_id
        payment = Payment(
            company_id=self.company_id,
            customer_id=customer.id,  # Now guaranteed to be valid
            crm_payment_id=str(payment_data.get('id')),
            transaction_id=str(transaction_id),
            amount=amount,
            currency='TZS',  # Tanzanian Shilling
            payment_method='mobile_money',  # MPESA is mobile money
            payment_date=payment_date,
            status=status,
            description=f"MPESA payment from {payer_name}",
            reference_number=payment_data.get('mpesa_reference'),
            synced_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        logger.debug(f"✅ Created payment: Amount={amount}, Customer={customer_account_no}")
        return payment
    
    def update(self, payment: Payment, payment_data: Dict) -> Payment:
        """
        Update existing payment
        ✅ ENHANCED: Uses tx_amount and properly updates fields
        """
        # Update transaction ID
        if 'mpesa_reference' in payment_data:
            payment.transaction_id = str(payment_data.get('mpesa_reference') or payment.transaction_id)
        
        # ✅ Update amount from tx_amount
        if 'tx_amount' in payment_data or 'transaction_amount' in payment_data:
            try:
                new_amount = float(payment_data.get('tx_amount') or 
                                  payment_data.get('transaction_amount', payment.amount))
                payment.amount = new_amount
            except (ValueError, TypeError):
                pass  # Keep existing amount if parse fails
        
        # Update status based on flags
        if 'is_refund' in payment_data or 'posted_to_ledgers' in payment_data:
            is_refund = payment_data.get('is_refund', 0)
            posted_to_ledgers = payment_data.get('posted_to_ledgers', 0)
            
            if is_refund:
                payment.status = 'refunded'
            elif posted_to_ledgers:
                payment.status = 'completed'
            elif 'status' in payment_data:
                payment.status = payment_data.get('status')
        
        # Update payment date if provided
        if 'transaction_time' in payment_data:
            new_date = self._parse_date(payment_data['transaction_time'])
            if new_date:
                payment.payment_date = new_date
        
        # Update description if payer changed
        if 'payer' in payment_data:
            payer_name = payment_data.get('payer', '')
            payment.description = f"MPESA payment from {payer_name}"
        
        payment.updated_at = datetime.utcnow()
        payment.synced_at = datetime.utcnow()
        
        logger.debug(f"✅ Updated payment {payment.id}")
        return payment
    
    def create_or_update(self, payment_data: Dict) -> Optional[bool]:
        """
        Create new payment or update existing one
        Returns: True if created, False if updated, None if skipped
        """
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
        query = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.company_id == self.company_id,
            Payment.status == 'completed'
        )
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
        """Parse date string to datetime"""
        if not date_string:
            return None
        
        # Remove any extra whitespace
        date_string = str(date_string).strip()
        
        # Try various formats
        formats = [
            '%Y-%m-%d %H:%M:%S',  # "2021-10-18 09:10:30"
            '%Y-%m-%d',            # "2021-10-18"
            '%Y-%m-%dT%H:%M:%S',   # ISO format
            '%Y-%m-%dT%H:%M:%SZ'   # ISO format with Z
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except (ValueError, AttributeError):
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None