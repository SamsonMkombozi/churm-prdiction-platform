from app import create_app
import os

app = create_app()

with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print(f"\n📊 Database Configuration:")
    print(f"   URI: {db_uri}")
    
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        
        # Handle relative vs absolute paths
        if not db_path.startswith('/'):
            # Relative path - make it absolute
            from pathlib import Path
            project_root = Path(__file__).parent
            db_path = str(project_root / db_path)
        
        print(f"   Resolved path: {db_path}")
        print(f"   File exists: {os.path.exists(db_path)}")
        print(f"   Directory exists: {os.path.exists(os.path.dirname(db_path))}")
        
        if os.path.exists(db_path):
            print(f"   File readable: {os.access(db_path, os.R_OK)}")
            print(f"   File writable: {os.access(db_path, os.W_OK)}")
            
        dir_path = os.path.dirname(db_path)
        if os.path.exists(dir_path):
            print(f"   Directory readable: {os.access(dir_path, os.R_OK)}")
            print(f"   Directory writable: {os.access(dir_path, os.W_OK)}")
