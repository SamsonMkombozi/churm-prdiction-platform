from app import create_app, db
from app.models.user import User

# Create app
app = create_app('default')

# Create all tables
with app.app_context():
    # Drop all tables (be careful with this in production!)
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    # Create a test admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='Admin User',
        role='admin'
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    print("✅ Database initialized successfully!")
    print("✅ Admin user created:")
    print("   Username: admin")
    print("   Password: admin123")