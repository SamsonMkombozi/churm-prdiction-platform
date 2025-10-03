"""
Fixed Authentication Controller with Proper Logout
app/controllers/auth_controller.py
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user, logout_user, login_required
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        success, message, user = AuthService.login_user_service(
            email, password, remember
        )
        
        if success:
            flash(message, 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard.index'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        success, message, user = AuthService.register_user(
            email, password, full_name, company_name
        )
        
        if success:
            flash(f'{message} Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Logout user - properly sign out
    Clears session and logs out user
    """
    # Get user name before logout for the message
    user_name = current_user.full_name if hasattr(current_user, 'full_name') else 'User'
    
    # Logout the user (Flask-Login)
    logout_user()
    
    # Clear the session completely
    session.clear()
    
    # Flash success message
    flash(f'Goodbye {user_name}! You have been successfully logged out.', 'success')
    
    # Redirect to login page
    return redirect(url_for('auth.login'))