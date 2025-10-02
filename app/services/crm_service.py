"""
CRM Service - Stub for now
TODO: Implement actual CRM integration
"""
from flask import current_app

class CRMService:
    """Stub CRM Service"""
    
    def __init__(self, company):
        self.company = company
    
    def sync_data(self):
        """Stub sync method"""
        current_app.logger.info(f"CRM sync called for company {self.company.id}")
        return {
            'status': 'pending',
            'message': 'CRM service not yet implemented'
        }
    
    def test_connection(self):
        """Test CRM API connection"""
        return {
            'success': False,
            'message': 'CRM service not yet implemented'
        }
