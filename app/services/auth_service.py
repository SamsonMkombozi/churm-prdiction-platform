"""
Fixed Authentication Service
app/services/auth_service.py

✅ FIXED: Import db from extensions, not from app
"""

from app.extensions import db  # ✅ FIXED: Import from extensions
from app.models.user import User
from app.models.company import Company
from flask_login import login_user, logout_user
import re

class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def register_user(email, password, full_name, company_name=None):
        """
        Register a new user and optionally create a company
        Returns: (success: bool, message: str, user: User)
        """
        # Validate input
        if not email or not password or not full_name:
            return False, "Email, password, and full name are required", None
        
        # Validate email format
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return False, "Invalid email format", None
        
        # Validate password strength
        if len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        # Check if email exists
        if User.query.filter_by(email=email.lower()).first():
            return False, "Email already registered", None
        
        try:
            # If company name provided, create company first
            company = None
            if company_name:
                # Check if company exists
                existing_company = Company.query.filter_by(name=company_name).first()
                if existing_company:
                    return False, "Company name already exists", None
                
                # Create company
                try:
                    from slugify import slugify
                    slug = slugify(company_name)
                except ImportError:
                    # If slugify not available, create simple slug
                    import re
                    slug = re.sub(r'[^\w\s-]', '', company_name.lower())
                    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
                
                company = Company(
                    name=company_name,
                    slug=slug,
                    is_active=True
                )
                db.session.add(company)
                db.session.flush()  # Get company.id without committing
            
            # Create new user
            user = User(
                email=email.lower(),
                full_name=full_name,
                company_id=company.id if company else None,
                role='admin' if company else 'viewer',  # First user in company is admin
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return True, "Registration successful", user
        
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    @staticmethod
    def login_user_service(username_or_email, password, remember=False):
        """
        Authenticate user and create session
        username_or_email: Can be either username or email (we only use email now)
        Returns: (success: bool, message: str, user: User)
        """
        if not username_or_email or not password:
            return False, "Email and password are required", None
        
        # Find user by email (case-insensitive)
        user = User.query.filter(
            User.email == username_or_email.lower()
        ).first()
        
        if not user:
            return False, "Invalid email or password", None
        
        if not user.is_active:
            return False, "Account is disabled. Please contact your administrator.", None
        
        # Check if user's company is active (if they have one)
        if user.company and not user.company.is_active:
            return False, "Your company account is inactive. Please contact support.", None
        
        if not user.check_password(password):
            return False, "Invalid email or password", None
        
        # Log in user
        login_user(user, remember=remember)
        user.update_last_login()
        
        return True, "Login successful", user
    
    @staticmethod
    def logout_user_service():
        """Logout current user"""
        logout_user()
        return True, "Logged out successfully"
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """
        Change user password
        Returns: (success: bool, message: str)
        """
        if not user.check_password(old_password):
            return False, "Current password is incorrect"
        
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"
        
        try:
            user.set_password(new_password)
            db.session.commit()
            return True, "Password changed successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to change password: {str(e)}"