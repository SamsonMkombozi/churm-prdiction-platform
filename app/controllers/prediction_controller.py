"""
Prediction Controller - Churn Prediction Routes
app/controllers/prediction_controller.py
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.services.prediction_service import PredictionService
from app.middleware.tenant_middleware import manager_required
import logging

logger = logging.getLogger(__name__)

# Create blueprint
prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Prediction Dashboard - Overview of churn predictions
    """
    company = current_user.company
    
    # Get prediction statistics
    total_predictions = Prediction.query.filter_by(company_id=company.id).count()
    high_risk = Prediction.query.filter_by(company_id=company.id, churn_risk='high').count()
    medium_risk = Prediction.query.filter_by(company_id=company.id, churn_risk='medium').count()
    low_risk = Prediction.query.filter_by(company_id=company.id, churn_risk='low').count()
    
    # Get recent high-risk customers
    high_risk_customers = db.session.query(Customer, Prediction).join(
        Prediction, Customer.id == Prediction.customer_id
    ).filter(
        Customer.company_id == company.id,
        Prediction.churn_risk == 'high'
    ).order_by(Prediction.churn_probability.desc()).limit(10).all()
    
    stats = {
        'total_predictions': total_predictions,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
    }
    
    return render_template(
        'prediction/dashboard.html',
        company=company,
        stats=stats,
        high_risk_customers=high_risk_customers
    )


@prediction_bp.route('/run', methods=['POST'])
@login_required
@manager_required
def run_predictions():
    """
    Run predictions for all customers
    """
    try:
        company = current_user.company
        
        # Initialize prediction service
        pred_service = PredictionService(company)
        
        # Run predictions and update database
        result = pred_service.update_customer_predictions()
        
        flash(
            f'Predictions complete! Updated {result["updated"]} customers.',
            'success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Predictions complete! Updated {result["updated"]} customers.',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@prediction_bp.route('/customer/<int:customer_id>')
@login_required
def customer_prediction(customer_id):
    """
    View prediction details for a specific customer
    """
    company = current_user.company
    
    # Get customer
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=company.id
    ).first_or_404()
    
    # Get latest prediction
    prediction = Prediction.get_latest_for_customer(company.id, customer_id)
    
    # Get prediction history
    prediction_history = Prediction.query.filter_by(
        company_id=company.id,
        customer_id=customer_id
    ).order_by(Prediction.predicted_at.desc()).limit(10).all()
    
    return render_template(
        'prediction/customer_detail.html',
        company=company,
        customer=customer,
        prediction=prediction,
        prediction_history=prediction_history
    )


@prediction_bp.route('/high-risk')
@login_required
def high_risk_customers():
    """
    List all high-risk customers
    """
    company = current_user.company
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query high-risk customers with their predictions
    pagination = db.session.query(Customer, Prediction).join(
        Prediction, Customer.id == Prediction.customer_id
    ).filter(
        Customer.company_id == company.id,
        Prediction.churn_risk == 'high'
    ).order_by(Prediction.churn_probability.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template(
        'prediction/high_risk.html',
        company=company,
        pagination=pagination
    )


@prediction_bp.route('/model-info')
@login_required
def model_info():
    """
    Get model information
    """
    try:
        company = current_user.company
        pred_service = PredictionService(company)
        
        info = pred_service.get_model_info()
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@prediction_bp.route('/statistics')
@login_required
def statistics():
    """
    Get prediction statistics as JSON
    """
    company = current_user.company
    
    stats = {
        'total_predictions': Prediction.query.filter_by(company_id=company.id).count(),
        'high_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='high').count(),
        'medium_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='medium').count(),
        'low_risk': Prediction.query.filter_by(company_id=company.id, churn_risk='low').count(),
        'total_customers': Customer.query.filter_by(company_id=company.id).count(),
    }
    
    return jsonify(stats)