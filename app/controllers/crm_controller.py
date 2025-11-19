"""
Enhanced CRM Controller with Integrated Payment-Based Predictions
app/controllers/crm_controller.py

✅ ENHANCED FEATURES:
1. Integrated payment-based churn prediction from n.py
2. Multi-table customer mapping (crm_customers, crm_tickets, nav_mpesa_transactions, spl_statistics)
3. Real-time risk assessment and prediction generation
4. Enhanced sync performance with prediction analytics
"""

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.models import Customer, Payment, Ticket
from app.models.company import Company 
from app.services.crm_service import EnhancedCRMServiceWithPredictions
from app.extensions import db
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import traceback


crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced CRM Dashboard with integrated payment-based predictions"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get enhanced connection information with prediction capabilities
        crm_service = EnhancedCRMServiceWithPredictions(company)
        connection_info = crm_service.get_connection_info()
        
        # ✅ ENHANCED: Include prediction statistics
        stats = {
            'customers': Customer.query.filter_by(company_id=company.id).count(),
            'active_customers': Customer.query.filter_by(company_id=company.id, status='active').count(),
            'tickets': Ticket.query.filter_by(company_id=company.id).count(),
            'open_tickets': Ticket.query.filter_by(company_id=company.id, status='open').count(),
            'payments': Payment.query.filter_by(company_id=company.id).count(),
            'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(company_id=company.id).scalar() or 0,
            'last_sync': company.last_sync_at,
            'sync_status': company.sync_status or 'never',
            
            # ✅ NEW: Prediction statistics
            'high_risk_customers': Customer.query.filter_by(company_id=company.id, churn_risk='high').count(),
            'medium_risk_customers': Customer.query.filter_by(company_id=company.id, churn_risk='medium').count(),
            'low_risk_customers': Customer.query.filter_by(company_id=company.id, churn_risk='low').count(),
            'customers_with_predictions': Customer.query.filter(
                Customer.company_id == company.id,
                Customer.churn_probability.isnot(None)
            ).count(),
            'avg_churn_probability': db.session.query(func.avg(Customer.churn_probability))\
                .filter_by(company_id=company.id)\
                .filter(Customer.churn_probability.isnot(None))\
                .scalar() or 0
        }
        
        # Get recent customers with enhanced payment-based metrics
        recent_customers = Customer.query.filter_by(company_id=company.id)\
            .order_by(desc(Customer.created_at))\
            .limit(10)\
            .all()
        
        # Calculate enhanced tenure and payment metrics for display
        for customer in recent_customers:
            if customer.signup_date:
                tenure_delta = datetime.utcnow() - customer.signup_date
                customer.tenure_months = max(1, tenure_delta.days // 30)
            else:
                customer.tenure_months = 0
            
            # Add payment behavior indicator (from n.py logic)
            if hasattr(customer, 'last_payment_date') and customer.last_payment_date:
                days_since_payment = (datetime.utcnow() - customer.last_payment_date).days
                if days_since_payment >= 90:
                    customer.payment_status = 'high_risk'
                elif days_since_payment >= 60:
                    customer.payment_status = 'medium_risk'
                else:
                    customer.payment_status = 'good'
            else:
                customer.payment_status = 'no_data'
        
        return render_template('crm/dashboard.html',
                             company=company,
                             connection_info=connection_info,
                             stats=stats,
                             recent_customers=recent_customers)
    
    except Exception as e:
        current_app.logger.error(f"Enhanced dashboard error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Fallback data
        connection_info = {
            'postgresql_configured': False,
            'api_configured': False,
            'preferred_method': 'none',
            'prediction_enabled': False
        }
        
        stats = {
            'customers': 0, 'active_customers': 0, 'tickets': 0, 'open_tickets': 0,
            'payments': 0, 'total_revenue': 0, 'last_sync': None, 'sync_status': 'error',
            'high_risk_customers': 0, 'medium_risk_customers': 0, 'low_risk_customers': 0,
            'customers_with_predictions': 0, 'avg_churn_probability': 0
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
    """Enhanced selective sync with integrated payment-based predictions"""
    
    company = current_user.company
    if not company:
        return jsonify({'success': False, 'message': 'No company associated with user'}), 400
    
    try:
        # Get enhanced sync options with prediction generation
        sync_options = request.get_json() or {}
        
        # ✅ ENHANCED: Default to all enabled including predictions
        if not sync_options:
            sync_options = {
                'sync_customers': True,
                'sync_payments': True,
                'sync_tickets': True,
                'sync_usage': True,
                'generate_predictions': True  # NEW: Enable predictions by default
            }
        
        # Ensure prediction generation is included
        if 'generate_predictions' not in sync_options:
            sync_options['generate_predictions'] = True
        
        current_app.logger.info(f"Starting enhanced sync with predictions for {company.name}")
        current_app.logger.info(f"Enhanced sync options: {sync_options}")
        
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
        
        # Initialize enhanced CRM service with predictions
        crm_service = EnhancedCRMServiceWithPredictions(company)
        
        # Check connection
        connection_info = crm_service.get_connection_info()
        
        if connection_info['preferred_method'] == 'none':
            return jsonify({
                'success': False,
                'message': 'No sync method configured. Please configure PostgreSQL or API connection in Company Settings.'
            }), 400
        
        # Start enhanced sync with predictions
        result = crm_service.sync_data_selective(sync_options)
        
        if result['success']:
            # Build enhanced success message with prediction details
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
            
            if sync_options.get('sync_usage'):
                usage_total = stats['usage_stats']['new'] + stats['usage_stats']['updated']
                if usage_total > 0:
                    sync_summary.append(f"{usage_total} usage records")
            
            # ✅ ENHANCED: Include prediction summary
            if sync_options.get('generate_predictions') and 'predictions' in stats:
                pred_total = stats['predictions']['generated']
                if pred_total > 0:
                    sync_summary.append(f"{pred_total} predictions")
            
            message = f"Enhanced sync completed: {', '.join(sync_summary) if sync_summary else 'data'}"
            
            # Add performance info with prediction details
            if 'performance' in result:
                perf = result['performance']
                message += f" via {perf.get('connection_method', 'PostgreSQL')} in {perf['sync_duration']}s"
                
                if perf.get('predictions_generated', 0) > 0:
                    message += f" with {perf['predictions_generated']} churn predictions"
            
            # ✅ ENHANCED: Include prediction summary in response
            response_data = {
                'success': True,
                'message': message,
                'stats': stats,
                'performance': result.get('performance', {})
            }
            
            if 'prediction_summary' in result:
                response_data['prediction_summary'] = result['prediction_summary']
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'stats': result.get('stats', {})
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"Enhanced sync error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Update company status
        company.sync_status = 'failed'
        company.sync_error = str(e)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'message': f"Enhanced sync failed: {str(e)}"
        }), 500

@crm_bp.route('/sync/status')
@login_required
def sync_status():
    """Get enhanced sync status with prediction info"""
    
    company = current_user.company
    if not company:
        return jsonify({'error': 'No company found'}), 404
    
    # Get prediction statistics
    try:
        prediction_stats = {
            'total_predictions': Customer.query.filter(
                Customer.company_id == company.id,
                Customer.churn_probability.isnot(None)
            ).count(),
            'high_risk': Customer.query.filter_by(company_id=company.id, churn_risk='high').count(),
            'medium_risk': Customer.query.filter_by(company_id=company.id, churn_risk='medium').count(),
            'low_risk': Customer.query.filter_by(company_id=company.id, churn_risk='low').count(),
            'last_prediction': db.session.query(func.max(Customer.last_prediction_date))\
                .filter_by(company_id=company.id).scalar()
        }
    except Exception as e:
        current_app.logger.warning(f"Error getting prediction stats: {e}")
        prediction_stats = {
            'total_predictions': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0, 'last_prediction': None
        }
    
    return jsonify({
        'status': company.sync_status or 'never',
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'error': company.sync_error,
        'total_syncs': company.total_syncs or 0,
        'prediction_stats': prediction_stats  # ✅ NEW: Include prediction statistics
    })

@crm_bp.route('/connection/test')
@login_required
def test_connection():
    """Test enhanced CRM connection with prediction capabilities"""
    
    company = current_user.company
    if not company:
        return jsonify({'success': False, 'message': 'No company found'}), 404
    
    try:
        crm_service = EnhancedCRMServiceWithPredictions(company)
        test_result = crm_service.test_postgresql_connection()
        
        return jsonify(test_result)
    
    except Exception as e:
        current_app.logger.error(f"Enhanced connection test error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Enhanced connection test failed: {str(e)}',
            'connection_type': 'error'
        }), 500

# ✅ NEW: Prediction-specific routes

@crm_bp.route('/predictions/summary')
@login_required
def prediction_summary():
    """Get comprehensive prediction summary"""
    
    company = current_user.company
    if not company:
        return jsonify({'error': 'No company found'}), 404
    
    try:
        # Get prediction distribution
        prediction_stats = {
            'total_customers': Customer.query.filter_by(company_id=company.id).count(),
            'customers_with_predictions': Customer.query.filter(
                Customer.company_id == company.id,
                Customer.churn_probability.isnot(None)
            ).count(),
            'high_risk': Customer.query.filter_by(company_id=company.id, churn_risk='high').count(),
            'medium_risk': Customer.query.filter_by(company_id=company.id, churn_risk='medium').count(),
            'low_risk': Customer.query.filter_by(company_id=company.id, churn_risk='low').count(),
            'avg_churn_probability': float(db.session.query(func.avg(Customer.churn_probability))\
                .filter_by(company_id=company.id)\
                .filter(Customer.churn_probability.isnot(None))\
                .scalar() or 0),
            'last_prediction_date': db.session.query(func.max(Customer.last_prediction_date))\
                .filter_by(company_id=company.id).scalar()
        }
        
        # Get high-risk customers for immediate action
        high_risk_customers = Customer.query.filter_by(
            company_id=company.id,
            churn_risk='high'
        ).order_by(desc(Customer.churn_probability)).limit(10).all()
        
        high_risk_list = []
        for customer in high_risk_customers:
            high_risk_list.append({
                'id': customer.id,
                'name': customer.customer_name,
                'probability': customer.churn_probability,
                'phone': customer.phone,
                'last_payment_date': customer.last_payment_date.isoformat() if hasattr(customer, 'last_payment_date') and customer.last_payment_date else None
            })
        
        return jsonify({
            'success': True,
            'prediction_stats': prediction_stats,
            'high_risk_customers': high_risk_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Prediction summary error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get prediction summary: {str(e)}'
        }), 500

@crm_bp.route('/predictions/regenerate', methods=['POST'])
@login_required
def regenerate_predictions():
    """Regenerate predictions for all customers"""
    
    company = current_user.company
    if not company:
        return jsonify({'success': False, 'message': 'No company found'}), 400
    
    try:
        # Start prediction generation only
        sync_options = {
            'sync_customers': False,
            'sync_payments': False,
            'sync_tickets': False,
            'sync_usage': False,
            'generate_predictions': True
        }
        
        crm_service = EnhancedCRMServiceWithPredictions(company)
        result = crm_service.sync_data_selective(sync_options)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Prediction regeneration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to regenerate predictions: {str(e)}'
        }), 500

# ✅ PRESERVED: All existing customer, payment, and ticket management routes with enhanced features

@crm_bp.route('/customers')
@login_required
def customers():
    """Enhanced customer management page with prediction filtering"""
    
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get filters from request
        status_filter = request.args.get('status', '')
        risk_filter = request.args.get('risk', '')
        search_filter = request.args.get('search', '')
        
        # ✅ NEW: Payment behavior filter (from n.py logic)
        payment_filter = request.args.get('payment_behavior', '')
        
        # Get customers with pagination and enhanced filters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = Customer.query.filter_by(company_id=company.id)
        
        # Apply existing filters
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
        
        # ✅ NEW: Payment behavior filter
        if payment_filter == 'no_payments':
            query = query.filter(
                or_(Customer.total_payments == 0, Customer.total_payments.is_(None))
            )
        elif payment_filter == 'poor_payer':
            # Customers with high churn probability due to payment issues
            query = query.filter(Customer.churn_risk == 'high')
        elif payment_filter == 'good_payer':
            # Customers with recent payments and low risk
            query = query.filter(Customer.churn_risk == 'low')
        
        # Calculate enhanced tenure and payment metrics for display
        customers_query = query.order_by(desc(Customer.created_at))
        pagination = customers_query.paginate(page=page, per_page=per_page, error_out=False)
        
        for customer in pagination.items:
            if customer.signup_date:
                tenure_delta = datetime.utcnow() - customer.signup_date
                customer.tenure_months = max(1, tenure_delta.days // 30)
            else:
                customer.tenure_months = 0
        
        return render_template('crm/customers.html', 
                             company=company,
                             customers=pagination.items,
                             pagination=pagination,
                             current_status=status_filter,
                             current_risk=risk_filter,
                             current_search=search_filter,
                             current_payment_behavior=payment_filter,
                             datetime=datetime
                             ) # ✅ NEW filter
        
        
                            
                             
    except Exception as e:
        current_app.logger.error(f"Enhanced customers page error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Return safe fallback
        return render_template('crm/customers.html',
                             company=company,
                             customers=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='', current_risk='', current_search='', current_payment_behavior='',
                             error_message=str(e),
                             datetime=datetime
                             )

# ✅ PRESERVED: All other existing routes (payments, tickets, customer_detail, ticket_detail) remain the same
# Just import them from the original controller or copy them here

@crm_bp.route('/payments')
@login_required
def payments():
    """Payment management page - PRESERVED FROM ORIGINAL"""
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
                             company=company,
                             payments=pagination.items,
                             pagination=pagination,
                             current_status=status_filter,
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
                             current_status='', current_method='', current_search='',
                             error_message=str(e))

@crm_bp.route('/tickets')
@login_required
def tickets():
    """Ticket management page - PRESERVED FROM ORIGINAL"""
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
                             company=company,
                             tickets=pagination.items,
                             pagination=pagination,
                             current_status=status_filter,
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
                             current_status='', current_priority='', current_search='',
                             error_message=str(e))

@crm_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Enhanced customer detail page with payment-based insights"""
    company = current_user.company
    if not company:
        return redirect(url_for('dashboard.index'))
    
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=company.id
    ).first_or_404()
    
    # Calculate enhanced tenure
    if customer.signup_date:
        tenure_delta = datetime.utcnow() - customer.signup_date
        customer.tenure_months = max(1, tenure_delta.days // 30)
    
    # ✅ ENHANCED: Add payment behavior analysis
    if hasattr(customer, 'last_payment_date') and customer.last_payment_date:
        days_since_payment = (datetime.utcnow() - customer.last_payment_date).days
        customer.days_since_last_payment = days_since_payment
        
        # Apply n.py risk logic for display
        if days_since_payment >= 90:
            customer.payment_risk_level = 'HIGH'
            customer.payment_risk_message = f"No payments for {days_since_payment} days - URGENT ACTION REQUIRED"
        elif days_since_payment >= 60:
            customer.payment_risk_level = 'MEDIUM'
            customer.payment_risk_message = f"No payments for {days_since_payment} days - Monitor closely"
        else:
            customer.payment_risk_level = 'LOW'
            customer.payment_risk_message = f"Recent payment ({days_since_payment} days ago) - Good standing"
    else:
        customer.payment_risk_level = 'UNKNOWN'
        customer.payment_risk_message = "No payment data available"
        customer.days_since_last_payment = None
    
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
                         payments=recent_payments,
                         tickets=recent_tickets)

@crm_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    """Ticket detail page - PRESERVED FROM ORIGINAL"""
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