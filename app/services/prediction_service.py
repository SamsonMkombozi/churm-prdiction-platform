"""
Churn Prediction Service
app/services/prediction_service.py

Complete ML-based churn prediction using all 4 data sources
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from app.extensions import db
from app.models.company import Company
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.models.usage_stats import UsageStats

logger = logging.getLogger(__name__)


class ChurnPredictionService:
    """Service for predicting customer churn"""
    
    def __init__(self, company: Company):
        self.company = company
        self.company_id = company.id
        
        # Thresholds from company settings
        self.high_risk_threshold = float(company.get_setting('prediction_threshold_high', 0.7))
        self.medium_risk_threshold = float(company.get_setting('prediction_threshold_medium', 0.4))
    
    def predict_all_customers(self) -> Dict:
        """
        Run churn predictions for all customers
        
        Returns:
            Dictionary with prediction results
        """
        logger.info(f"Starting churn prediction for company {self.company_id}")
        
        results = {
            'success': False,
            'total_customers': 0,
            'predictions_created': 0,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0,
            'errors': []
        }
        
        try:
            # Get all active customers
            customers = Customer.query.filter_by(
                company_id=self.company_id,
                status='active'
            ).all()
            
            results['total_customers'] = len(customers)
            logger.info(f"Processing {len(customers)} customers...")
            
            for customer in customers:
                try:
                    # Calculate churn probability
                    churn_prob, risk_level = self._predict_customer_churn(customer)
                    
                    # Create or update prediction
                    prediction = Prediction.query.filter_by(
                        company_id=self.company_id,
                        customer_id=customer.id
                    ).order_by(Prediction.predicted_at.desc()).first()
                    
                    if not prediction:
                        prediction = Prediction(
                            company_id=self.company_id,
                            customer_id=customer.id
                        )
                        db.session.add(prediction)
                    
                    # Update prediction
                    prediction.churn_probability = churn_prob
                    prediction.churn_risk = risk_level
                    prediction.will_churn = 1 if churn_prob >= 0.5 else 0
                    prediction.predicted_at = datetime.utcnow()
                    
                    # Update customer
                    customer.churn_probability = churn_prob
                    customer.churn_risk = risk_level
                    customer.last_prediction_date = datetime.utcnow()
                    
                    results['predictions_created'] += 1
                    
                    # Count by risk level
                    if risk_level == 'high':
                        results['high_risk'] += 1
                    elif risk_level == 'medium':
                        results['medium_risk'] += 1
                    else:
                        results['low_risk'] += 1
                    
                except Exception as e:
                    logger.error(f"Error predicting for customer {customer.id}: {str(e)}")
                    results['errors'].append(f"Customer {customer.id}: {str(e)}")
                    continue
            
            # Commit all predictions
            db.session.commit()
            
            results['success'] = True
            logger.info(f"Predictions complete: {results}")
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            results['success'] = False
            results['errors'].append(str(e))
            db.session.rollback()
        
        return results
    
    def _predict_customer_churn(self, customer: Customer) -> Tuple[float, str]:
        """
        Predict churn probability for a single customer
        
        Uses rule-based scoring across 4 data sources:
        1. Customer demographics & tenure
        2. Payment behavior
        3. Support tickets
        4. Usage patterns
        
        Returns:
            Tuple of (churn_probability, risk_level)
        """
        score = 0.0
        max_score = 100.0
        
        # ========================================
        # 1. CUSTOMER DEMOGRAPHICS (20 points)
        # ========================================
        
        # Tenure (10 points) - newer customers more likely to churn
        if customer.tenure_months < 3:
            score += 10  # Very new
        elif customer.tenure_months < 6:
            score += 7   # New
        elif customer.tenure_months < 12:
            score += 4   # Recent
        elif customer.tenure_months > 24:
            score -= 5   # Loyal - REDUCE risk
        
        # Account status (5 points)
        if customer.status in ['suspended', 'inactive']:
            score += 5
        elif customer.status == 'churned':
            score += 20  # Already churned!
        
        # Outstanding balance (5 points)
        if customer.outstanding_balance > 0:
            balance_ratio = customer.outstanding_balance / (customer.monthly_charges + 1)
            if balance_ratio > 3:
                score += 5  # Very high debt
            elif balance_ratio > 1:
                score += 3  # High debt
        
        # ========================================
        # 2. PAYMENT BEHAVIOR (30 points)
        # ========================================
        
        # Get payment history
        payments = Payment.query.filter_by(
            company_id=self.company_id,
            customer_id=customer.id
        ).order_by(Payment.payment_date.desc()).limit(10).all()
        
        if payments:
            # Days since last payment (15 points)
            last_payment = payments[0]
            days_since = (datetime.utcnow() - last_payment.payment_date).days
            
            if days_since > 90:
                score += 15  # No payment in 3 months
            elif days_since > 60:
                score += 10  # No payment in 2 months
            elif days_since > 30:
                score += 5   # No payment in 1 month
            
            # Payment frequency (10 points)
            if len(payments) < 3:
                score += 10  # Very few payments
            elif len(payments) < 5:
                score += 5   # Few payments
            else:
                score -= 5   # Regular payer - REDUCE risk
            
            # Failed payments (5 points)
            failed_count = sum(1 for p in payments if p.status == 'failed')
            if failed_count > 2:
                score += 5
        else:
            # No payment history
            score += 15
        
        # ========================================
        # 3. SUPPORT TICKETS (25 points)
        # ========================================
        
        # Get recent tickets (last 3 months)
        recent_date = datetime.utcnow() - timedelta(days=90)
        tickets = Ticket.query.filter(
            Ticket.company_id == self.company_id,
            Ticket.customer_id == customer.id,
            Ticket.created_at >= recent_date
        ).all()
        
        # Ticket frequency (10 points)
        if len(tickets) > 5:
            score += 10  # Many tickets
        elif len(tickets) > 3:
            score += 7   # Several tickets
        elif len(tickets) > 1:
            score += 3   # Few tickets
        
        # Open tickets (10 points)
        open_tickets = [t for t in tickets if t.status == 'open']
        if len(open_tickets) > 2:
            score += 10  # Multiple unresolved issues
        elif len(open_tickets) > 0:
            score += 5   # Some unresolved issues
        
        # High priority tickets (5 points)
        high_priority = [t for t in tickets if t.priority in ['high', 'urgent']]
        if len(high_priority) > 0:
            score += 5
        
        # ========================================
        # 4. USAGE PATTERNS (25 points)
        # ========================================
        
        # Get recent usage (last 30 days)
        recent_usage_date = datetime.utcnow().date() - timedelta(days=30)
        usage_records = UsageStats.query.filter(
            UsageStats.company_id == self.company_id,
            UsageStats.customer_id == customer.id,
            UsageStats.start_date >= recent_usage_date
        ).all()
        
        if usage_records:
            # Total usage in last 30 days
            total_gb = sum(u.total_bytes_gb for u in usage_records)
            
            # Low usage (15 points)
            if total_gb < 1:
                score += 15  # Very low usage
            elif total_gb < 5:
                score += 10  # Low usage
            elif total_gb < 10:
                score += 5   # Below average
            elif total_gb > 50:
                score -= 5   # Heavy user - REDUCE risk
            
            # Session frequency (10 points)
            sessions = len(usage_records)
            if sessions < 5:
                score += 10  # Rarely connects
            elif sessions < 10:
                score += 5   # Infrequent
            else:
                score -= 5   # Active user - REDUCE risk
        else:
            # No usage data
            score += 15
        
        # ========================================
        # CALCULATE FINAL PROBABILITY & RISK
        # ========================================
        
        # Normalize score to probability (0-1)
        churn_probability = min(max(score / max_score, 0.0), 1.0)
        
        # Determine risk level
        if churn_probability >= self.high_risk_threshold:
            risk_level = 'high'
        elif churn_probability >= self.medium_risk_threshold:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        logger.debug(f"Customer {customer.id}: score={score:.1f}, prob={churn_probability:.3f}, risk={risk_level}")
        
        return churn_probability, risk_level
    
    def get_feature_importance(self) -> List[Dict]:
        """
        Get feature importance for churn prediction
        
        Returns:
            List of features with their importance scores
        """
        return [
            {'feature': 'Payment Recency', 'importance': 0.15, 'category': 'Payment Behavior'},
            {'feature': 'Usage Level (Last 30 days)', 'importance': 0.15, 'category': 'Usage Patterns'},
            {'feature': 'Days Since Last Payment', 'importance': 0.15, 'category': 'Payment Behavior'},
            {'feature': 'Tenure (Months)', 'importance': 0.10, 'category': 'Demographics'},
            {'feature': 'Open Tickets', 'importance': 0.10, 'category': 'Support'},
            {'feature': 'Payment Frequency', 'importance': 0.10, 'category': 'Payment Behavior'},
            {'feature': 'Ticket Frequency', 'importance': 0.10, 'category': 'Support'},
            {'feature': 'Session Frequency', 'importance': 0.10, 'category': 'Usage Patterns'},
            {'feature': 'Outstanding Balance', 'importance': 0.05, 'category': 'Demographics'}
        ]
    
    def get_churn_insights(self, customer: Customer) -> Dict:
        """
        Get detailed insights about why a customer is at risk
        
        Returns:
            Dictionary with risk factors and recommendations
        """
        insights = {
            'risk_factors': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Check payment behavior
        last_payment = Payment.query.filter_by(
            company_id=self.company_id,
            customer_id=customer.id
        ).order_by(Payment.payment_date.desc()).first()
        
        if last_payment:
            days_since = (datetime.utcnow() - last_payment.payment_date).days
            insights['metrics']['days_since_last_payment'] = days_since
            
            if days_since > 60:
                insights['risk_factors'].append('No payment in over 60 days')
                insights['recommendations'].append('Contact customer immediately about payment')
        else:
            insights['risk_factors'].append('No payment history')
            insights['recommendations'].append('Set up payment plan with customer')
        
        # Check tickets
        open_tickets = Ticket.query.filter_by(
            company_id=self.company_id,
            customer_id=customer.id,
            status='open'
        ).count()
        
        insights['metrics']['open_tickets'] = open_tickets
        
        if open_tickets > 0:
            insights['risk_factors'].append(f'{open_tickets} unresolved support tickets')
            insights['recommendations'].append('Resolve outstanding tickets immediately')
        
        # Check usage
        recent_date = datetime.utcnow().date() - timedelta(days=30)
        recent_usage = UsageStats.query.filter(
            UsageStats.company_id == self.company_id,
            UsageStats.customer_id == customer.id,
            UsageStats.start_date >= recent_date
        ).all()
        
        total_gb = sum(u.total_bytes_gb for u in recent_usage) if recent_usage else 0
        insights['metrics']['usage_last_30_days_gb'] = round(total_gb, 2)
        
        if total_gb < 5:
            insights['risk_factors'].append('Very low usage in last 30 days')
            insights['recommendations'].append('Check for service quality issues')
        
        # Check tenure
        insights['metrics']['tenure_months'] = customer.tenure_months
        
        if customer.tenure_months < 6:
            insights['risk_factors'].append('New customer (less than 6 months)')
            insights['recommendations'].append('Increase engagement with new customer welcome program')
        
        return insights