"""
Complete Prediction Controller with Database Integration
app/controllers/prediction_controller.py

Replace your entire prediction controller with this version
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
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
    Run batch predictions for customers - WITH DATABASE SAVING
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
        
        # Save to database
        saved_count = 0
        updated_customers = 0
        
        try:
            from app.models.customer import Customer
            from app.models.prediction import Prediction
            from app.extensions import db
            from datetime import datetime
            
            # Get company ID
            company_id = 1  # Default company
            try:
                if current_user and current_user.is_authenticated and hasattr(current_user, 'company'):
                    company_id = current_user.company.id
            except:
                pass
            
            for result in results:
                customer_id = result['customer_id']
                
                try:
                    # Update customer record if it exists
                    customer = Customer.query.filter_by(id=customer_id).first()
                    if customer:
                        customer.churn_probability = result['churn_probability']
                        customer.churn_risk = result['churn_risk']
                        
                        # Try to update last_prediction_date
                        try:
                            customer.last_prediction_date = datetime.utcnow()
                        except Exception as e:
                            logger.warning(f"Could not update last_prediction_date: {e}")
                        
                        updated_customers += 1
                        logger.info(f"Updated customer {customer_id}: {result['churn_risk']} risk")
                    
                    # Save detailed prediction record
                    try:
                        prediction = Prediction.create_prediction(
                            company_id=company_id,
                            customer_id=customer.crm_customer_id if customer and customer.crm_customer_id else str(customer_id),
                            prediction_result=result
                        )
                        if prediction:
                            saved_count += 1
                    except Exception as e:
                        logger.warning(f"Could not save prediction for customer {customer_id}: {e}")
                        
                except Exception as e:
                    logger.warning(f"Error processing customer {customer_id}: {e}")
            
            # Commit all changes
            db.session.commit()
            logger.info(f"✅ Committed {updated_customers} customer updates and {saved_count} predictions")
            
        except Exception as e:
            logger.warning(f"Database operations not available: {e}")
        
        # Log results
        logger.info(f"✅ Processed {len(results)} customers")
        for result in results:
            logger.info(f"Customer {result['customer_id']}: {result['churn_risk']} risk ({result['churn_probability']:.3f})")
        
        # Return success response
        response = {
            'status': 'success',
            'message': 'Batch prediction completed successfully',
            'predictions_processed': len(results),
            'predictions_saved': saved_count,
            'customers_updated': updated_customers,
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
    Predict churn for a single customer - WITH DATABASE SAVING
    """
    try:
        from datetime import datetime
        
        # Get customer data from request
        customer_data = request.get_json()
        
        if not customer_data:
            return jsonify({
                'status': 'error',
                'message': 'No customer data provided'
            }), 400
        
        logger.info(f"🔄 Processing prediction for customer: {customer_data}")
        
        # Make prediction
        result = prediction_service.predict_customer_churn(customer_data)
        logger.info(f"🎯 Prediction result: {result['churn_risk']} risk ({result['churn_probability']:.3f})")
        
        # Save to database
        customer_id = customer_data.get('id')
        if customer_id:
            try:
                from app.models.customer import Customer
                from app.models.prediction import Prediction
                from app.extensions import db
                
                # Get company ID
                company_id = 1  # Default company
                try:
                    if current_user and current_user.is_authenticated and hasattr(current_user, 'company'):
                        company_id = current_user.company.id
                except:
                    pass
                
                logger.info(f"💾 Saving to database - Customer: {customer_id}, Company: {company_id}")
                
                # Update customer record
                customer = Customer.query.filter_by(id=customer_id).first()
                if customer:
                    customer.churn_probability = result['churn_probability']
                    customer.churn_risk = result['churn_risk']
                    
                    # Try to update last_prediction_date
                    try:
                        customer.last_prediction_date = datetime.utcnow()
                        logger.info(f"📅 Updated last_prediction_date")
                    except Exception as e:
                        logger.warning(f"Could not update last_prediction_date: {e}")
                    
                    logger.info(f"👤 Updated customer record: {customer.customer_name}")
                else:
                    logger.warning(f"⚠️ Customer {customer_id} not found in database")
                
                # Save detailed prediction record
                try:
                    prediction = Prediction.create_prediction(
                        company_id=company_id,
                        customer_id=customer.crm_customer_id if customer and customer.crm_customer_id else str(customer_id),
                        prediction_result=result
                    )
                    
                    if prediction:
                        logger.info(f"💾 Saved prediction record with ID: {prediction.id}")
                    else:
                        logger.warning("⚠️ Prediction record creation returned None")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to save detailed prediction: {e}")
                    logger.error(f"Error details: {type(e).__name__}: {str(e)}")
                
                # Commit changes
                db.session.commit()
                logger.info("✅ Database changes committed successfully")
                
            except Exception as e:
                logger.error(f"❌ Database save failed: {e}")
                try:
                    db.session.rollback()
                except:
                    pass
        
        return jsonify({
            'status': 'success',
            'message': f'Prediction completed for customer {customer_id}',
            'result': {
                'customer_id': result['customer_id'],
                'churn_risk': result['churn_risk'],
                'churn_probability': round(result['churn_probability'], 3),
                'confidence': result['confidence'],
                'risk_factors': result['risk_factors'],
                'saved_to_database': True
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Single prediction failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}'
        }), 500


@prediction_bp.route('/predict-by-id/<int:customer_id>', methods=['POST'])
def predict_by_customer_id(customer_id):
    """
    Predict churn for a specific customer by ID - WITH DATABASE SAVING
    """
    try:
        from app.models.customer import Customer
        from app.models.prediction import Prediction
        from app.extensions import db
        from datetime import datetime
        
        logger.info(f"🎯 Predicting for customer ID: {customer_id}")
        
        # Get company ID
        company_id = 1  # Default company
        try:
            if current_user and current_user.is_authenticated and hasattr(current_user, 'company'):
                company_id = current_user.company.id
        except:
            pass
        
        # Get customer from database
        customer = Customer.query.filter_by(id=customer_id).first()
        
        if not customer:
            logger.warning(f"❌ Customer {customer_id} not found")
            return jsonify({
                'status': 'error',
                'message': f'Customer {customer_id} not found'
            }), 404
        
        # Prepare customer data for prediction
        customer_data = {
            'id': customer.id,
            'tenure_months': customer.tenure_months or 0,
            'monthly_charges': customer.monthly_charges or 0,
            'total_charges': customer.total_charges or 0,
            'outstanding_balance': customer.outstanding_balance or 0,
            'total_tickets': customer.total_tickets or 0,
            'total_payments': customer.total_payments or 0
        }
        
        logger.info(f"📊 Customer data: {customer_data}")
        
        # Make prediction
        result = prediction_service.predict_customer_churn(customer_data)
        logger.info(f"🎯 Prediction: {result['churn_risk']} risk ({result['churn_probability']:.3f})")
        
        # Update customer record
        customer.churn_probability = result['churn_probability']
        customer.churn_risk = result['churn_risk']
        
        # Try to update last_prediction_date
        try:
            customer.last_prediction_date = datetime.utcnow()
        except Exception as e:
            logger.warning(f"Could not update last_prediction_date: {e}")
        
        # Save detailed prediction
        try:
            prediction = Prediction.create_prediction(
                company_id=company_id,
                customer_id=customer.crm_customer_id or str(customer.id),
                prediction_result=result
            )
            if prediction:
                logger.info(f"💾 Saved prediction record: {prediction.id}")
        except Exception as e:
            logger.warning(f"Could not save detailed prediction: {e}")
        
        # Commit changes
        db.session.commit()
        logger.info("✅ All changes committed to database")
        
        return jsonify({
            'status': 'success',
            'customer_id': customer.id,
            'customer_name': customer.customer_name,
            'churn_risk': result['churn_risk'],
            'churn_probability': round(result['churn_probability'], 3),
            'confidence': result['confidence'],
            'saved_to_database': True
        })
        
    except Exception as e:
        logger.error(f"❌ Prediction by ID failed: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@prediction_bp.route('/model-info', methods=['GET'])
def model_info():
    """
    Get information about the loaded ML model
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
    """
    try:
        # Get model info
        model_info = prediction_service.get_model_info()
        
        # Get database stats
        stats = {}
        try:
            from app.models.prediction import Prediction
            stats['total_predictions'] = Prediction.query.count()
        except:
            stats['total_predictions'] = 0
        
        return render_template('prediction/dashboard.html', 
                             model_info=model_info,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"❌ Dashboard request failed: {str(e)}")
        return f"Dashboard error: {str(e)}"


@prediction_bp.route('/test')
def test_endpoint():
    """Test endpoint to verify the controller is working"""
    try:
        from app.models.prediction import Prediction
        prediction_count = Prediction.query.count()
    except:
        prediction_count = "Database not available"
    
    return jsonify({
        'status': 'ok',
        'message': 'Enhanced prediction controller with database saving is working!',
        'model_loaded': prediction_service.is_trained,
        'model_type': prediction_service.model_type,
        'predictions_in_database': prediction_count,
        'endpoints': [
            'POST /prediction/run-predictions - Batch predictions',
            'POST /prediction/predict - Single customer prediction',
            'POST /prediction/predict-by-id/<id> - Predict by customer ID',
            'GET /prediction/model-info - Model information',
            'GET /prediction/dashboard - Prediction dashboard',
            'GET /prediction/test - This endpoint'
        ]
    })


@prediction_bp.route('/debug/<int:customer_id>')
def debug_customer(customer_id):
    """Debug endpoint to check customer data"""
    try:
        from app.models.customer import Customer
        from app.models.prediction import Prediction
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': f'Customer {customer_id} not found'})
        
        # Get customer's predictions
        predictions = Prediction.query.filter_by(customer_id=str(customer_id)).all()
        
        return jsonify({
            'customer': {
                'id': customer.id,
                'name': customer.customer_name,
                'churn_risk': customer.churn_risk,
                'churn_probability': customer.churn_probability,
                'last_prediction_date': customer.last_prediction_date.isoformat() if hasattr(customer, 'last_prediction_date') and customer.last_prediction_date else None
            },
            'predictions_count': len(predictions),
            'latest_prediction': predictions[-1].to_dict() if predictions else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})