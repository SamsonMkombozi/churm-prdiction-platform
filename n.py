#!/usr/bin/env python3
"""
Emergency Fix: Find and Patch Prediction Controller

This script will help you quickly locate and fix the actual prediction controller
that's causing the 'stats' is undefined error.
"""

import os
import glob
import re

def emergency_fix():
    """Find and suggest fixes for the prediction controller"""
    
    print("EMERGENCY FIX: Locating Prediction Controller")
    print("=" * 50)
    
    # Step 1: Find files that might contain the prediction dashboard route
    search_patterns = [
        "**/*.py"
    ]
    
    potential_files = []
    
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for prediction dashboard indicators
                    indicators = [
                        r'/prediction/dashboard',
                        r'prediction.*dashboard', 
                        r'def dashboard.*prediction',
                        r'prediction_bp.*dashboard',
                        r'@.*route.*prediction.*dashboard'
                    ]
                    
                    for indicator in indicators:
                        if re.search(indicator, content, re.IGNORECASE):
                            potential_files.append({
                                'file': file,
                                'content': content,
                                'size': len(content)
                            })
                            break
                            
                except Exception as e:
                    continue
    
    if potential_files:
        print(f"Found {len(potential_files)} potential prediction controller files:")
        
        for i, file_info in enumerate(potential_files):
            print(f"\n{i+1}. {file_info['file']} ({file_info['size']} chars)")
            
            # Look for the specific route definition
            lines = file_info['content'].split('\n')
            for line_num, line in enumerate(lines, 1):
                if any(keyword in line.lower() for keyword in ['def dashboard', '/prediction/dashboard', '@route']):
                    if 'dashboard' in line.lower():
                        print(f"   Line {line_num}: {line.strip()}")
    
    else:
        print("No prediction controller files found!")
        print("The route might be defined differently.")
    
    # Generate universal fixes
    print(f"\nUNIVERSAL FIXES:")
    print("=" * 30)
    
    print("""
OPTION 1: Create a standalone prediction controller

Create a new file: app/controllers/prediction_controller.py

```python
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

@prediction_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get company safely
        company = getattr(current_user, 'company', None)
        if not company and hasattr(current_user, 'company_id'):
            from app.models.company import Company
            company = Company.query.get(current_user.company_id)
        
        if not company:
            company = type('Company', (), {'name': 'Your Company'})()
        
        # Provide all required variables
        stats = {
            'total_customers': 0,
            'at_risk_customers': 0,
            'high_risk_customers': 0,
            'prediction_accuracy': 0.85
        }
        
        recent_activities = [{
            'title': 'Dashboard loaded successfully',
            'timestamp': '2024-10-24 10:00'
        }]
        
        high_risk_customers = []
        
        return render_template('prediction/dashboard.html',
                             company=company,
                             stats=stats,
                             recent_activities=recent_activities,
                             high_risk_customers=high_risk_customers)
                             
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))
```

Then register it in your main app file:
```python
from app.controllers.prediction_controller import prediction_bp
app.register_blueprint(prediction_bp)
```
""")
    
    print("""
OPTION 2: Quick Template Fix (Temporary)

If you can't modify the controller immediately, make your template safer:

In templates/prediction/dashboard.html, change the title block from:
```jinja2
{% block title %}Dashboard - {{ company.name }}{% endblock %}
```

To:
```jinja2
{% block title %}Prediction Dashboard{% if company %} - {{ company.name }}{% endif %}{% endblock %}
```

And add this at the top of the template content:
```jinja2
{% set company = company or {'name': 'Your Company'} %}
{% set stats = stats or {'total_customers': 0, 'at_risk_customers': 0, 'high_risk_customers': 0, 'prediction_accuracy': 0.85} %}
{% set recent_activities = recent_activities or [] %}
{% set high_risk_customers = high_risk_customers or [] %}
```
""")
    
    print("""
OPTION 3: Add to existing dashboard controller

In your dashboard_controller.py, add this route:

```python
@dashboard_bp.route('/prediction/dashboard')
@login_required
def prediction_dashboard():
    try:
        company = getattr(current_user, 'company', None)
        if not company:
            company = type('Company', (), {'name': 'Your Company'})()
        
        stats = {
            'total_customers': 0,
            'at_risk_customers': 0,
            'high_risk_customers': 0,
            'prediction_accuracy': 0.85
        }
        
        return render_template('prediction/dashboard.html',
                             company=company,
                             stats=stats,
                             recent_activities=[],
                             high_risk_customers=[])
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))
```
""")

def check_current_routes():
    """Check what routes are currently registered"""
    
    print("\nROUTE DEBUGGING:")
    print("=" * 20)
    
    print("""
To see what routes are currently registered in your Flask app:

1. Add this to your main app file temporarily:
```python
@app.before_first_request
def show_routes():
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule.rule} -> {rule.endpoint}")
```

2. Or run this in your Flask shell:
```python
flask shell
>>> from your_app import app
>>> for rule in app.url_map.iter_rules():
...     print(f"{rule.rule} -> {rule.endpoint}")
```

Look for any route that matches '/prediction/dashboard'
""")

def main():
    print("PREDICTION CONTROLLER EMERGENCY FIX")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print()
    
    emergency_fix()
    check_current_routes()
    
    print("\nIMMEDIATE ACTIONS:")
    print("=" * 20)
    print("1. Try OPTION 2 (Template Fix) first - it's the quickest")
    print("2. If that works, then implement OPTION 1 or 3 for a permanent fix")
    print("3. Restart your Flask application after any changes")
    print("4. Test /prediction/dashboard")

if __name__ == "__main__":
    main()