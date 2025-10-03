"""
Custom Jinja2 Template Filters
"""
from datetime import datetime

def number_filter(value):
    """Format number with commas"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

def datetime_filter(value, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime object"""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    try:
        return value.strftime(format)
    except (AttributeError, ValueError):
        return str(value)

def date_filter(value, format='%Y-%m-%d'):
    """Format date object"""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    try:
        return value.strftime(format)
    except (AttributeError, ValueError):
        return str(value)

def currency_filter(value, symbol='$'):
    """Format as currency"""
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return value

def percentage_filter(value, decimals=1):
    """Format as percentage"""
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return value

def register_filters(app):
    """Register all custom filters with Flask app"""
    app.jinja_env.filters['number'] = number_filter
    app.jinja_env.filters['datetime'] = datetime_filter
    app.jinja_env.filters['date'] = date_filter
    app.jinja_env.filters['currency'] = currency_filter
    app.jinja_env.filters['percentage'] = percentage_filter