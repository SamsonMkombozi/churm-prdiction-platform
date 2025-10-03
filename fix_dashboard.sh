#!/bin/bash
# Script to replace dashboard_controller.py

cat > app/controllers/dashboard_controller.py << 'EOF'
"""
Dashboard Controller - Fixed Version
app/controllers/dashboard_controller.py
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    """Main dashboard - with company context"""
    # Get company from current user
    company = current_user.company
    
    # Get basic stats (these methods are safe)
    stats = {
        'total_customers': company.get_customer_count(),
        'total_tickets': company.get_ticket_count(),
        'total_payments': company.get_payment_count(),
        'high_risk_customers': company.get_high_risk_customer_count(),
        'active_users': company.get_active_user_count(),
    }
    
    # Pass company and stats to template
    return render_template('dashboard/index.html', company=company, stats=stats)


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    company = current_user.company
    return render_template('dashboard/analytics.html', company=company)
EOF

echo "✅ Dashboard controller updated!"
echo "Now restart your Flask app: python3 run.py"
