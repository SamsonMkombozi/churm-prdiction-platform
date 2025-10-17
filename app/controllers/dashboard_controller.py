# app/controllers/dashboard_controller.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Import your models
from app.models.company import Company
from app.models.customer import Customer

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Set up logging
logger = logging.getLogger(__name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    """Main dashboard page"""
    try:
        # Get company data
        company = None
        stats = {
            'total_customers': 0,
            'at_risk_customers': 0,
            'prediction_accuracy': 0.0,  # ✅ FIXED: Ensure this key exists
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_tickets': 0,
            'total_payments': 0,
            'high_risk_customers': 0,
            'active_users': 0
        }
        
        if current_user.company_id:
            company = Company.query.get(current_user.company_id)
            if company:
                # Get actual customer count
                total_customers = Customer.query.filter_by(company_id=company.id).count()
                
                # Calculate statistics - using safe methods from Company model
                stats = {
                    'total_customers': total_customers,
                    'at_risk_customers': int(total_customers * 0.15),  # Assume 15% at risk
                    'prediction_accuracy': 85.2,  # Placeholder accuracy
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_tickets': company.get_ticket_count(),
                    'total_payments': company.get_payment_count(),
                    'high_risk_customers': company.get_high_risk_customer_count(),
                    'active_users': company.get_active_user_count()
                }
        
        logger.info(f"Dashboard stats: {stats}")  # Debug log
        
        return render_template('dashboard/index.html', 
                             company=company, 
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"Error in dashboard index: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'error')
        
        # Return with safe default stats to prevent template errors
        safe_stats = {
            'total_customers': 0,
            'at_risk_customers': 0,
            'prediction_accuracy': 0.0,
            'last_updated': 'Never',
            'total_tickets': 0,
            'total_payments': 0,
            'high_risk_customers': 0,
            'active_users': 0
        }
        
        return render_template('dashboard/index.html', 
                             company=None, 
                             stats=safe_stats)

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = {
            'total_customers': 0,
            'at_risk_customers': 0,
            'prediction_accuracy': 0.0,
            'last_updated': datetime.now().isoformat(),
            'total_tickets': 0,
            'total_payments': 0,
            'high_risk_customers': 0,
            'active_users': 0
        }
        
        if current_user.company_id:
            company = Company.query.get(current_user.company_id)
            if company:
                total_customers = Customer.query.filter_by(company_id=company.id).count()
                stats.update({
                    'total_customers': total_customers,
                    'at_risk_customers': int(total_customers * 0.15),
                    'prediction_accuracy': 85.2,
                    'last_updated': datetime.now().isoformat(),
                    'total_tickets': company.get_ticket_count(),
                    'total_payments': company.get_payment_count(),
                    'high_risk_customers': company.get_high_risk_customer_count(),
                    'active_users': company.get_active_user_count()
                })
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in api_stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    return render_template('dashboard/analytics.html')

# Export the blueprint
__all__ = ['dashboard_bp']