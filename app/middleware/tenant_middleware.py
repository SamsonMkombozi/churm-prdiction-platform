"""
Tenant Middleware for Multi-Tenant Isolation
Automatically filters all database queries by company_id
"""
from flask import g, request, abort
from flask_login import current_user
from functools import wraps
from app.extensions import db  # Changed from 'from app import db'

def tenant_middleware():
    """
    Middleware to set current company context before each request
    """
    # Skip for static files and auth routes
    if request.endpoint and (
        request.endpoint.startswith('static') or 
        request.endpoint.startswith('auth.')
    ):
        return
    
    # Set company context if user is logged in
    if current_user.is_authenticated:
        g.company_id = current_user.company_id
        
        # Import here to avoid circular import
        from app.models.company import Company
        g.company = Company.query.get(current_user.company_id)
        
        if not g.company or not g.company.is_active:
            abort(403, description="Company account is inactive")

def get_current_company():
    """Get current company from request context"""
    return getattr(g, 'company', None)

def get_current_company_id():
    """Get current company ID from request context"""
    return getattr(g, 'company_id', None)

def company_required(f):
    """
    Decorator to ensure user belongs to an active company
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'company_id'):
            abort(403, description="No company context found")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to ensure user is admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403, description="Admin access required")
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """
    Decorator to ensure user is manager or admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager():
            abort(403, description="Manager access required")
        return f(*args, **kwargs)
    return decorated_function

class TenantQuery:
    """
    Helper class for tenant-aware queries
    Usage: TenantQuery(Model).filter_by(...).all()
    """
    def __init__(self, model):
        self.model = model
        self.query = model.query
        
        # Automatically add company filter if company_id exists
        if hasattr(model, 'company_id') and hasattr(g, 'company_id'):
            self.query = self.query.filter_by(company_id=g.company_id)
    
    def filter_by(self, **kwargs):
        self.query = self.query.filter_by(**kwargs)
        return self
    
    def filter(self, *args):
        self.query = self.query.filter(*args)
        return self
    
    def order_by(self, *args):
        self.query = self.query.order_by(*args)
        return self
    
    def limit(self, limit):
        self.query = self.query.limit(limit)
        return self
    
    def offset(self, offset):
        self.query = self.query.offset(offset)
        return self
    
    def all(self):
        return self.query.all()
    
    def first(self):
        return self.query.first()
    
    def count(self):
        return self.query.count()
    
    def paginate(self, page=1, per_page=20):
        return self.query.paginate(page=page, per_page=per_page, error_out=False)

def company_scope(model):
    """
    Factory function for tenant-aware queries
    Usage: company_scope(Customer).filter_by(status='active').all()
    """
    return TenantQuery(model)