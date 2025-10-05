#!/usr/bin/env python3
"""
Auto-fix CRM Service sync_payments method
Run this: python3 fix_crm_service.py
"""

import re
import shutil
from datetime import datetime

def fix_crm_service():
    """Replace sync_payments method in crm_service.py"""
    
    file_path = 'app/services/crm_service.py'
    backup_path = f'{file_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print("=" * 60)
    print("FIXING CRM SERVICE sync_payments METHOD")
    print("=" * 60)
    print()
    
    # Read current file
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found!")
        return False
    
    # Backup
    print(f"📁 Creating backup: {backup_path}")
    shutil.copy2(file_path, backup_path)
    print("✅ Backup created")
    print()
    
    # New sync_payments method
    new_method = '''    def sync_payments(self) -> Dict:
        """
        Sync payment transactions from CRM to database
        ✅ FIXED: Handles missing customers gracefully
        
        Returns:
            Dictionary with sync results
        """
        from app.repositories.payment_repository import PaymentRepository
        
        try:
            # Fetch payments from CRM
            payments_data = self.fetch_payments()
            
            repo = PaymentRepository(self.company)
            
            created = 0
            updated = 0
            skipped = 0  # ✅ NEW: Track skipped payments
            errors = 0
            
            for payment_data in payments_data:
                try:
                    result = repo.create_or_update(payment_data)
                    
                    # ✅ FIX: Handle None return (skipped due to missing customer)
                    if result is True:
                        created += 1
                    elif result is False:
                        updated += 1
                    elif result is None:
                        skipped += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync payment {payment_data.get('id')}: {e}")
                    errors += 1
            
            # Commit all changes
            db.session.commit()
            
            # Build message
            message = f"Synced {created} new, {updated} updated"
            if skipped > 0:
                message += f", {skipped} skipped (customers not found)"
            if errors > 0:
                message += f", {errors} errors"
            
            logger.info(message)
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'errors': errors,
                'total': len(payments_data),
                'message': message
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Payment sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }'''
    
    # Find and replace the sync_payments method
    # Pattern to match the entire method including its content
    pattern = r'(    def sync_payments\(self\) -> Dict:.*?(?=\n    def |\n\ndef |\Z))'
    
    if not re.search(pattern, content, re.DOTALL):
        print("❌ Could not find sync_payments method!")
        print("   You'll need to update it manually.")
        print()
        print("Look for 'def sync_payments(self)' in crm_service.py")
        print("and replace the entire method with the one shown in the script output")
        return False
    
    # Replace the method
    new_content = re.sub(pattern, new_method, content, flags=re.DOTALL)
    
    # Verify replacement happened
    if new_content == content:
        print("⚠️  No changes made - method may already be updated")
        return True
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("✅ sync_payments method updated successfully!")
    print()
    print("=" * 60)
    print("CHANGES APPLIED")
    print("=" * 60)
    print()
    print("📋 Summary:")
    print("   ✅ payment_repository.py - Fixed (handles missing customers)")
    print("   ✅ crm_service.py - Fixed (tracks skipped payments)")
    print()
    print("🚀 Next steps:")
    print("   1. Restart Flask: python3 run.py")
    print("   2. Go to: http://localhost:5001/crm/dashboard")
    print("   3. Click 'Sync CRM Data'")
    print()
    print("Expected result:")
    print("   ✅ Sync completes successfully")
    print("   ✅ Customers synced: ~1000+")
    print("   ✅ Payments synced: Most payments")
    print("   ⚠️  Some payments skipped (customers not in DB)")
    print()
    
    return True


if __name__ == '__main__':
    success = fix_crm_service()
    
    if success:
        print("=" * 60)
        print("✅ ALL FIXES COMPLETE!")
        print("=" * 60)
        exit(0)
    else:
        print()
        print("=" * 60)
        print("⚠️  MANUAL UPDATE REQUIRED")
        print("=" * 60)
        exit(1)