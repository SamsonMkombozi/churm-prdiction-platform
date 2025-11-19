#!/usr/bin/env python3
"""
Show the exact changes needed for the render_template calls
"""

print("🔧 EXACT CHANGES NEEDED")
print("=" * 40)

print("1. FIRST render_template (around line 466):")
print()
print("CHANGE FROM:")
print("""        return render_template('crm/customers.html', 
                             company=company,
                             customers=pagination.items,
                             pagination=pagination,
                             current_status=status_filter,""")

print()
print("TO:")
print("""        return render_template('crm/customers.html', 
                             company=company,
                             customers=pagination.items,
                             pagination=pagination,
                             current_status=status_filter,
                             datetime=datetime)  # ← ADD THIS LINE""")

print()
print("=" * 50)
print()

print("2. SECOND render_template (around line 485):")
print()
print("CHANGE FROM:")
print("""        return render_template('crm/customers.html',
                             company=company,
                             customers=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='', current_risk='', current_search='', current_payment_behavior='',
                             error_message=str(e))""")

print()
print("TO:")
print("""        return render_template('crm/customers.html',
                             company=company,
                             customers=[],
                             pagination=type('Pagination', (), {'total': 0, 'pages': 1, 'page': 1, 'per_page': 50, 'has_prev': False, 'has_next': False})(),
                             current_status='', current_risk='', current_search='', current_payment_behavior='',
                             error_message=str(e),
                             datetime=datetime)  # ← ADD THIS LINE""")

print()
print("🎯 SUMMARY:")
print("Add 'datetime=datetime' as the last parameter in both render_template calls")
print("This will make the datetime variable available in your template")
print("Your disconnection dates will then show '2 days ago', '3 days ago', etc.")