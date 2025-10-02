from app import db
from app.models.user import User
from flask_login import login_user, logout_user
import re

class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def register_user(username, email, password, full_name=None):
        """
        Register a new user
        Returns: (success: bool, message: str, user: User)
        """
        # Validate input
        if not username or not email or not password:
            return False, "All fields are required", None
        
        # Validate email format
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return False, "Invalid email format", None
        
        # Validate password strength
        if len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return False, "Username already exists", None
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            return False, "Email already registered", None
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                full_name=full_name or username
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return True, "Registration successful", user
        
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    @staticmethod
    def login_user_service(username, password, remember=False):
        """
        Authenticate user and create session
        Returns: (success: bool, message: str, user: User)
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return False, "Invalid username or password", None
        
        if not user.is_active:
            return False, "Account is disabled", None
        
        if not user.check_password(password):
            return False, "Invalid username or password", None
        
        # Log in user
        login_user(user, remember=remember)
        user.update_last_login()
        
        return True, "Login successful", user
    
    @staticmethod
    def logout_user_service():
        """Logout current user"""
        logout_user()
        return True, "Logged out successfully"