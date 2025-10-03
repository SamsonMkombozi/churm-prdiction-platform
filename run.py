from app import create_app
import os

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )