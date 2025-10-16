# app/controllers/prediction_controller.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
import traceback
from datetime import datetime
import logging

# Import the correct service name - should match your actual service class
try:
    from app.services.prediction_service import ChurnPredictionService  # Changed from PredictionService
except ImportError:
    # Fallback if service doesn't exist yet
    ChurnPredictionService = None

from app.models.company import Company
from app.models.customer import Customer

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
    """Prediction dashboard"""
    try:
        # Get company data
        company = None
        total_customers = 0
        at_risk_customers = 0
        prediction_accuracy = 0.0
        
        if current_user.company_id:
            company = Company.query.get(current_user.company_id)
            if company:
                total_customers = Customer.query.filter_by(company_id=company.id).count()
                # For now, simulate some stats - replace with actual calculations
                at_risk_customers = int(total_customers * 0.15)  # Assume 15% at risk
                prediction_accuracy = 85.2  # Placeholder accuracy
        
        stats = {
            'total_customers': total_customers,
            'at_risk_customers': at_risk_customers,
            'prediction_accuracy': prediction_accuracy,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('prediction/dashboard.html', 
                             company=company, 
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"Error in prediction dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading the prediction dashboard.', 'error')
        return redirect(url_for('dashboard.index'))

@prediction_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Handle prediction requests"""
    try:
        if not ChurnPredictionService:
            return jsonify({
                'error': 'Prediction service not available'
            }), 503
            
        # Get form data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Initialize prediction service
        service = ChurnPredictionService()
        
        # Perform prediction (placeholder logic)
        prediction_result = {
            'customer_id': data.get('customer_id'),
            'churn_probability': 0.25,  # Placeholder
            'risk_level': 'Medium',
            'prediction_date': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'prediction': prediction_result
        })
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({
            'error': 'Prediction failed',
            'details': str(e)
        }), 500

@prediction_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle CSV upload for batch predictions"""
    try:
        if request.method == 'GET':
            return render_template('prediction/upload.html')
            
        # Handle file upload
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV file
                df = pd.read_csv(file)
                
                # Validate CSV structure (add your validation logic here)
                required_columns = ['customer_id']  # Define required columns
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                    return redirect(request.url)
                
                # Process predictions (placeholder)
                results = []
                for _, row in df.iterrows():
                    results.append({
                        'customer_id': row['customer_id'],
                        'churn_probability': 0.25,  # Placeholder
                        'risk_level': 'Medium'
                    })
                
                flash(f'Successfully processed {len(results)} predictions', 'success')
                return render_template('prediction/results.html', results=results)
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Please upload a CSV file', 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Error in upload: {str(e)}")
        flash('An error occurred during upload.', 'error')
        return redirect(url_for('prediction.upload'))

# Export the blueprint for import
__all__ = ['prediction_bp']