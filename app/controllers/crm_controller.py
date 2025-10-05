"""
CRM Controller - CRM Data Management
app/controllers/crm_controller.py
"""
from flask import Blueprint, render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.payment import Payment
from app.middleware.tenant_middleware import manager_required
from app.services.crm_service import CRMService
from app.repositories.customer_repository import CustomerRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.payment_repository import PaymentRepository
import logging

logger = logging.getLogger(__name__)

# Create blueprint
crm_bp = Blueprint('crm', __name__)


@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """
    CRM Dashboard - Shows sync status and recent data
    """
    company = current_user.company
    
    # Get repositories
    customer_repo = CustomerRepository(company)
    ticket_repo = TicketRepository(company)
    payment_repo = PaymentRepository(company)
    
# Get statistics
    stats = {
        'total_customers': customer_repo.count(),
        'customers': customer_repo.count(),
        'active_customers': customer_repo.count_by_status('active'),
        'total_tickets': ticket_repo.count(),
        'tickets': ticket_repo.count(),
        'open_tickets': ticket_repo.count_by_status('open'),
        'total_payments': payment_repo.count(),
        'payments': payment_repo.count(),
        'total_revenue': payment_repo.get_total_revenue(),
        'active_users': current_user.company.get_active_user_count(),
        'last_sync': company.last_sync_at,
        'sync_status': company.sync_status
    }
    
    # Get recent data
    recent_customers = customer_repo.get_recent(limit=5)
    open_tickets = ticket_repo.get_open_tickets()[:5]
    recent_payments = payment_repo.get_recent(limit=10)
    
    return render_template(
        'crm/dashboard.html',
        company=company,
        stats=stats,
        recent_customers=recent_customers,
        open_tickets=open_tickets,
        recent_payments=recent_payments
    )


@crm_bp.route('/customers')
@login_required
def customers():
    """
    List all customers
    """
    company = current_user.company
    repo = CustomerRepository(company)
    
    # Get pagination parameters
    from flask import request
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    risk = request.args.get('risk')
    
    # Get paginated customers
    pagination = repo.get_paginated(page=page, per_page=20, status=status, risk=risk)
    
    return render_template(
        'crm/customers.html',
        company=company,
        customers=pagination.items,
        pagination=pagination,
        current_status=status,
        current_risk=risk
    )


@crm_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """
    Customer detail page
    """
    company = current_user.company
    customer_repo = CustomerRepository(company)
    ticket_repo = TicketRepository(company)
    payment_repo = PaymentRepository(company)
    
    customer = customer_repo.get_by_id(customer_id)
    
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('crm.customers'))
    
    # Get customer's tickets and payments
    tickets = ticket_repo.get_by_customer(customer_id)
    payments = payment_repo.get_by_customer(customer_id)
    
    return render_template(
        'crm/customer_detail.html',
        company=company,
        customer=customer,
        tickets=tickets,
        payments=payments
    )


@crm_bp.route('/tickets')
@login_required
def tickets():
    """
    List all support tickets
    """
    company = current_user.company
    repo = TicketRepository(company)
    
    # Get pagination parameters
    from flask import request
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    # Get paginated tickets
    pagination = repo.get_paginated(page=page, per_page=20, status=status, priority=priority)
    
    return render_template(
        'crm/tickets.html',
        company=company,
        tickets=pagination.items,
        pagination=pagination,
        current_status=status,
        current_priority=priority
    )


@crm_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    """
    Ticket detail page
    """
    company = current_user.company
    repo = TicketRepository(company)
    
    ticket = repo.get_by_id(ticket_id)
    
    if not ticket:
        flash('Ticket not found', 'danger')
        return redirect(url_for('crm.tickets'))
    
    return render_template(
        'crm/ticket_detail.html',
        company=company,
        ticket=ticket
    )


@crm_bp.route('/payments')
@login_required
def payments():
    """
    List all payment transactions
    """
    company = current_user.company
    repo = PaymentRepository(company)
    
    # Get pagination parameters
    from flask import request
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    # Get paginated payments
    pagination = repo.get_paginated(page=page, per_page=20, status=status)
    
    return render_template(
        'crm/payments.html',
        company=company,
        payments=pagination.items,
        pagination=pagination,
        current_status=status
    )


@crm_bp.route('/sync', methods=['POST'])
@login_required
@manager_required
def sync():
    """
    Trigger CRM data synchronization
    """
    try:
        company = current_user.company
        
        # Check if sync is already in progress
        if company.sync_status == 'in_progress':
            return jsonify({
                'success': False,
                'message': 'Sync already in progress'
            }), 400
        
        # Validate CRM configuration
        if not company.crm_api_url:
            return jsonify({
                'success': False,
                'message': 'CRM API URL not configured. Please update company settings.'
            }), 400
        
        # Initialize CRM service
        try:
            crm_service = CRMService(company)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        # Test connection first
        success, message = crm_service.test_connection()
        if not success:
            return jsonify({
                'success': False,
                'message': f'CRM connection failed: {message}'
            }), 500
        
        # Run sync
        logger.info(f"Starting manual sync for company {company.id}")
        results = crm_service.sync_data()
        
        if results.get('status') == 'completed':
            return jsonify({
                'success': True,
                'message': results.get('summary', {}).get('message', 'Sync completed'),
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': results.get('message', 'Sync failed'),
                'results': results
            }), 500
        
    except Exception as e:
        logger.error(f"Error during manual sync: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@crm_bp.route('/sync/status')
@login_required
def sync_status():
    """
    Get current sync status (for polling)
    """
    company = current_user.company
    
    return jsonify({
        'status': company.sync_status,
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'total_syncs': company.total_syncs,
        'error': company.sync_error
    })


@crm_bp.route('/test-connection', methods=['POST'])
@login_required
@manager_required
def test_connection():
    """
    Test CRM API connection
    """
    try:
        company = current_user.company
        
        if not company.crm_api_url:
            return jsonify({
                'success': False,
                'message': 'CRM API URL not configured'
            }), 400
        
        try:
            crm_service = CRMService(company)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        success, message = crm_service.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@crm_bp.route('/statistics')
@login_required
def statistics():
    """
    Get CRM statistics as JSON
    """
    company = current_user.company
    
    customer_repo = CustomerRepository(company)
    ticket_repo = TicketRepository(company)
    payment_repo = PaymentRepository(company)
    
    stats = {
        'customers': {
            'total': customer_repo.count(),
            'active': customer_repo.count_by_status('active'),
            'inactive': customer_repo.count_by_status('inactive'),
            'high_risk': customer_repo.count_by_risk('high'),
            'medium_risk': customer_repo.count_by_risk('medium'),
            'low_risk': customer_repo.count_by_risk('low')
        },
        'tickets': {
            'total': ticket_repo.count(),
            'open': ticket_repo.count_by_status('open'),
            'closed': ticket_repo.count_by_status('closed'),
            'in_progress': ticket_repo.count_by_status('in_progress'),
            'avg_resolution_time': ticket_repo.get_average_resolution_time()
        },
        'payments': {
            'total': payment_repo.count(),
            'completed': payment_repo.count_by_status('completed'),
            'pending': payment_repo.count_by_status('pending'),
            'total_revenue': payment_repo.get_total_revenue()
        },
        'sync': {
            'status': company.sync_status,
            'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
            'total_syncs': company.total_syncs
        }
    }
    
    return jsonify(stats)