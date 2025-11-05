"""
Models Package Init File
app/models/__init__.py
"""

# Import all models safely
try:
    from app.models.user import User
except ImportError:
    User = None

try:
    from app.models.company import Company
except ImportError:
    Company = None

try:
    from app.models.customer import Customer
except ImportError:
    Customer = None

try:
    from app.models.ticket import Ticket
except ImportError:
    Ticket = None

try:
    from app.models.payment import Payment
except ImportError:
    Payment = None

try:
    from app.models.prediction import Prediction
except ImportError:
    Prediction = None

try:
    from app.models.usage_stats import UsageStats
except ImportError:
    UsageStats = None

# Export available models
__all__ = [name for name, obj in locals().items() 
          if obj is not None and not name.startswith('_')]
