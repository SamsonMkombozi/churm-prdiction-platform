"""
Company Controller - Company Management and Settings
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.company import Company
from app.models.user import User
from app.middleware.tenant_middleware import manager_required, admin_required
from app.services.crm_service import CRMService  # TODO: Create this
import logging

logger = logging.getLogger(__name__)

# Create blueprint
company_bp = Blueprint('company', __name__)


@company_bp.route('/')
@login_required
def index():
    """
    Company overview page
    Shows company details and statistics
    """
    company = current_user.company
    
    # Get company statistics
    stats = {
        'total_customers': company.get_customer_count(),
        'total_tickets': company.get_ticket_count(),
        'total_payments': company.get_payment_count(),
        'total_predictions': company.get_prediction_count(),
        'high_risk_customers': company.get_high_risk_customer_count(),
        'active_users': company.get_active_user_count(),
        'last_sync': company.last_sync_at,
        'sync_status': company.sync_status
    }
    
    return render_template('company/index.html', company=company, stats=stats)


@company_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@manager_required
def settings():
    """
    Company settings page
    GET: Show settings form
    POST: Update settings
    """
    company = current_user.company
    
    if request.method == 'POST':
        try:
            # Update basic information
            company.name = request.form.get('name', company.name).strip()
            company.description = request.form.get('description', '').strip()
            company.industry = request.form.get('industry', '').strip()
            company.website = request.form.get('website', '').strip()
            
            # Update CRM settings
            crm_api_url = request.form.get('crm_api_url', '').strip()
            if crm_api_url:
                company.crm_api_url = crm_api_url
            
            # Update CRM API key if provided
            crm_api_key = request.form.get('crm_api_key', '').strip()
            if crm_api_key:
                company.set_crm_api_key(crm_api_key)
            
            # Update application settings
            settings_updates = {
                'notification_email': request.form.get('notification_email', '').strip(),
                'enable_email_alerts': request.form.get('enable_email_alerts') == 'on',
                'enable_auto_sync': request.form.get('enable_auto_sync') == 'on',
                'sync_frequency': int(request.form.get('sync_frequency', 3600)),
                'prediction_threshold_high': float(request.form.get('threshold_high', 0.7)),
                'prediction_threshold_medium': float(request.form.get('threshold_medium', 0.4)),
                'timezone': request.form.get('timezone', 'UTC'),
                'date_format': request.form.get('date_format', '%Y-%m-%d'),
                'currency': request.form.get('currency', 'USD')
            }
            
            company.update_settings(settings_updates)
            
            db.session.commit()
            flash('Company settings updated successfully', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating company settings: {e}")
            flash(f'Failed to update settings: {str(e)}', 'danger')
    
    return render_template('company/settings.html', company=company)


@company_bp.route('/users')
@login_required
@manager_required
def users():
    """
    Manage company users
    Shows list of users in the company
    """
    company = current_user.company
    users = company.users.order_by(User.created_at.desc()).all()
    
    return render_template('company/users.html', company=company, users=users)


@company_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """
    Add new user to company
    GET: Show add user form
    POST: Create new user
    """
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            full_name = request.form.get('full_name', '').strip()
            role = request.form.get('role', 'viewer')
            password = request.form.get('password', '')
            
            # Validation
            if not email or not full_name or not password:
                flash('All fields are required', 'danger')
                return render_template('company/add_user.html')
            
            # Check if user exists
            existing_user = User.find_by_email(email)
            if existing_user:
                flash('User with this email already exists', 'danger')
                return render_template('company/add_user.html')
            
            # Create user
            from app.models.user import UserRole
            user_role = UserRole[role.upper()]
            
            new_user = User.create_user(
                email=email,
                password=password,
                full_name=full_name,
                company_id=current_user.company_id,
                role=user_role
            )
            
            flash(f'User {full_name} added successfully', 'success')
            return redirect(url_for('company.users'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding user: {e}")
            flash(f'Failed to add user: {str(e)}', 'danger')
    
    return render_template('company/add_user.html')


@company_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Verify user belongs to current company
        if user.company_id != current_user.company_id:
            flash('Unauthorized action', 'danger')
            return redirect(url_for('company.users'))
        
        # Don't allow deactivating self
        if user.id == current_user.id:
            flash('You cannot deactivate your own account', 'warning')
            return redirect(url_for('company.users'))
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.full_name} {status} successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user status: {e}")
        flash(f'Failed to update user status: {str(e)}', 'danger')
    
    return redirect(url_for('company.users'))


@company_bp.route('/sync', methods=['POST'])
@login_required
@manager_required
def sync_data():
    """
    Trigger manual CRM data synchronization
    """
    try:
        company = current_user.company
        
        # Check if sync is already in progress
        if company.sync_status == 'in_progress':
            return jsonify({
                'success': False,
                'message': 'Sync already in progress'
            }), 400
        
        # Initialize CRM service
        crm_service = CRMService(company.id)
        
        # Run sync
        results = crm_service.sync_all_data()
        
        if 'error' in results:
            return jsonify({
                'success': False,
                'message': results['error']
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Data synchronized successfully',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@company_bp.route('/sync-status')
@login_required
def sync_status():
    """
    Get current sync status
    """
    company = current_user.company
    
    return jsonify({
        'status': company.sync_status,
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'total_syncs': company.total_syncs,
        'error': company.sync_error
    })


@company_bp.route('/statistics')
@login_required
def statistics():
    """
    Get company statistics as JSON
    For dashboard widgets and AJAX requests
    """
    company = current_user.company
    
    stats = {
        'customers': {
            'total': company.get_customer_count(),
        },
        'tickets': {
            'total': company.get_ticket_count(),
        },
        'payments': {
            'total': company.get_payment_count(),
        },
        'predictions': {
            'total': company.get_prediction_count(),
            'high_risk': company.get_high_risk_customer_count(),
        },
        'users': {
            'active': company.get_active_user_count(),
        },
        'sync': {
            'status': company.sync_status,
            'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
            'total_syncs': company.total_syncs
        }
    }
    
    return jsonify(stats)