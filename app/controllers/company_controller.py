"""
Enhanced Company Controller with PostgreSQL Configuration
app/controllers/company_controller.py

Features:
1. PostgreSQL configuration handling
2. Connection testing
3. Enhanced settings management
4. Real-time data display from CRM database
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.company import Company
from app.models.user import User
from app.middleware.tenant_middleware import manager_required, admin_required
from app.services.crm_service import EnhancedCRMService
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint
company_bp = Blueprint('company', __name__)

@company_bp.route('/')
@login_required
def index():
    """
    Enhanced company overview with real CRM data
    """
    company = current_user.company
    
    if not company:
        flash('No company associated with your account.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Get comprehensive dashboard statistics
    stats = company.get_dashboard_stats()
    
    # Get connection info
    try:
        crm_service = EnhancedCRMService(company)
        connection_info = crm_service.get_connection_info()
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        connection_info = {'preferred_method': 'none'}
    
    return render_template('company/index.html', 
                         company=company, 
                         stats=stats,
                         connection_info=connection_info)

@company_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@manager_required
def settings():
    """
    Enhanced company settings with PostgreSQL configuration
    """
    company = current_user.company
    
    if request.method == 'POST':
        try:
            # Update basic information
            company.name = request.form.get('name', company.name).strip()
            company.description = request.form.get('description', '').strip()
            company.industry = request.form.get('industry', '').strip()
            company.website = request.form.get('website', '').strip()
            
            # ✅ ENHANCED: Update PostgreSQL settings
            postgresql_host = request.form.get('postgresql_host', '').strip()
            postgresql_port = request.form.get('postgresql_port', '5432').strip()
            postgresql_database = request.form.get('postgresql_database', '').strip()
            postgresql_username = request.form.get('postgresql_username', '').strip()
            postgresql_password = request.form.get('postgresql_password', '').strip()
            
            # Update PostgreSQL configuration
            if postgresql_host:
                company.postgresql_host = postgresql_host
            if postgresql_port:
                try:
                    company.postgresql_port = int(postgresql_port)
                except ValueError:
                    company.postgresql_port = 5432
            if postgresql_database:
                company.postgresql_database = postgresql_database
            if postgresql_username:
                company.postgresql_username = postgresql_username
            if postgresql_password:
                company.set_postgresql_password(postgresql_password)
            
            # ✅ ENHANCED: Update API settings
            api_base_url = request.form.get('api_base_url', '').strip()
            api_username = request.form.get('api_username', '').strip()
            api_password = request.form.get('api_password', '').strip()
            api_key = request.form.get('api_key', '').strip()
            
            if api_base_url:
                company.api_base_url = api_base_url
            if api_username:
                company.api_username = api_username
            if api_password:
                company.set_api_password(api_password)
            if api_key:
                company.set_api_key(api_key)
            
            # ✅ ENHANCED: Update application settings
            settings_updates = {
                'enable_auto_sync': request.form.get('enable_auto_sync') == 'on',
                'sync_frequency': int(request.form.get('sync_frequency', 3600)),
                'notification_email': request.form.get('notification_email', '').strip(),
                'enable_email_alerts': request.form.get('enable_email_alerts') == 'on',
                'enable_sync_notifications': request.form.get('enable_sync_notifications') == 'on',
                
                # Default sync options
                'default_sync_customers': request.form.get('default_sync_customers') == 'on',
                'default_sync_payments': request.form.get('default_sync_payments') == 'on',
                'default_sync_tickets': request.form.get('default_sync_tickets') == 'on',
                'default_sync_usage': request.form.get('default_sync_usage') == 'on',
                
                # Prediction thresholds
                'prediction_threshold_high': float(request.form.get('threshold_high', 0.7)),
                'prediction_threshold_medium': float(request.form.get('threshold_medium', 0.4)),
                'prediction_threshold_low': float(request.form.get('threshold_low', 0.2)),
                'auto_prediction_enabled': request.form.get('auto_prediction_enabled') == 'on',
                
                # Regional settings
                'timezone': request.form.get('timezone', 'UTC'),
                'date_format': request.form.get('date_format', '%Y-%m-%d'),
                'currency': request.form.get('currency', 'TZS')
            }
            
            company.update_settings(settings_updates)
            
            db.session.commit()
            
            # Provide helpful feedback based on configuration
            if company.has_postgresql_config():
                flash('✅ Settings saved! PostgreSQL configuration detected - you can now enjoy 10-50x faster sync performance!', 'success')
            elif company.has_api_config():
                flash('✅ Settings saved! API configuration detected. Consider adding PostgreSQL for better performance.', 'success')
            else:
                flash('✅ Settings saved! Configure PostgreSQL or API connection to enable data synchronization.', 'warning')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating company settings: {e}")
            logger.error(traceback.format_exc())
            flash(f'Failed to update settings: {str(e)}', 'danger')
    
    return render_template('company/settings.html', company=company)

@company_bp.route('/test-connection', methods=['POST'])
@login_required
@manager_required
def test_connection():
    """
    Test database connections
    """
    try:
        company = current_user.company
        test_type = request.json.get('test_type', 'postgresql')
        connection_data = request.json.get('connection_data', {})
        
        results = {}
        
        if test_type in ['postgresql', 'all']:
            # Test PostgreSQL connection
            try:
                crm_service = EnhancedCRMService(company)
                postgres_result = crm_service.test_postgresql_connection()
                results['postgresql'] = postgres_result
            except Exception as e:
                results['postgresql'] = {
                    'success': False,
                    'message': f'PostgreSQL test failed: {str(e)}',
                    'details': ['Check if psycopg2 is installed and PostgreSQL is accessible']
                }
        
        if test_type in ['api', 'all']:
            # Test API connection
            try:
                # Simple API connectivity test
                import requests
                if company.api_base_url:
                    response = requests.get(company.api_base_url, timeout=10)
                    if response.status_code in [200, 401, 403]:
                        results['api'] = {
                            'success': True,
                            'message': 'API endpoint is reachable',
                            'details': [f'Status code: {response.status_code}', 'API connection available']
                        }
                    else:
                        results['api'] = {
                            'success': False,
                            'message': f'API returned status {response.status_code}',
                            'details': ['Check API URL and server status']
                        }
                else:
                    results['api'] = {
                        'success': False,
                        'message': 'API URL not configured',
                        'details': ['Configure API base URL in settings']
                    }
            except Exception as e:
                results['api'] = {
                    'success': False,
                    'message': f'API test failed: {str(e)}',
                    'details': ['Check API URL and network connectivity']
                }
        
        # Generate summary
        summary_parts = []
        if results.get('postgresql', {}).get('success'):
            summary_parts.append('✅ PostgreSQL: Ready for high-speed sync')
        elif 'postgresql' in results:
            summary_parts.append('❌ PostgreSQL: Configuration needed')
        
        if results.get('api', {}).get('success'):
            summary_parts.append('✅ API: Available as fallback')
        elif 'api' in results:
            summary_parts.append('❌ API: Configuration needed')
        
        if not summary_parts:
            summary = 'No connection methods configured. Please setup PostgreSQL or API.'
        else:
            summary = ' | '.join(summary_parts)
        
        results['summary'] = summary
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        }), 500

@company_bp.route('/sync', methods=['POST'])
@login_required
@manager_required
def sync_data():
    """
    Enhanced manual CRM data synchronization
    """
    try:
        company = current_user.company
        
        # Check if sync is already in progress
        if company.sync_status == 'in_progress':
            return jsonify({
                'success': False,
                'message': 'Sync already in progress'
            }), 400
        
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
        
        logger.info(f"🚀 Starting enhanced sync for {company.name}")
        logger.info(f"📊 Sync options: {sync_options}")
        
        # Initialize enhanced CRM service
        crm_service = EnhancedCRMService(company)
        
        # Check connection configuration
        connection_info = crm_service.get_connection_info()
        
        if connection_info['preferred_method'] == 'none':
            return jsonify({
                'success': False,
                'message': 'No sync method configured. Please configure PostgreSQL or API connection in Company Settings.',
                'help': 'Configure PostgreSQL for 10-50x faster performance, or API for standard sync speed.'
            }), 400
        
        # Run enhanced sync
        results = crm_service.sync_data_selective(sync_options)
        
        if results.get('success'):
            # Build enhanced success message
            stats = results['stats']
            performance = results.get('performance', {})
            
            message_parts = []
            if stats['customers']['new'] + stats['customers']['updated'] > 0:
                message_parts.append(f"{stats['customers']['new'] + stats['customers']['updated']} customers")
            if stats['payments']['new'] + stats['payments']['updated'] > 0:
                message_parts.append(f"{stats['payments']['new'] + stats['payments']['updated']} payments")
            if stats['tickets']['new'] + stats['tickets']['updated'] > 0:
                message_parts.append(f"{stats['tickets']['new'] + stats['tickets']['updated']} tickets")
            if stats['usage']['new'] + stats['usage']['updated'] > 0:
                message_parts.append(f"{stats['usage']['new'] + stats['usage']['updated']} usage records")
            
            base_message = f"Enhanced sync completed! Processed {', '.join(message_parts) if message_parts else 'data'}"
            
            # Add performance info
            if performance.get('connection_method') == 'postgresql':
                base_message += f" via PostgreSQL in {performance.get('sync_duration', 0)}s"
                if performance.get('records_per_second'):
                    base_message += f" ({performance['records_per_second']} records/sec)"
            
            return jsonify({
                'success': True,
                'message': base_message,
                'stats': stats,
                'performance': performance,
                'connection_method': connection_info['preferred_method']
            })
        else:
            return jsonify({
                'success': False,
                'message': results.get('message', 'Sync failed'),
                'stats': results.get('stats', {}),
                'error_details': results.get('error_details')
            }), 500
            
    except Exception as e:
        logger.error(f"Enhanced sync error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update company status
        company.mark_sync_failed(str(e))
        
        return jsonify({
            'success': False,
            'message': f"Enhanced sync failed: {str(e)}",
            'help': 'Check your PostgreSQL or API configuration and try again.'
        }), 500

@company_bp.route('/sync-status')
@login_required
def sync_status():
    """
    Get enhanced sync status with performance info
    """
    company = current_user.company
    
    # Get connection info
    try:
        crm_service = EnhancedCRMService(company)
        connection_info = crm_service.get_connection_info()
    except Exception as e:
        connection_info = {'preferred_method': 'none'}
    
    return jsonify({
        'status': company.sync_status,
        'last_sync': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'total_syncs': company.total_syncs,
        'error': company.sync_error,
        'connection_method': connection_info['preferred_method'],
        'performance_info': connection_info.get('performance_boost', 'Unknown'),
        'configuration_status': {
            'postgresql_configured': connection_info.get('postgresql_configured', False),
            'api_configured': connection_info.get('api_configured', False)
        }
    })

@company_bp.route('/reset-sync-status', methods=['POST'])
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