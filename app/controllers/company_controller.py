"""
Company Controller - Company Management and Settings
Streamlined version that uses Company model methods for churn prediction
Safe version that handles missing Phase 4 models
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.company import Company
from app.models.user import User
from app.middleware.tenant_middleware import manager_required, admin_required
from app.services.crm_service import CRMService
import logging

logger = logging.getLogger(__name__)

# Create blueprint
company_bp = Blueprint('company', __name__)


@company_bp.route('/')
@login_required
def index():
    """
    Company overview page with enhanced churn prediction visualization
    Shows company details, statistics, and churn prediction insights
    """
    company = current_user.company
    
    # Get basic company statistics
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
    
    # Enhanced churn prediction statistics - now from model
    churn_stats = company.get_churn_visualization_data()
    
    return render_template('company/index.html', 
                         company=company, 
                         stats=stats, 
                         churn_stats=churn_stats)


@company_bp.route('/churn-dashboard')
@login_required
def churn_dashboard():
    """
    Dedicated churn prediction dashboard with comprehensive visualizations
    """
    company = current_user.company
    
    # Get comprehensive churn data from model methods
    churn_data = {
        'overview': company.get_churn_overview(),
        'risk_distribution': company.get_risk_distribution(),
        'trend_analysis': company.get_churn_trend_analysis(),
        'segment_analysis': company.get_customer_segment_analysis(),
        'top_risk_customers': company.get_top_risk_customers(),
        'intervention_opportunities': company.get_intervention_opportunities(),
        'prediction_accuracy': company.get_prediction_accuracy_metrics()
    }
    
    return render_template('company/churn_dashboard.html', 
                         company=company, 
                         churn_data=churn_data)


@company_bp.route('/churn-visualizations')
@login_required
def churn_visualizations():
    """
    Interactive churn prediction visualizations page
    """
    company = current_user.company
    
    # Get data for various visualization types from model methods
    viz_data = {
        'gauge_charts': company.get_gauge_chart_data(),
        'progress_bars': company.get_progress_bar_data(),
        'heatmaps': company.get_heatmap_data(),
        'scatter_plots': company.get_scatter_plot_data(),
        'timeline_data': company.get_timeline_data()
    }
    
    return render_template('company/churn_visualizations.html', 
                         company=company, 
                         viz_data=viz_data)


@company_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@manager_required
def settings():
    """
    Company settings page with enhanced churn prediction configuration
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
            
            # Enhanced application settings with churn prediction configs
            settings_updates = {
                'notification_email': request.form.get('notification_email', '').strip(),
                'enable_email_alerts': request.form.get('enable_email_alerts') == 'on',
                'enable_auto_sync': request.form.get('enable_auto_sync') == 'on',
                'sync_frequency': int(request.form.get('sync_frequency', 3600)),
                
                # Churn prediction thresholds
                'prediction_threshold_high': float(request.form.get('threshold_high', 0.7)),
                'prediction_threshold_medium': float(request.form.get('threshold_medium', 0.4)),
                'prediction_threshold_low': float(request.form.get('threshold_low', 0.2)),
                
                # Churn visualization settings
                'enable_churn_alerts': request.form.get('enable_churn_alerts') == 'on',
                'churn_alert_frequency': int(request.form.get('churn_alert_frequency', 24)),
                'auto_intervention_enabled': request.form.get('auto_intervention_enabled') == 'on',
                'intervention_threshold': float(request.form.get('intervention_threshold', 0.8)),
                
                # Dashboard settings
                'dashboard_refresh_interval': int(request.form.get('dashboard_refresh_interval', 300)),
                'show_prediction_confidence': request.form.get('show_prediction_confidence') == 'on',
                'enable_customer_segments': request.form.get('enable_customer_segments') == 'on',
                
                # Display preferences
                'timezone': request.form.get('timezone', 'UTC'),
                'date_format': request.form.get('date_format', '%Y-%m-%d'),
                'currency': request.form.get('currency', 'USD'),
                'chart_color_scheme': request.form.get('chart_color_scheme', 'default')
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
            # Get form data
            email = request.form.get('email', '').strip().lower()
            full_name = request.form.get('full_name', '').strip()
            role = request.form.get('role', 'viewer').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            is_active = request.form.get('is_active') == 'on'
            
            # Validation
            if not email:
                flash('Email is required', 'danger')
                return render_template('company/add_user.html')
            
            if not full_name:
                flash('Full name is required', 'danger')
                return render_template('company/add_user.html')
            
            if not password:
                flash('Password is required', 'danger')
                return render_template('company/add_user.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters', 'danger')
                return render_template('company/add_user.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('company/add_user.html')
            
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('A user with this email already exists', 'danger')
                return render_template('company/add_user.html')
            
            # Validate role
            valid_roles = ['viewer', 'analyst', 'manager', 'admin']
            if role not in valid_roles:
                flash('Invalid role selected', 'danger')
                return render_template('company/add_user.html')
            
            # Create new user
            new_user = User(
                email=email,
                full_name=full_name,
                company_id=current_user.company_id,
                role=role,
                is_active=is_active
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User {full_name} ({email}) added successfully with role: {role}', 'success')
            return redirect(url_for('company.users'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding user: {e}")
            flash(f'Failed to add user: {str(e)}', 'danger')
            return render_template('company/add_user.html')
    
    # GET request - show form
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
        crm_service = CRMService(company)
        
        # Run sync
        results = crm_service.sync_data()
        
        if results.get('status') == 'error':
            return jsonify({
                'success': False,
                'message': results.get('message', 'Sync failed')
            }), 500
        
        return jsonify({
            'success': True,
            'message': results.get('message', 'CRM service is not yet implemented (Phase 4)'),
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
    

@company_bp.route('/sync/reset', methods=['POST'])
@login_required
@manager_required
def reset_sync_status():
    """
    Reset sync status if stuck
    """
    try:
        company = current_user.company
        
        logger.info(f"Manually resetting sync status for company {company.id}")
        
        company.sync_status = 'pending'
        company.sync_error = None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sync status has been reset. You can now start a new sync.'
        })
        
    except Exception as e:
        logger.error(f"Error resetting sync status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@company_bp.route('/statistics')
@login_required
def statistics():
    """
    Get comprehensive company statistics as JSON
    Enhanced with churn prediction metrics using model methods
    For dashboard widgets and AJAX requests
    """
    company = current_user.company
    
    # Basic statistics
    basic_stats = {
        'customers': {
            'total': company.get_customer_count(),
            'active': company.get_active_customer_count(),
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
            'total': company.users.count(),
            'active': company.get_active_user_count(),
        },
        'sync': {
            'status': company.sync_status,
            'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
            'total_syncs': company.total_syncs,
        }
    }
    
    # Enhanced churn statistics from model
    churn_stats = company.get_churn_visualization_data()
    
    # Combine all statistics
    stats = {**basic_stats, 'churn': churn_stats}
    
    return jsonify(stats)


# Enhanced API endpoints for churn prediction visualization using model methods
@company_bp.route('/api/churn/overview')
@login_required
def api_churn_overview():
    """API endpoint for churn overview data"""
    company = current_user.company
    data = company.get_churn_overview()
    return jsonify(data)


@company_bp.route('/api/churn/risk-distribution')
@login_required
def api_risk_distribution():
    """API endpoint for risk distribution data"""
    company = current_user.company
    data = company.get_risk_distribution()
    return jsonify(data)


@company_bp.route('/api/churn/trend-analysis')
@login_required
def api_trend_analysis():
    """API endpoint for churn trend analysis"""
    company = current_user.company
    days = request.args.get('days', 30, type=int)
    data = company.get_churn_trend_analysis(days)
    return jsonify(data)


@company_bp.route('/api/churn/customer-segments')
@login_required
def api_customer_segments():
    """API endpoint for customer segment analysis"""
    company = current_user.company
    data = company.get_customer_segment_analysis()
    return jsonify(data)


@company_bp.route('/api/churn/top-risk-customers')
@login_required
def api_top_risk_customers():
    """API endpoint for top risk customers"""
    company = current_user.company
    limit = request.args.get('limit', 10, type=int)
    data = company.get_top_risk_customers(limit)
    return jsonify(data)


@company_bp.route('/api/churn/intervention-opportunities')
@login_required
def api_intervention_opportunities():
    """API endpoint for intervention opportunities"""
    company = current_user.company
    data = company.get_intervention_opportunities()
    return jsonify(data)


@company_bp.route('/api/churn/gauge-data')
@login_required
def api_gauge_data():
    """API endpoint for gauge chart data"""
    company = current_user.company
    data = company.get_gauge_chart_data()
    return jsonify(data)


@company_bp.route('/api/churn/progress-data')
@login_required
def api_progress_data():
    """API endpoint for progress bar data"""
    company = current_user.company
    data = company.get_progress_bar_data()
    return jsonify(data)


@company_bp.route('/api/churn/heatmap-data')
@login_required
def api_heatmap_data():
    """API endpoint for heatmap data"""
    company = current_user.company
    data = company.get_heatmap_data()
    return jsonify(data)


@company_bp.route('/api/churn/scatter-data')
@login_required
def api_scatter_data():
    """API endpoint for scatter plot data"""
    company = current_user.company
    data = company.get_scatter_plot_data()
    return jsonify(data)


@company_bp.route('/api/churn/timeline-data')
@login_required
def api_timeline_data():
    """API endpoint for timeline data"""
    company = current_user.company
    data = company.get_timeline_data()
    return jsonify(data)


@company_bp.route('/api/test-notifications', methods=['POST'])
@login_required
@manager_required
def test_notifications():
    """Test notification system"""
    try:
        company = current_user.company
        notification_email = company.get_setting('notification_email')
        
        if not notification_email:
            return jsonify({
                'success': False,
                'message': 'No notification email configured'
            }), 400
        
        # Here you would implement actual email sending
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f'Test notification would be sent to {notification_email}'
        })
        
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500