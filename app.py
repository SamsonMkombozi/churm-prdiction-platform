"""
Main Flask Application Entry Point
app.py

Run this file to start the Flask development server
"""
import os
from app import create_app

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the application
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("🚀 Starting Churn Prediction Platform")
    print("=" * 40)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug mode: {debug_mode}")
    print(f"Host: {os.getenv('FLASK_HOST', '127.0.0.1')}")
    print(f"Port: {os.getenv('FLASK_PORT', 5000)}")
    print("=" * 40)
    
    # Start the server
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=debug_mode
    )
