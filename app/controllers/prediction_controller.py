# app/controllers/prediction_controller.py - UPDATED FOR REAL PREDICTIONS
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
import traceback
from datetime import datetime
import logging

from app.services.prediction_service import ChurnPredictionService
from app.models.company import Company
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.extensions import db

# Create blueprint
prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

# Set up logging
logger = logging.getLogger(__name__)

@prediction_bp.route('/test')
def test():
    """Test route to verify controller is working"""
    return jsonify({
        'status': 'success',
        'message': 'Prediction controller is working!',
        'timestamp': datetime.now().isoformat()
    })

@prediction_bp.route('/dashboard')
@login_required
def dashboard():
    """Prediction dashboard with real data"""
    try:
        company = current_user.company
        if not company:
            flash('No company associated with your account', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Get customers for prediction statistics
        customers = Customer.query.filter_by(company_id=company.id).all()
        
        # Initialize prediction service and get model info
        prediction_service = ChurnPredictionService()
        model_info = prediction_service.get_model_info()
        
        # Calculate statistics
        total_customers = len(customers)
        
        # Get existing predictions
        recent_predictions = Prediction.query.filter_by(
            company_id=company.id
        ).order_by(Prediction.predicted_at.desc()).limit(100).all()
        
        # Calculate risk distribution from recent predictions
        high_risk_count = sum(1 for p in recent_predictions if p.churn_risk == 'high')
        medium_risk_count = sum(1 for p in recent_predictions if p.churn_risk == 'medium')
        low_risk_count = sum(1 for p in recent_predictions if p.churn_risk == 'low')
        
        # Calculate average prediction accuracy (if we have historical data)
        if recent_predictions:
            avg_probability = sum(p.churn_probability for p in recent_predictions) / len(recent_predictions)
            prediction_accuracy = model_info.get('metrics', {}).get('accuracy', 0.85) * 100
        else:
            avg_probability = 0
            prediction_accuracy = 85.0  # Default
        
        stats = {
            'total_customers': total_customers,
            'at_risk_customers': high_risk_count,
            'high_risk_customers': high_risk_count,
            'medium_risk_customers': medium_risk_count,
            'low_risk_customers': low_risk_count,
            'prediction_accuracy': prediction_accuracy,
            'avg_churn_probability': avg_probability * 100,
            'total_predictions': len(recent_predictions),
            'last_updated': recent_predictions[0].predicted_at.strftime('%Y-%m-%d %H:%M:%S') if recent_predictions else 'Never'
        }
        
        return render_template('prediction/dashboard.html', 
                             company=company, 
                             stats=stats,
                             model_info=model_info,
                             recent_predictions=recent_predictions[:10])
                             
    except Exception as e:
        logger.error(f"Error in prediction dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading the prediction dashboard.', 'error')
        return redirect(url_for('dashboard.index'))

@prediction_bp.route('/run-predictions', methods=['POST'])
@login_required
def run_predictions():
    """Run predictions for all customers in the company"""
    try:
        company = current_user.company
        if not company:
            return jsonify({'error': 'No company associated with account'}), 400
        
        # Get all customers
        customers = Customer.query.filter_by(company_id=company.id).all()
        
        if not customers:
            return jsonify({'error': 'No customers found. Please sync CRM data first.'}), 400
        
        # Initialize prediction service
        prediction_service = ChurnPredictionService()
        
        # Prepare customer data for prediction
        customers_data = []
        for customer in customers:
            customer_data = {
                'id': customer.id,
                'customer_id': customer.id,
                'tenure_months': customer.tenure_months or 0,
                'monthly_charges': customer.monthly_charges or 0,
                'total_charges': customer.total_charges or 0,
                'outstanding_balance': customer.outstanding_balance or 0,
                'total_tickets': customer.total_tickets or 0,
                'total_payments': customer.total_payments or 0,
                'service_type': customer.service_type,
                'connection_type': customer.connection_type,
                'account_type': customer.account_type,
                'status': customer.status
            }
            customers_data.append(customer_data)
        
        # Run batch predictions
        logger.info(f"Running predictions for {len(customers_data)} customers...")
        prediction_results = prediction_service.predict_batch(customers_data)
        
        # Save predictions to database and update customer records
        saved_count = 0
        updated_count = 0
        
        for result in prediction_results:
            try:
                customer_id = result['customer_id']
                customer = Customer.query.get(customer_id)
                
                if customer:
                    # Update customer's churn risk and probability
                    customer.churn_risk = result['churn_risk']
                    customer.churn_probability = result['churn_probability']
                    customer.last_prediction_date = datetime.utcnow()
                    updated_count += 1
                    
                    # Save prediction record
                    prediction = Prediction(
                        company_id=company.id,
                        customer_id=customer_id,
                        churn_probability=result['churn_probability'],
                        churn_risk=result['churn_risk'],
                        will_churn=result['will_churn'],
                        model_version=result.get('model_version'),
                        predicted_at=datetime.utcnow()
                    )
                    db.session.add(prediction)
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving prediction for customer {result.get('customer_id')}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        # Calculate summary statistics
        high_risk = sum(1 for r in prediction_results if r['churn_risk'] == 'high')
        medium_risk = sum(1 for r in prediction_results if r['churn_risk'] == 'medium')
        low_risk = sum(1 for r in prediction_results if r['churn_risk'] == 'low')
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(prediction_results)} predictions',
            'results': {
                'total_predictions': len(prediction_results),
                'customers_updated': updated_count,
                'predictions_saved': saved_count,
                'high_risk': high_risk,
                'medium_risk': medium_risk,
                'low_risk': low_risk,
                'prediction_method': prediction_results[0].get('prediction_method') if prediction_results else 'unknown'
            }
        })
        
    except Exception as e:
        logger.error(f"Error running predictions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to run predictions',
            'details': str(e)
        }), 500

@prediction_bp.route('/customer/<int:customer_id>')
@login_required
def customer_prediction(customer_id):
    """Show detailed prediction for a specific customer"""
    try:
        company = current_user.company
        customer = Customer.query.filter_by(
            id=customer_id, 
            company_id=company.id
        ).first()
        
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('prediction.dashboard'))
        
        # Get customer's prediction history
        predictions = Prediction.query.filter_by(
            customer_id=customer_id,
            company_id=company.id
        ).order_by(Prediction.predicted_at.desc()).limit(10).all()
        
        # Get the latest prediction or run a new one
        if predictions:
            latest_prediction = predictions[0]
        else:
            # Run prediction for this customer
            prediction_service = ChurnPredictionService()
            customer_data = {
                'id': customer.id,
                'customer_id': customer.id,
                'tenure_months': customer.tenure_months or 0,
                'monthly_charges': customer.monthly_charges or 0,
                'total_charges': customer.total_charges or 0,
                'outstanding_balance': customer.outstanding_balance or 0,
                'total_tickets': customer.total_tickets or 0,
                'total_payments': customer.total_payments or 0
            }
            
            result = prediction_service.predict_customer_churn(customer_data)
            
            # Create a temporary prediction object for display
            latest_prediction = type('obj', (object,), {
                'churn_probability': result['churn_probability'],
                'churn_risk': result['churn_risk'],
                'will_churn': result['will_churn'],
                'predicted_at': datetime.utcnow()
            })
            
            # Update customer record
            customer.churn_risk = result['churn_risk']
            customer.churn_probability = result['churn_probability']
            customer.last_prediction_date = datetime.utcnow()
            db.session.commit()
        
        return render_template('prediction/customer_detail.html',
                             customer=customer,
                             prediction=latest_prediction,
                             prediction_history=predictions)
        
    except Exception as e:
        logger.error(f"Error showing customer prediction: {str(e)}")
        flash('Error loading customer prediction', 'error')
        return redirect(url_for('prediction.dashboard'))

@prediction_bp.route('/high-risk')
@login_required
def high_risk_customers():
    """Show high-risk customers with real predictions"""
    try:
        company = current_user.company
        
        # Get high-risk customers with their latest predictions
        high_risk_customers = db.session.query(Customer, Prediction).join(
            Prediction, Customer.id == Prediction.customer_id
        ).filter(
            Customer.company_id == company.id,
            Prediction.churn_risk == 'high'
        ).order_by(Prediction.churn_probability.desc()).all()
        
        # If no predictions exist, suggest running predictions first
        if not high_risk_customers:
            flash('No high-risk predictions found. Run predictions first to identify at-risk customers.', 'info')
        
        return render_template('prediction/high_risk.html',
                             company=company,
                             high_risk_customers=high_risk_customers)
        
    except Exception as e:
        logger.error(f"Error loading high-risk customers: {str(e)}")
        flash('Error loading high-risk customers', 'error')
        return redirect(url_for('prediction.dashboard'))

@prediction_bp.route('/model-info')
@login_required
def model_info():
    """Get information about the current prediction model"""
    try:
        prediction_service = ChurnPredictionService()
        model_info = prediction_service.get_model_info()
        
        return jsonify({
            'success': True,
            'model_info': model_info
        })
        
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prediction_bp.route('/predict-single', methods=['POST'])
@login_required
def predict_single():
    """Predict churn for a single customer via API"""
    try:
        # Get customer data from request
        data = request.get_json() if request.is_json else request.form.to_dict()
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return jsonify({'error': 'customer_id required'}), 400
        
        # Get customer from database
        customer = Customer.query.filter_by(
            id=customer_id,
            company_id=current_user.company_id
        ).first()
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Prepare customer data
        customer_data = {
            'id': customer.id,
            'customer_id': customer.id,
            'tenure_months': customer.tenure_months or 0,
            'monthly_charges': customer.monthly_charges or 0,
            'total_charges': customer.total_charges or 0,
            'outstanding_balance': customer.outstanding_balance or 0,
            'total_tickets': customer.total_tickets or 0,
            'total_payments': customer.total_payments or 0
        }
        
        # Run prediction
        prediction_service = ChurnPredictionService()
        result = prediction_service.predict_customer_churn(customer_data)
        
        return jsonify({
            'success': True,
            'prediction': result
        })
        
    except Exception as e:
        logger.error(f"Error in single prediction: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Export the blueprint
__all__ = ['prediction_bp']