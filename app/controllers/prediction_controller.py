"""
Prediction Controller with No Authentication for ML Testing
app/controllers/prediction_controller.py

Remove @login_required for testing the ML functionality
"""
from flask import Blueprint, request, jsonify, render_template
import logging

# Import services
from app.services.prediction_service import ChurnPredictionService

# Create blueprint
prediction_bp = Blueprint('prediction', __name__)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize prediction service
prediction_service = ChurnPredictionService()


@prediction_bp.route('/run-predictions', methods=['POST'])
def run_predictions():
    """
    Run batch predictions for customers
    No authentication required for testing
    """
    try:
        logger.info("🚀 Starting batch prediction process")
        
        # For testing, create some sample customers
        sample_customers = [
            {
                'id': 1,
                'tenure_months': 24,
                'monthly_charges': 75.0,
                'total_charges': 1800.0,
                'outstanding_balance': 50.0,
                'total_tickets': 1,
                'total_payments': 24
            },
            {
                'id': 2,
                'tenure_months': 3,
                'monthly_charges': 120.0,
                'total_charges': 360.0,
                'outstanding_balance': 240.0,
                'total_tickets': 5,
                'total_payments': 2
            },
            {
                'id': 3,
                'tenure_months': 12,
                'monthly_charges': 65.0,
                'total_charges': 780.0,
                'outstanding_balance': 0.0,
                'total_tickets': 0,
                'total_payments': 12
            },
            {
                'id': 4,
                'tenure_months': 6,
                'monthly_charges': 95.0,
                'total_charges': 570.0,
                'outstanding_balance': 190.0,
                'total_tickets': 3,
                'total_payments': 5
            },
            {
                'id': 5,
                'tenure_months': 18,
                'monthly_charges': 55.0,
                'total_charges': 990.0,
                'outstanding_balance': 0.0,
                'total_tickets': 1,
                'total_payments': 18
            }
        ]
        
        # Run batch prediction
        results = prediction_service.predict_batch(sample_customers)
        
        # Log results
        logger.info(f"✅ Processed {len(results)} customers")
        for result in results:
            logger.info(f"Customer {result['customer_id']}: {result['churn_risk']} risk ({result['churn_probability']:.3f})")
        
        # Save to database (optional - may fail if models don't exist)
        saved_count = 0
        try:
            from app.models.prediction import Prediction
            from app.extensions import db
            
            for result in results:
                # Try to save to database
                try:
                    prediction = Prediction.create_prediction(
                        company_id=1,  # Default company for testing
                        customer_id=result['customer_id'],
                        prediction_result=result
                    )
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Could not save prediction for customer {result['customer_id']}: {e}")
        except Exception as e:
            logger.warning(f"Database operations not available: {e}")
        
        # Return success response
        response = {
            'status': 'success',
            'message': 'Batch prediction completed successfully',
            'predictions_processed': len(results),
            'predictions_saved': saved_count,
            'results': [
                {
                    'customer_id': r['customer_id'],
                    'churn_risk': r['churn_risk'],
                    'churn_probability': round(r['churn_probability'], 3),
                    'confidence': r['confidence']
                }
                for r in results
            ]
        }
        
        logger.info("✅ Batch prediction completed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Batch prediction failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}'
        }), 500


@prediction_bp.route('/predict', methods=['POST'])
def predict_single():
    """
    Predict churn for a single customer
    No authentication required for testing
    """
    try:
        # Get customer data from request
        customer_data = request.get_json()
        
        if not customer_data:
            return jsonify({
                'status': 'error',
                'message': 'No customer data provided'
            }), 400
        
        # Make prediction
        result = prediction_service.predict_customer_churn(customer_data)
        
        logger.info(f"✅ Prediction for customer {customer_data.get('id', 'unknown')}: {result['churn_risk']} risk")
        
        return jsonify({
            'status': 'success',
            'result': {
                'customer_id': result['customer_id'],
                'churn_risk': result['churn_risk'],
                'churn_probability': round(result['churn_probability'], 3),
                'confidence': result['confidence'],
                'risk_factors': result['risk_factors']
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Single prediction failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}'
        }), 500


@prediction_bp.route('/model-info', methods=['GET'])
def model_info():
    """
    Get information about the loaded ML model
    No authentication required for testing
    """
    try:
        info = prediction_service.get_model_info()
        
        return jsonify({
            'status': 'success',
            'model_info': info
        })
        
    except Exception as e:
        logger.error(f"❌ Model info request failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Model info request failed: {str(e)}'
        }), 500


@prediction_bp.route('/dashboard')
def dashboard():
    """
    Simple prediction dashboard
    No authentication required for testing
    """
    try:
        # Get model info
        model_info = prediction_service.get_model_info()
        
        return render_template('prediction/dashboard.html', 
                             model_info=model_info)
        
    except Exception as e:
        logger.error(f"❌ Dashboard request failed: {str(e)}")
        return f"Dashboard error: {str(e)}"


@prediction_bp.route('/test')
def test_endpoint():
    """Test endpoint to verify the controller is working"""
    return jsonify({
        'status': 'ok',
        'message': 'Prediction controller is working!',
        'model_loaded': prediction_service.is_trained,
        'model_type': prediction_service.model_type
    })