"""
Ticket Repository - Data access layer for support tickets
app/repositories/ticket_repository.py
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.extensions import db
from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.company import Company


class TicketRepository:
    """Repository for ticket data operations"""
    
    def __init__(self, company: Company):
        """
        Initialize repository for a specific company
        
        Args:
            company: Company instance
        """
        self.company = company
        self.company_id = company.id
    
    def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID within company"""
        return Ticket.query.filter_by(
            id=ticket_id,
            company_id=self.company_id
        ).first()
    
    def get_by_crm_id(self, crm_ticket_id: str) -> Optional[Ticket]:
        """Get ticket by CRM ID"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            crm_ticket_id=crm_ticket_id
        ).first()
    
    def get_all(self, limit: int = None) -> List[Ticket]:
        """Get all tickets for company"""
        query = Ticket.query.filter_by(company_id=self.company_id)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_status(self, status: str) -> List[Ticket]:
        """Get tickets by status"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            status=status
        ).all()
    
    def get_open_tickets(self) -> List[Ticket]:
        """Get all open tickets"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            status='open'
        ).all()
    
    def get_by_customer(self, customer_id: int) -> List[Ticket]:
        """Get all tickets for a customer"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            customer_id=customer_id
        ).order_by(Ticket.created_at.desc()).all()
    
    def get_by_priority(self, priority: str) -> List[Ticket]:
        """Get tickets by priority"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            priority=priority
        ).all()
    
    def get_recent(self, limit: int = 10) -> List[Ticket]:
        """Get recent tickets"""
        return Ticket.query.filter_by(
            company_id=self.company_id
        ).order_by(Ticket.created_at.desc()).limit(limit).all()
    
    def create(self, ticket_data: Dict) -> Ticket:
        """
        Create new ticket from dictionary
        
        Args:
            ticket_data: Dictionary with ticket data
            
        Returns:
            Created ticket instance
        """
        # Find customer by CRM ID
        customer = None
        if 'customer_id' in ticket_data:
            customer = Customer.find_by_crm_id(
                self.company_id, 
                ticket_data['customer_id']
            )
        
        ticket = Ticket(
            company_id=self.company_id,
            customer_id=customer.id if customer else None,
            crm_ticket_id=ticket_data.get('id'),
            ticket_number=ticket_data.get('ticket_number'),
            title=ticket_data.get('title'),
            description=ticket_data.get('description'),
            category=ticket_data.get('category'),
            priority=ticket_data.get('priority', 'medium'),
            status=ticket_data.get('status', 'open'),
            resolution=ticket_data.get('resolution'),
            resolved_at=self._parse_date(ticket_data.get('resolved_at')),
            assigned_to=ticket_data.get('assigned_to'),
            department=ticket_data.get('department'),
            synced_at=datetime.utcnow()
        )
        
        # Calculate resolution time if resolved
        if ticket.resolved_at:
            ticket.calculate_resolution_time()
        
        db.session.add(ticket)
        
        return ticket
    
    def update(self, ticket: Ticket, ticket_data: Dict) -> Ticket:
        """
        Update existing ticket from dictionary
        
        Args:
            ticket: Ticket instance to update
            ticket_data: Dictionary with updated data
            
        Returns:
            Updated ticket instance
        """
        # Update fields
        ticket.ticket_number = ticket_data.get('ticket_number', ticket.ticket_number)
        ticket.title = ticket_data.get('title', ticket.title)
        ticket.description = ticket_data.get('description', ticket.description)
        ticket.category = ticket_data.get('category', ticket.category)
        ticket.priority = ticket_data.get('priority', ticket.priority)
        ticket.status = ticket_data.get('status', ticket.status)
        ticket.resolution = ticket_data.get('resolution', ticket.resolution)
        ticket.assigned_to = ticket_data.get('assigned_to', ticket.assigned_to)
        ticket.department = ticket_data.get('department', ticket.department)
        
        # Update dates
        if 'resolved_at' in ticket_data:
            ticket.resolved_at = self._parse_date(ticket_data['resolved_at'])
            if ticket.resolved_at:
                ticket.calculate_resolution_time()
        
        ticket.updated_at = datetime.utcnow()
        ticket.synced_at = datetime.utcnow()
        
        return ticket
    
    def create_or_update(self, ticket_data: Dict) -> bool:
        """
        Create new ticket or update existing one
        
        Args:
            ticket_data: Dictionary with ticket data
            
        Returns:
            True if created, False if updated
        """
        crm_id = ticket_data.get('id')
        
        if not crm_id:
            raise ValueError("Ticket data must have 'id' field")
        
        # Check if ticket exists
        ticket = self.get_by_crm_id(crm_id)
        
        if ticket:
            # Update existing
            self.update(ticket, ticket_data)
            return False
        else:
            # Create new
            self.create(ticket_data)
            return True
    
    def delete(self, ticket: Ticket):
        """Delete ticket"""
        db.session.delete(ticket)
    
    def count(self) -> int:
        """Get total ticket count"""
        return Ticket.query.filter_by(company_id=self.company_id).count()
    
    def count_by_status(self, status: str) -> int:
        """Count tickets by status"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            status=status
        ).count()
    
    def count_by_priority(self, priority: str) -> int:
        """Count tickets by priority"""
        return Ticket.query.filter_by(
            company_id=self.company_id,
            priority=priority
        ).count()
    
    def get_paginated(self, page: int = 1, per_page: int = 20,
                     status: str = None, priority: str = None):
        """
        Get paginated tickets with optional filters
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            status: Filter by status
            priority: Filter by priority
            
        Returns:
            Pagination object
        """
        query = Ticket.query.filter_by(company_id=self.company_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        return query.order_by(Ticket.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def get_average_resolution_time(self) -> float:
        """Calculate average resolution time in hours"""
        avg = db.session.query(
            db.func.avg(Ticket.resolution_time_hours)
        ).filter(
            Ticket.company_id == self.company_id,
            Ticket.resolution_time_hours.isnot(None)
        ).scalar()
        
        return avg or 0.0
    
    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None