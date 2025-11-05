"""
ENHANCED CRM Controller with Selective Sync
app/controllers/crm_controller.py

Features:
- Selective sync options (choose what to sync)
- Smart update detection (skip unchanged data)
- Better error reporting
"""
from flask import Blueprint, render_template, jsonify, flash, redirect, url_for, request
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
    """CRM Dashboard - Shows sync status and recent data"""
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


@crm_bp.route('/sync', methods=['POST'])
@login_required
@manager_required
def sync():
    """
    ✅ ENHANCED: Selective sync with smart update detection
    
    Request body (JSON):
    {
        "sync_customers": true,
        "sync_payments": true,
        "sync_tickets": true,
        "sync_usage": false
    }
    
    If no options provided, syncs all data types.
    """
    try:
        company = current_user.company
        
        # Check if CRM is configured
        if not company.crm_api_url:
            return jsonify({
                'success': False,
                'message': 'CRM API URL not configured. Please configure in Company Settings.',
                'fix_instructions': 'Go to Company Settings and add your CRM API URL'
            }), 400
        
        # Check if sync is already in progress
        if company.sync_status == 'in_progress':
            return jsonify({
                'success': False,
                'message': 'Sync already in progress. Please wait for it to complete.',
                'current_status': company.sync_status
            }), 400
        
        # Get sync options from request
        try:
            sync_options = request.get_json() or {}
        except:
            sync_options = {}
        
        # Convert sync options to expected format
        formatted_options = {
            'customers': sync_options.get('sync_customers', True),
            'payments': sync_options.get('sync_payments', True),
            'tickets': sync_options.get('sync_tickets', True),
            'usage': sync_options.get('sync_usage', True)
        }
        
        logger.info(f"🔄 Selective sync requested with options: {formatted_options}")
        
        # Initialize CRM service
        try:
            crm_service = CRMService(company)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f"Failed to initialize CRM service: {str(e)}",
                'fix_instructions': 'Check your CRM configuration in Company Settings'
            }), 400
        
        # Test connection first
        logger.info(f"🔍 Testing CRM connection for company {company.id}")
        connection_result = crm_service.test_connection()
        
        if not connection_result.get('success'):
            error_message = connection_result.get('message', 'Unknown connection error')
            debug_info = connection_result.get('debug_info', {})
            
            logger.error(f"❌ CRM connection failed: {error_message}")
            
            return jsonify({
                'success': False,
                'message': f"Cannot connect to CRM: {error_message}",
                'debug_info': debug_info,
                'fix_instructions': [
                    'Check if the CRM API URL is correct',
                    'Verify the CRM server is running and accessible',
                    'Confirm the table names are correct'
                ]
            }), 400
        
        # Perform selective sync
        logger.info(f"🚀 Starting selective sync for company {company.id}")
        results = crm_service.sync_selective_data(formatted_options)
        
        if results['success']:
            # Build success message with details
            message_parts = []
            
            for data_type in ['customers', 'payments', 'tickets', 'usage']:
                data = results.get(data_type, {})
                if data.get('synced', False):
                    new = data.get('new', 0)
                    updated = data.get('updated', 0)
                    if new > 0 or updated > 0:
                        message_parts.append(f"{data_type}: {new} new, {updated} updated")
                else:
                    message_parts.append(f"{data_type}: no changes")
            
            message = "Successfully synced! " + "; ".join(message_parts)
            
            return jsonify({
                'success': True,
                'message': message,
                'results': results,
                'summary': {
                    'sync_time': results.get('sync_time', 0),
                    'customers': results.get('customers', {}),
                    'payments': results.get('payments', {}),
                    'tickets': results.get('tickets', {}),
                    'usage': results.get('usage', {})
                }
            })
        else:
            # Handle sync failure
            errors = results.get('errors', ['Unknown error'])
            error_msg = '; '.join(errors[:3])
            
            return jsonify({
                'success': False,
                'message': f'Sync failed: {error_msg}',
                'errors': errors,
                'results': results
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error during sync: {str(e)}", exc_info=True)
        
        # Reset sync status on error
        try:
            company.sync_status = 'failed'
            company.sync_error = str(e)
            db.session.commit()
        except:
            pass
        
        return jsonify({
            'success': False,
            'message': f'Sync error: {str(e)}',
            'error_type': type(e).__name__
        }), 500


@crm_bp.route('/test-connection', methods=['POST'])
@login_required
@manager_required
def test_connection():
    """Test CRM API connection with detailed debugging"""
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
        
        result = crm_service.test_connection()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500


@crm_bp.route('/sync/status')
@login_required
def sync_status():
    """Get current sync status (for polling)"""
    company = current_user.company
    
    return jsonify({
        'status': company.sync_status,
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'total_syncs': company.total_syncs,
        'error': company.sync_error
    })


# Keep all other existing routes (customers, tickets, payments, etc.)
# ... (your existing customer, ticket, payment routes remain unchanged)

@crm_bp.route('/customers')
@login_required
def customers():
    """List all customers with statistics"""
    company = current_user.company
    customer_repo = CustomerRepository(company)
    ticket_repo = TicketRepository(company)
    payment_repo = PaymentRepository(company)

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    risk = request.args.get('risk')

    pagination = customer_repo.get_paginated(page=page, per_page=20, status=status, risk=risk)

    stats = {
        'customers': customer_repo.count(),
        'active_customers': customer_repo.count_by_status('active'),
        'tickets': ticket_repo.count(),
        'open_tickets': ticket_repo.count_by_status('open'),
        'payments': payment_repo.count(),
        'total_revenue': payment_repo.get_total_revenue(),
        'last_sync': company.last_sync_at,
        'sync_status': company.sync_status
    }

    recent_customers = customer_repo.get_recent(limit=5)

    return render_template(
        'crm/customers.html',
        company=company,
        stats=stats,
        recent_customers=recent_customers,
        customers=pagination.items,
        pagination=pagination,
        current_status=status,
        current_risk=risk
    )


@crm_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Customer detail page"""
    company = current_user.company
    customer_repo = CustomerRepository(company)
    ticket_repo = TicketRepository(company)
    payment_repo = PaymentRepository(company)
    
    customer = customer_repo.get_by_id(customer_id)
    
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('crm.customers'))
    
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
    """List all support tickets"""
    company = current_user.company
    repo = TicketRepository(company)
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
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
    """Ticket detail page"""
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
    """List all payment transactions"""
    company = current_user.company
    repo = PaymentRepository(company)
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    pagination = repo.get_paginated(page=page, per_page=20, status=status)
    
    return render_template(
        'crm/payments.html',
        company=company,
        payments=pagination.items,
        pagination=pagination,
        current_status=status
    )


@crm_bp.route('/statistics')
@login_required
def statistics():
    """Get CRM statistics as JSON"""
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