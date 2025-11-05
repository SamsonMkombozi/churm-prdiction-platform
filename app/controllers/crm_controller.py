"""
Enhanced CRM Controller with Selective Sync Support
app/controllers/crm_controller.py

Handles the selective sync functionality from the dashboard.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.models import Customer, Payment, Ticket
from app.models.company import Company 
from app.services.crm_service import EnhancedCRMService
from app.extensions import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import traceback

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced CRM Dashboard with PostgreSQL support"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get connection information
        crm_service = EnhancedCRMService(company)
        connection_info = crm_service.get_connection_info()
        
        # Get statistics
        stats = {
            'customers': Customer.query.filter_by(company_id=company.id).count(),
            'active_customers': Customer.query.filter_by(company_id=company.id, status='active').count(),
            'tickets': Ticket.query.filter_by(company_id=company.id).count(),
            'open_tickets': Ticket.query.filter_by(company_id=company.id, status='open').count(),
            'payments': Payment.query.filter_by(company_id=company.id).count(),
            'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(company_id=company.id).scalar() or 0,
            'last_sync': company.last_sync,
            'sync_status': company.sync_status or 'never'
        }
        
        # Get recent customers
        recent_customers = Customer.query.filter_by(company_id=company.id)\
            .order_by(desc(Customer.created_at))\
            .limit(10)\
            .all()
        
        # Calculate tenure for customers
        for customer in recent_customers:
            if customer.contract_start_date:
                tenure_delta = datetime.utcnow() - customer.contract_start_date
                customer.tenure_months = max(1, tenure_delta.days // 30)
            else:
                customer.tenure_months = 0
        
        return render_template('crm/enhanced_dashboard.html',
                             company=company,
                             connection_info=connection_info,
                             stats=stats,
                             recent_customers=recent_customers)
    
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Fallback data in case of errors
        connection_info = {
            'postgresql_configured': False,
            'api_configured': False,
            'preferred_method': 'none'
        }
        
        stats = {
            'customers': 0,
            'active_customers': 0,
            'tickets': 0,
            'open_tickets': 0,
            'payments': 0,
            'total_revenue': 0,
            'last_sync': None,
            'sync_status': 'error'
        }
        
        return render_template('crm/enhanced_dashboard.html',
                             company=company,
                             connection_info=connection_info,
                             stats=stats,
                             recent_customers=[],
                             error_message=str(e))

@crm_bp.route('/sync', methods=['POST'])
@login_required
def sync():
    """Enhanced selective sync endpoint"""
    
    company = current_user.company
    if not company:
        return jsonify({'success': False, 'message': 'No company associated with user'}), 400
    
    try:
        # Get sync options from request
        sync_options = request.get_json() or {}
        
        # Default to all enabled if no options provided
        if not sync_options:
            sync_options = {
                'sync_customers': True,
                'sync_payments': True,
                'sync_tickets': True,
                'sync_usage': False
            }
        
        current_app.logger.info(f"Starting selective sync for {company.name}")
        current_app.logger.info(f"Sync options: {sync_options}")
        
        # Check if at least one option is selected
        if not any(sync_options.values()):
            return jsonify({
                'success': False,
                'message': 'Please select at least one data type to sync'
            }), 400
        
        # Check if sync is already in progress
        if company.sync_status == 'in_progress':
            return jsonify({
                'success': False,
                'message': 'Sync already in progress. Please wait for it to complete.'
            }), 409
        
        # Initialize CRM service
        crm_service = EnhancedCRMService(company)
        
        # Check connection
        connection_info = crm_service.get_connection_info()
        
        if connection_info['preferred_method'] == 'none':
            return jsonify({
                'success': False,
                'message': 'No sync method configured. Please configure PostgreSQL or API connection in Company Settings.'
            }), 400
        
        # Start sync
        result = crm_service.sync_data_selective(sync_options)
        
        if result['success']:
            # Build success message with sync details
            stats = result['stats']
            sync_summary = []
            
            if sync_options.get('sync_customers'):
                customer_total = stats['customers']['new'] + stats['customers']['updated']
                if customer_total > 0:
                    sync_summary.append(f"{customer_total} customers")
            
            if sync_options.get('sync_payments'):
                payment_total = stats['payments']['new'] + stats['payments']['updated']
                if payment_total > 0:
                    sync_summary.append(f"{payment_total} payments")
            
            if sync_options.get('sync_tickets'):
                ticket_total = stats['tickets']['new'] + stats['tickets']['updated']
                if ticket_total > 0:
                    sync_summary.append(f"{ticket_total} tickets")
            
            message = f"Successfully synced {', '.join(sync_summary) if sync_summary else 'data'}"
            
            # Add performance info if available
            if 'performance' in result:
                perf = result['performance']
                if perf.get('connection_method') == 'postgresql':
                    message += f" via PostgreSQL in {perf['sync_duration']}s"
                else:
                    message += f" via API"
            
            return jsonify({
                'success': True,
                'message': message,
                'stats': stats,
                'performance': result.get('performance', {})
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'stats': result.get('stats', {})
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"Sync error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Update company status
        company.sync_status = 'failed'
        company.sync_error = str(e)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'message': f"Sync failed: {str(e)}"
        }), 500

@crm_bp.route('/sync/status')
@login_required
def sync_status():
    """Get current sync status"""
    
    company = current_user.company
    if not company:
        return jsonify({'error': 'No company found'}), 404
    
    return jsonify({
        'status': company.sync_status or 'never',
        'last_sync': company.last_sync.isoformat() if company.last_sync else None,
        'error': company.sync_error,
        'total_syncs': company.total_syncs or 0
    })

@crm_bp.route('/connection/test')
@login_required
def test_connection():
    """Test CRM connection"""
    
    company = current_user.company
    if not company:
        return jsonify({'success': False, 'message': 'No company found'}), 404
    
    try:
        crm_service = EnhancedCRMService(company)
        connection_info = crm_service.get_connection_info()
        
        if connection_info['postgresql_configured']:
            # Test PostgreSQL connection
            if crm_service.test_postgresql_connection():
                return jsonify({
                    'success': True,
                    'message': '✅ Direct PostgreSQL connection successful! This will be used for faster sync.',
                    'connection_type': 'postgresql'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '❌ PostgreSQL connection failed. Check your configuration.',
                    'connection_type': 'postgresql'
                })
        
        elif connection_info['api_configured']:
            # Test API connection (you can implement this)
            return jsonify({
                'success': True,
                'message': '✅ API connection available (fallback method).',
                'connection_type': 'api'
            })
        
        else:
            return jsonify({
                'success': False,
                'message': '❌ No connection method configured.',
                'connection_type': 'none'
            })
    
    except Exception as e:
        current_app.logger.error(f"Connection test error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}',
            'connection_type': 'error'
        }), 500

# Keep existing routes for customers, payments, tickets
@crm_bp.route('/customers')
@login_required
def customers():
    """Customer management page"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    # Get customers with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    customers = Customer.query.filter_by(company_id=company.id)\
        .order_by(desc(Customer.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('crm/customers.html', customers=customers)

@crm_bp.route('/payments')
@login_required
def payments():
    """Payment management page"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    # Get payments with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    payments = Payment.query.filter_by(company_id=company.id)\
        .order_by(desc(Payment.transaction_time))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('crm/payments.html', payments=payments)

@crm_bp.route('/tickets')
@login_required
def tickets():
    """Ticket management page"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    # Get tickets with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    tickets = Ticket.query.filter_by(company_id=company.id)\
        .order_by(desc(Ticket.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('crm/tickets.html', tickets=tickets)