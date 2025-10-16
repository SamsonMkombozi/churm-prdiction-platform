#!/usr/bin/env python3
"""
Template Diagnostic Script
Run this to check template configuration
"""

import os
import sys

def check_template_structure():
    """Check if template files exist"""
    print("🔍 Checking template structure...")
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check templates directory
    templates_dir = os.path.join(current_dir, 'templates')
    print(f"📁 Templates directory: {templates_dir}")
    print(f"✅ Templates directory exists: {os.path.exists(templates_dir)}")
    
    if os.path.exists(templates_dir):
        print("\n📋 Template files found:")
        for root, dirs, files in os.walk(templates_dir):
            level = root.replace(templates_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith('.html'):
                    print(f"{subindent}{file}")
    
    # Check specific files
    required_templates = [
        'templates/base.html',
        'templates/dashboard/index.html',
        'templates/auth/login.html',
        'templates/company/index.html'
    ]
    
    print("\n🎯 Checking required templates:")
    for template in required_templates:
        full_path = os.path.join(current_dir, template)
        exists = os.path.exists(full_path)
        print(f"{'✅' if exists else '❌'} {template}")
        if not exists and 'dashboard/index.html' in template:
            # Try to create the missing dashboard template
            dashboard_dir = os.path.join(current_dir, 'templates', 'dashboard')
            os.makedirs(dashboard_dir, exist_ok=True)
            print(f"📁 Created dashboard directory: {dashboard_dir}")

def create_minimal_dashboard_template():
    """Create a minimal dashboard template if it doesn't exist"""
    templates_dir = os.path.join(os.getcwd(), 'templates')
    dashboard_dir = os.path.join(templates_dir, 'dashboard')
    dashboard_file = os.path.join(dashboard_dir, 'index.html')
    
    if not os.path.exists(dashboard_file):
        os.makedirs(dashboard_dir, exist_ok=True)
        
        minimal_template = '''{% extends 'base.html' %}

{% block title %}Dashboard - {{ company.name }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <h1 class="h2">
        <i class="fas fa-tachometer-alt me-2"></i>Dashboard
    </h1>
    
    <div class="row">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Total Customers</h5>
                    <h3>{{ stats.total_customers or 0 }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>High Risk</h5>
                    <h3>{{ stats.high_risk_customers or 0 }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Tickets</h5>
                    <h3>{{ stats.total_tickets or 0 }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Payments</h5>
                    <h3>{{ stats.total_payments or 0 }}</h3>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Quick Actions</h5>
                </div>
                <div class="card-body">
                    <a href="{{ url_for('crm.dashboard') }}" class="btn btn-primary me-2">
                        <i class="fas fa-sync me-2"></i>CRM Dashboard
                    </a>
                    <a href="{{ url_for('crm.customers') }}" class="btn btn-success me-2">
                        <i class="fas fa-users me-2"></i>View Customers
                    </a>
                    <a href="{{ url_for('company.settings') }}" class="btn btn-info">
                        <i class="fas fa-cog me-2"></i>Settings
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        with open(dashboard_file, 'w') as f:
            f.write(minimal_template)
        
        print(f"✅ Created minimal dashboard template: {dashboard_file}")
        return True
    
    return False

def main():
    print("🚀 Template Diagnostic Tool")
    print("=" * 50)
    
    check_template_structure()
    
    print("\n🔧 Attempting to fix missing templates...")
    if create_minimal_dashboard_template():
        print("✅ Dashboard template created successfully")
    else:
        print("ℹ️  Dashboard template already exists")
    
    print("\n✅ Diagnostic complete. Try running your Flask app now.")

if __name__ == '__main__':
    main()