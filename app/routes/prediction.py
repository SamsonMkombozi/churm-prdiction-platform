"""
Prediction Routes - FIXED
app/routes/prediction.py

Fixes "too many values to unpack" error
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.decorators import company_required
from app.extensions import db
from sqlalchemy import desc

prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')


@prediction_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    """Prediction dashboard"""
    company = current_user.company
    
    # Get statistics
    stats = {
        'total_predictions': Prediction.query.filter_by(company_id=company.id).count(),
        'high_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='high').count(),
        'medium_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='medium').count(),
        'low_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='low').count(),
        'total_customers': Customer.query.filter_by(company_id=company.id).count()
    }
    
    # Get high-risk customers with their latest predictions
    # ✅ FIX: Query properly to avoid unpacking issues
    high_risk_predictions = Prediction.query.filter_by(
        company_id=company.id,
        churn_risk='high'
    ).order_by(desc(Prediction.predicted_at)).limit(10).all()
    
    # ✅ FIX: Build list properly
    high_risk_customers = []
    for prediction in high_risk_predictions:
        customer = Customer.query.get(prediction.customer_id)
        if customer:
            high_risk_customers.append((customer, prediction))
    
    return render_template('prediction/dashboard.html',
                         stats=stats,
                         high_risk_customers=high_risk_customers,
                         company=company)


@prediction_bp.route('/high-risk')
@login_required
@company_required
def high_risk_customers():
    """List all high-risk customers"""
    company = current_user.company
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # ✅ FIX: Query high-risk predictions with pagination
    predictions_query = Prediction.query.filter_by(
        company_id=company.id,
        churn_risk='high'
    ).order_by(desc(Prediction.churn_probability))
    
    pagination = predictions_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # ✅ FIX: Build customer-prediction pairs
    items = []
    for prediction in pagination.items:
        customer = Customer.query.get(prediction.customer_id)
        if customer:
            items.append((customer, prediction))
    
    # Replace pagination items with our pairs
    pagination.items = items
    
    return render_template('prediction/high_risk.html',
                         pagination=pagination,
                         current_status='high',
                         company=company)


@prediction_bp.route('/customer/<int:customer_id>')
@login_required
@company_required
def customer_prediction(customer_id):
    """View customer prediction details"""
    company = current_user.company
    
    # Get customer
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=company.id
    ).first_or_404()
    
    # Get latest prediction
    prediction = Prediction.query.filter_by(
        customer_id=customer_id,
        company_id=company.id
    ).order_by(desc(Prediction.predicted_at)).first()
    
    if not prediction:
        flash('No prediction available for this customer. Run predictions first.', 'warning')
        return redirect(url_for('crm.customer_detail', customer_id=customer_id))
    
    # Get prediction history
    prediction_history = Prediction.query.filter_by(
        customer_id=customer_id,
        company_id=company.id
    ).order_by(desc(Prediction.predicted_at)).limit(10).all()
    
    # Get insights
    from app.services.prediction_service import ChurnPredictionService
    prediction_service = ChurnPredictionService(company)
    insights = prediction_service.get_churn_insights(customer)
    
    # Get related data
    tickets = customer.tickets[:5] if hasattr(customer, 'tickets') else []
    payments = customer.payments[:5] if hasattr(customer, 'payments') else []
    
    return render_template('prediction/customer_detail.html',
                         customer=customer,
                         prediction=prediction,
                         prediction_history=prediction_history,
                         insights=insights,
                         tickets=tickets,
                         payments=payments,
                         company=company)


@prediction_bp.route('/run', methods=['POST'])
@login_required
@company_required
def run_predictions():
    """Run predictions for all customers"""
    try:
        company = current_user.company
        
        # Check if we have customers
        customer_count = Customer.query.filter_by(company_id=company.id).count()
        if customer_count == 0:
            return jsonify({
                'success': False,
                'message': 'No customers found. Please sync CRM data first.'
            }), 400
        
        # Initialize prediction service
        from app.services.prediction_service import ChurnPredictionService
        prediction_service = ChurnPredictionService(company)
        
        # Run predictions
        results = prediction_service.predict_all_customers()
        
        if results['success']:
            message = f"Successfully predicted churn for {results['predictions_created']} customers. "
            message += f"High risk: {results['high_risk']}, "
            message += f"Medium risk: {results['medium_risk']}, "
            message += f"Low risk: {results['low_risk']}"
            
            return jsonify({
                'success': True,
                'message': message,
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Prediction failed: ' + ', '.join(results.get('errors', ['Unknown error']))
            }), 500
        
    except Exception as e:
        logger.error(f"Error running predictions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error running predictions: {str(e)}'
        }), 500


@prediction_bp.route('/export')
@login_required
@company_required
def export_predictions():
    """Export predictions to CSV"""
    # TODO: Implement CSV export
    flash('Export feature coming soon!', 'info')
    return redirect(url_for('prediction.dashboard'))