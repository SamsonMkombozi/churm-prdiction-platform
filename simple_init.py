from app import create_app, db

# Force development mode
import os
os.environ['FLASK_ENV'] = 'development'

# Create app
app = create_app('development')

# Create all tables
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("✅ Database initialized successfully!")
    print("\nYou can now run: python run.py")
