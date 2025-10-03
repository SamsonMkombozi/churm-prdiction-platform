#!/usr/bin/env python3
"""
Template Structure Verification and Fix Script
Run this to verify your templates are in the correct location
"""

import os
from pathlib import Path

def check_template_structure():
    """Check if template structure is correct"""
    
    print("=" * 60)
    print("TEMPLATE STRUCTURE VERIFICATION")
    print("=" * 60)
    
    # Get project root (assumes script is in project root)
    project_root = Path(__file__).parent
    templates_dir = project_root / 'templates'
    
    print(f"\n📁 Project Root: {project_root}")
    print(f"📁 Templates Directory: {templates_dir}")
    
    # Check if templates directory exists
    if not templates_dir.exists():
        print(f"\n❌ Templates directory does not exist!")
        print(f"   Creating: {templates_dir}")
        templates_dir.mkdir(exist_ok=True)
        print("   ✅ Created templates directory")
    else:
        print(f"\n✅ Templates directory exists")
    
    # Required template structure
    required_templates = {
        'base.html': templates_dir / 'base.html',
        'auth/login.html': templates_dir / 'auth' / 'login.html',
        'auth/register.html': templates_dir / 'auth' / 'register.html',
        'auth/forgot_password.html': templates_dir / 'auth' / 'forgot_password.html',
        'auth/reset_password.html': templates_dir / 'auth' / 'reset_password.html',
        'dashboard/index.html': templates_dir / 'dashboard' / 'index.html',
        'dashboard/analytics.html': templates_dir / 'dashboard' / 'analytics.html',
        'company/index.html': templates_dir / 'company' / 'index.html',
        'company/settings.html': templates_dir / 'company' / 'settings.html',
        'company/users.html': templates_dir / 'company' / 'users.html',
        'errors/404.html': templates_dir / 'errors' / '404.html',
        'errors/403.html': templates_dir / 'errors' / '403.html',
        'errors/500.html': templates_dir / 'errors' / '500.html',
    }
    
    print("\n" + "=" * 60)
    print("CHECKING REQUIRED TEMPLATES")
    print("=" * 60)
    
    missing_templates = []
    existing_templates = []
    
    for template_name, template_path in required_templates.items():
        if template_path.exists():
            print(f"✅ {template_name}")
            existing_templates.append(template_name)
        else:
            print(f"❌ {template_name} - MISSING")
            missing_templates.append((template_name, template_path))
    
    # Create missing directories
    print("\n" + "=" * 60)
    print("CREATING MISSING DIRECTORIES")
    print("=" * 60)
    
    directories_to_create = [
        templates_dir / 'auth',
        templates_dir / 'dashboard',
        templates_dir / 'company',
        templates_dir / 'errors',
        templates_dir / 'predictions',
    ]
    
    for directory in directories_to_create:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory.relative_to(project_root)}")
        else:
            print(f"✓ Exists: {directory.relative_to(project_root)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Existing templates: {len(existing_templates)}")
    print(f"❌ Missing templates: {len(missing_templates)}")
    
    if missing_templates:
        print("\n⚠️  MISSING TEMPLATES:")
        for template_name, _ in missing_templates:
            print(f"   - {template_name}")
        print("\n💡 Solution:")
        print("   1. Make sure all template files from your documents are copied to the templates/ directory")
        print("   2. Maintain the correct directory structure (auth/, dashboard/, company/, errors/)")
        print("   3. Re-run this script to verify")
        return False
    else:
        print("\n✅ All required templates are in place!")
        return True

def verify_flask_config():
    """Verify Flask can find templates"""
    print("\n" + "=" * 60)
    print("FLASK CONFIGURATION CHECK")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app('development')
        
        print(f"✅ Flask app created successfully")
        print(f"📁 Template folder: {app.template_folder}")
        print(f"📁 Root path: {app.root_path}")
        
        # List all templates Flask can see
        from jinja2 import FileSystemLoader
        loader = app.jinja_env.loader
        
        if isinstance(loader, FileSystemLoader):
            print(f"\n📋 Template search paths:")
            for path in loader.searchpath:
                print(f"   - {path}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        return False

def list_current_templates():
    """List all templates currently in the templates directory"""
    print("\n" + "=" * 60)
    print("CURRENT TEMPLATE FILES")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    templates_dir = project_root / 'templates'
    
    if not templates_dir.exists():
        print("❌ Templates directory does not exist")
        return
    
    template_files = list(templates_dir.rglob('*.html'))
    
    if not template_files:
        print("⚠️  No template files found in templates/ directory")
    else:
        print(f"\nFound {len(template_files)} template file(s):")
        for template_file in sorted(template_files):
            relative_path = template_file.relative_to(templates_dir)
            print(f"   ✓ {relative_path}")

if __name__ == '__main__':
    print("\n🔍 Starting template verification...\n")
    
    # Check template structure
    structure_ok = check_template_structure()
    
    # List current templates
    list_current_templates()
    
    # Verify Flask configuration
    flask_ok = verify_flask_config()
    
    # Final result
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    
    if structure_ok and flask_ok:
        print("✅ All checks passed! Your templates should work now.")
        print("\n🚀 Next step: Run 'python run.py' to start your application")
        exit(0)
    else:
        print("❌ Some issues found. Please fix them and run this script again.")
        print("\n📝 Common fixes:")
        print("   1. Copy all template files to the templates/ directory")
        print("   2. Ensure subdirectories (auth/, dashboard/, company/, errors/) exist")
        print("   3. Check file permissions")
        exit(1)