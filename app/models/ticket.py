"""
Ticket Model - Support tickets from CRM
"""
from datetime import datetime
from app.extensions import db

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    # CRM Fields
    crm_ticket_id = db.Column(db.String(100), index=True)
    ticket_number = db.Column(db.String(100))
    
    # Ticket Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    
    # Assignment
    assigned_to = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Resolution
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ticket_company_customer', 'company_id', 'customer_id'),
        db.Index('idx_ticket_status', 'company_id', 'status'),
        db.Index('idx_ticket_priority', 'company_id', 'priority'),
        db.Index('idx_ticket_crm', 'company_id', 'crm_ticket_id'),
    )
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number} - {self.title[:50]}>'
    
    def to_dict(self):
        """Convert ticket to dictionary"""
        return {
            'id': self.id,
            'crm_ticket_id': self.crm_ticket_id,
            'ticket_number': self.ticket_number,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'department': self.department,
            'resolution': self.resolution,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def find_by_crm_id(company_id, crm_ticket_id):
        """Find ticket by CRM ID"""
        return Ticket.query.filter_by(
            company_id=company_id,
            crm_ticket_id=crm_ticket_id
        ).first()
    
    @staticmethod
    def get_open_tickets(company_id, limit=None):
        """Get open tickets for a company"""
        query = Ticket.query.filter_by(
            company_id=company_id,
            status='open'
        ).order_by(Ticket.priority.desc(), Ticket.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_high_priority_tickets(company_id, limit=None):
        """Get high-priority tickets"""
        query = Ticket.query.filter_by(
            company_id=company_id,
            priority='high'
        ).order_by(Ticket.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()