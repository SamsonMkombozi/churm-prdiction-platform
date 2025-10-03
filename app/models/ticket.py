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
    ticket_number = db.Column(db.String(50))
    
    # Ticket Information
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # technical, billing, service, complaint
    priority = db.Column(db.String(20))  # low, medium, high, urgent
    status = db.Column(db.String(50))  # open, in_progress, resolved, closed
    
    # Resolution
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    resolution_time_hours = db.Column(db.Float)  # Time to resolve in hours
    
    # Assignment
    assigned_to = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ticket_company_customer', 'company_id', 'customer_id'),
        db.Index('idx_ticket_status', 'company_id', 'status'),
        db.Index('idx_ticket_crm', 'company_id', 'crm_ticket_id'),
    )
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number} - {self.title}>'
    
    def calculate_resolution_time(self):
        """Calculate time taken to resolve ticket"""
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            self.resolution_time_hours = delta.total_seconds() / 3600
        return self.resolution_time_hours
    
    def to_dict(self):
        """Convert ticket to dictionary"""
        return {
            'id': self.id,
            'crm_ticket_id': self.crm_ticket_id,
            'ticket_number': self.ticket_number,
            'title': self.title,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_time_hours': self.resolution_time_hours,
        }
    
    @staticmethod
    def find_by_crm_id(company_id, crm_ticket_id):
        """Find ticket by CRM ID"""
        return Ticket.query.filter_by(
            company_id=company_id,
            crm_ticket_id=crm_ticket_id
        ).first()
    
    @staticmethod
    def get_open_tickets(company_id):
        """Get all open tickets for a company"""
        return Ticket.query.filter_by(
            company_id=company_id,
            status='open'
        ).all()