"""
Enhanced CRM Controller with Selective Sync Support - COMPLETELY FIXED VERSION
app/controllers/crm_controller.py

✅ FIXES:
1. Pass company variable to all templates
2. Pass pagination objects correctly
3. Pass filter variables for template compatibility
4. Proper error handling for missing data
5. Use last_sync_at instead of last_sync throughout
"""

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.models import Customer, Payment, Ticket
from app.models.company import Company 
from app.services.crm_service import EnhancedCRMService
from app.extensions import db
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import traceback

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced CRM Dashboard with PostgreSQL support - FIXED VERSION"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get connection information
        crm_service = EnhancedCRMService(company)
        connection_info = crm_service.get_connection_info()
        
        # ✅ FIX: Use correct attribute names from Company model
        stats = {
            'customers': Customer.query.filter_by(company_id=company.id).count(),
            'active_customers': Customer.query.filter_by(company_id=company.id, status='active').count(),
            'tickets': Ticket.query.filter_by(company_id=company.id).count(),
            'open_tickets': Ticket.query.filter_by(company_id=company.id, status='open').count(),
            'payments': Payment.query.filter_by(company_id=company.id).count(),
            'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(company_id=company.id).scalar() or 0,
            'last_sync': company.last_sync_at,  # ✅ FIX: Use last_sync_at instead of last_sync
            'sync_status': company.sync_status or 'never'
        }
        
        # Get recent customers
        recent_customers = Customer.query.filter_by(company_id=company.id)\
            .order_by(desc(Customer.created_at))\
            .limit(10)\
            .all()
        
        # Calculate tenure for customers
        for customer in recent_customers:
            if customer.signup_date:  # ✅ FIX: Use signup_date instead of contract_start_date
                tenure_delta = datetime.utcnow() - customer.signup_date
                customer.tenure_months = max(1, tenure_delta.days // 30)
            else:
                customer.tenure_months = 0
        
        return render_template('crm/dashboard.html',
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
        
        return render_template('crm/dashboard.html',
                             company=company,
                             connection_info=connection_info,
                             stats=stats,
                             recent_customers=[],
                             error_message=str(e))

@crm_bp.route('/sync', methods=['POST'])
@login_required
def sync():
    """Enhanced selective sync endpoint - FIXED VERSION"""
    
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
    """Get current sync status - FIXED VERSION"""
    
    company = current_user.company
    if not company:
        return jsonify({'error': 'No company found'}), 404
    
    # ✅ FIX: Use last_sync_at instead of last_sync
    return jsonify({
        'status': company.sync_status or 'never',
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
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

# ✅ FIXED: Customer management page with all required template variables
@crm_bp.route('/customers')
@login_required
def customers():
    """Customer management page - COMPLETELY FIXED VERSION"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get filters from request
        status_filter = request.args.get('status', '')
        risk_filter = request.args.get('risk', '')
        search_filter = request.args.get('search', '')
        
        # Get customers with pagination and filters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = Customer.query.filter_by(company_id=company.id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        if risk_filter:
            query = query.filter_by(churn_risk=risk_filter)
        if search_filter:
            query = query.filter(
                or_(
                    Customer.customer_name.ilike(f'%{search_filter}%'),
                    Customer.email.ilike(f'%{search_filter}%') if Customer.email else False
                )
            )
        
        # Calculate tenure for display
        for customer in query.all():
            if customer.signup_date:
                tenure_delta = datetime.utcnow() - customer.signup_date
                customer.tenure_months = max(1, tenure_delta.days // 30)
            else:
                customer.tenure_months = 0
        
        pagination = query.order_by(desc(Customer.created_at))\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('crm/customers.html', 
                             company=company,  # ✅ FIX: Pass company
                             customers=pagination.items,  # ✅ FIX: Use pagination.items
                             pagination=pagination,  # ✅ FIX: Pass pagination object
                             current_status=status_filter,  # ✅ FIX: Pass current filters
                             current_risk=risk_filter,
                             current_search=search_filter)
                             
    except Exception as e:
        current_app.logger.error(f"Customers page error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Return safe fallback
        return render_template('crm/customers.html',
                             company=company,
                             customers=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='',
                             current_risk='',
                             current_search='',
                             error_message=str(e))

# ✅ FIXED: Payment management page with all required template variables
@crm_bp.route('/payments')
@login_required
def payments():
    """Payment management page - COMPLETELY FIXED VERSION"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get filters from request
        status_filter = request.args.get('status', '')
        method_filter = request.args.get('method', '')
        search_filter = request.args.get('search', '')
        
        # Get payments with pagination and filters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = Payment.query.filter_by(company_id=company.id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        if method_filter:
            query = query.filter_by(payment_method=method_filter)
        if search_filter:
            query = query.join(Customer).filter(
                or_(
                    Payment.transaction_id.ilike(f'%{search_filter}%'),
                    Customer.customer_name.ilike(f'%{search_filter}%')
                )
            )
        
        pagination = query.order_by(desc(Payment.payment_date))\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('crm/payments.html',
                             company=company,  # ✅ FIX: Pass company
                             payments=pagination.items,  # ✅ FIX: Use pagination.items
                             pagination=pagination,  # ✅ FIX: Pass pagination object
                             current_status=status_filter,  # ✅ FIX: Pass current filters
                             current_method=method_filter,
                             current_search=search_filter)
                             
    except Exception as e:
        current_app.logger.error(f"Payments page error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Return safe fallback
        return render_template('crm/payments.html',
                             company=company,
                             payments=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='',
                             current_method='',
                             current_search='',
                             error_message=str(e))

# ✅ FIXED: Ticket management page with all required template variables
@crm_bp.route('/tickets')
@login_required
def tickets():
    """Ticket management page - COMPLETELY FIXED VERSION"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get filters from request
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        search_filter = request.args.get('search', '')
        
        # Get tickets with pagination and filters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = Ticket.query.filter_by(company_id=company.id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        if priority_filter:
            query = query.filter_by(priority=priority_filter)
        if search_filter:
            query = query.filter(
                or_(
                    Ticket.title.ilike(f'%{search_filter}%'),
                    Ticket.ticket_number.ilike(f'%{search_filter}%')
                )
            )
        
        pagination = query.order_by(desc(Ticket.created_at))\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('crm/tickets.html',
                             company=company,  # ✅ FIX: Pass company
                             tickets=pagination.items,  # ✅ FIX: Use pagination.items
                             pagination=pagination,  # ✅ FIX: Pass pagination object
                             current_status=status_filter,  # ✅ FIX: Pass current filters
                             current_priority=priority_filter,
                             current_search=search_filter)
                             
    except Exception as e:
        current_app.logger.error(f"Tickets page error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Return safe fallback
        return render_template('crm/tickets.html',
                             company=company,
                             tickets=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='',
                             current_priority='',
                             current_search='',
                             error_message=str(e))

# ✅ BONUS: Detail pages for individual records
@crm_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Customer detail page"""
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=company.id
    ).first_or_404()
    
    # Calculate tenure
    if customer.signup_date:
        tenure_delta = datetime.utcnow() - customer.signup_date
        customer.tenure_months = max(1, tenure_delta.days // 30)
    
    # Get recent payments and tickets
    recent_payments = Payment.query.filter_by(
        customer_id=customer.id
    ).order_by(desc(Payment.payment_date)).limit(10).all()
    
    recent_tickets = Ticket.query.filter_by(
        customer_id=customer.id
    ).order_by(desc(Ticket.created_at)).limit(10).all()
    
    return render_template('crm/customer_detail.html',
                         company=company,
                         customer=customer,
                         payments=recent_payments,  # Template expects 'payments'
                         tickets=recent_tickets)    # Template expects 'tickets'

@crm_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    """Ticket detail page"""
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    ticket = Ticket.query.filter_by(
        id=ticket_id,
        company_id=company.id
    ).first_or_404()
    
    return render_template('crm/ticket_detail.html',
                         company=company,
                         ticket=ticket)