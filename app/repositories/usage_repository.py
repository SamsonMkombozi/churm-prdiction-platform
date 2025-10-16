"""
Usage Statistics Repository
app/repositories/usage_repository.py
"""
from datetime import datetime, date, time
from typing import List, Optional, Dict
from app.extensions import db
from app.models.usage_stats import UsageStats
from app.models.customer import Customer
from app.models.company import Company
import logging

logger = logging.getLogger(__name__)


class UsageRepository:
    """Repository for usage statistics data operations"""
    
    def __init__(self, company: Company):
        self.company = company
        self.company_id = company.id
    
    def get_by_id(self, usage_id: int) -> Optional[UsageStats]:
        return UsageStats.query.filter_by(id=usage_id, company_id=self.company_id).first()
    
    def get_by_crm_id(self, crm_usage_id: str) -> Optional[UsageStats]:
        return UsageStats.query.filter_by(
            company_id=self.company_id,
            crm_usage_id=crm_usage_id
        ).first()
    
    def get_by_customer(self, customer_id: int, limit: int = 100) -> List[UsageStats]:
        return UsageStats.query.filter_by(
            company_id=self.company_id,
            customer_id=customer_id
        ).order_by(UsageStats.start_date.desc()).limit(limit).all()
    
    def create(self, usage_data: Dict) -> Optional[UsageStats]:
        """Create new usage record"""
        # Find customer by CRM ID or login
        customer_crm_id = usage_data.get('customer_id')
        login = usage_data.get('login')
        
        customer = None
        if customer_crm_id:
            customer = Customer.query.filter_by(
                company_id=self.company_id,
                crm_customer_id=str(customer_crm_id)
            ).first()
        
        # If not found by ID, try login (some CRMs use login as customer reference)
        if not customer and login:
            customer = Customer.query.filter_by(
                company_id=self.company_id,
                crm_customer_id=login
            ).first()
        
        if not customer:
            logger.debug(
                f"Skipping usage record {usage_data.get('id')} - "
                f"Customer {customer_crm_id} or login {login} not found"
            )
            return None
        
        # Parse dates and times
        start_date = self._parse_date(usage_data.get('start_date'))
        start_time = self._parse_time(usage_data.get('start_time'))
        end_date = self._parse_date(usage_data.get('end_date'))
        end_time = self._parse_time(usage_data.get('end_time'))
        
        # Parse bytes
        in_bytes = int(usage_data.get('in_bytes', 0) or 0)
        out_bytes = int(usage_data.get('out_bytes', 0) or 0)
        
        usage = UsageStats(
            company_id=self.company_id,
            customer_id=customer.id,
            crm_usage_id=str(usage_data.get('id')),
            crm_customer_id=str(customer_crm_id),
            service_id=usage_data.get('service_id'),
            tariff_id=usage_data.get('tariff_id'),
            login=login,
            in_bytes=in_bytes,
            out_bytes=out_bytes,
            total_bytes=in_bytes + out_bytes,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            synced_at=datetime.utcnow()
        )
        
        # Calculate duration
        usage.calculate_duration()
        
        db.session.add(usage)
        return usage
    
    def update(self, usage: UsageStats, usage_data: Dict) -> UsageStats:
        """Update existing usage record"""
        # Update bytes
        in_bytes = int(usage_data.get('in_bytes', usage.in_bytes) or 0)
        out_bytes = int(usage_data.get('out_bytes', usage.out_bytes) or 0)
        
        usage.in_bytes = in_bytes
        usage.out_bytes = out_bytes
        usage.total_bytes = in_bytes + out_bytes
        
        # Update dates if provided
        if 'start_date' in usage_data:
            usage.start_date = self._parse_date(usage_data['start_date'])
        if 'start_time' in usage_data:
            usage.start_time = self._parse_time(usage_data['start_time'])
        if 'end_date' in usage_data:
            usage.end_date = self._parse_date(usage_data['end_date'])
        if 'end_time' in usage_data:
            usage.end_time = self._parse_time(usage_data['end_time'])
        
        usage.updated_at = datetime.utcnow()
        usage.synced_at = datetime.utcnow()
        
        # Recalculate duration
        usage.calculate_duration()
        
        return usage
    
    def create_or_update(self, usage_data: Dict) -> Optional[bool]:
        """Create or update usage record"""
        crm_id = usage_data.get('id')
        
        if not crm_id:
            logger.warning("Usage data missing 'id' field - skipping")
            return None
        
        usage = self.get_by_crm_id(str(crm_id))
        
        if usage:
            self.update(usage, usage_data)
            return False
        else:
            created_usage = self.create(usage_data)
            return True if created_usage else None
    
    def get_customer_total_usage(self, customer_id: int) -> Dict:
        """Get total usage statistics for a customer"""
        result = db.session.query(
            db.func.sum(UsageStats.total_bytes).label('total'),
            db.func.sum(UsageStats.in_bytes).label('download'),
            db.func.sum(UsageStats.out_bytes).label('upload'),
            db.func.count(UsageStats.id).label('sessions'),
            db.func.sum(UsageStats.session_duration_minutes).label('total_minutes')
        ).filter_by(
            company_id=self.company_id,
            customer_id=customer_id
        ).first()
        
        return {
            'total_bytes': result.total or 0,
            'total_gb': round((result.total or 0) / (1024**3), 2),
            'download_bytes': result.download or 0,
            'upload_bytes': result.upload or 0,
            'total_sessions': result.sessions or 0,
            'total_minutes': result.total_minutes or 0
        }
    
    def count(self) -> int:
        return UsageStats.query.filter_by(company_id=self.company_id).count()
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[date]:
        """Parse date string"""
        if not date_string:
            return None
        try:
            return datetime.strptime(str(date_string), '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _parse_time(time_string: str) -> Optional[time]:
        """Parse time string"""
        if not time_string:
            return None
        try:
            return datetime.strptime(str(time_string), '%H:%M:%S').time()
        except (ValueError, AttributeError):
            return None