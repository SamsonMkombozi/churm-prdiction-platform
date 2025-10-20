# run.py - Simple Application Entry Point
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # Import and create app
    from app import create_app
    
    # Create application instance
    app = create_app('development')
    
    # Create database tables
    with app.app_context():
        try:
            from app.extensions import db
            db.create_all()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"⚠️ Database warning: {e}")
    
    # Run the application
    print("🚀 Starting Churn Prediction Platform...")
    print("📧 Try login: admin@example.com")
    print("🔑 Try password: admin123")
    print("🌐 URL: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
