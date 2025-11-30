#!/usr/bin/env python3
"""
Emergency Database Fix - Diagnose and Fix Permission Issues
"""

import os
import sys
import subprocess

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

print("\n" + "=" * 80)
print("🔍 DATABASE PERMISSION DIAGNOSIS")
print("=" * 80)

project = '/var/www/html/churn-prediction-platform'
instance_dir = f'{project}/instance'
db_file = f'{instance_dir}/churn_platform.db'

print(f"\n📂 Project: {project}")
print(f"📁 Instance: {instance_dir}")
print(f"💾 Database: {db_file}")

# 1. Check if files exist
print("\n" + "=" * 80)
print("1. FILE EXISTENCE CHECK")
print("=" * 80)
print(f"Instance directory exists: {os.path.exists(instance_dir)}")
print(f"Database file exists: {os.path.exists(db_file)}")

if os.path.exists(db_file):
    size = os.path.getsize(db_file)
    print(f"Database file size: {size:,} bytes")

# 2. Check permissions
print("\n" + "=" * 80)
print("2. PERMISSION CHECK")
print("=" * 80)

if os.path.exists(instance_dir):
    ls_output, _ = run_command(f'ls -la {instance_dir}')
    print("Directory listing:")
    print(ls_output)
    
    # Check directory permissions
    dir_stat = os.stat(instance_dir)
    dir_perms = oct(dir_stat.st_mode)[-3:]
    print(f"\nDirectory permissions: {dir_perms}")
    print(f"  Readable: {os.access(instance_dir, os.R_OK)}")
    print(f"  Writable: {os.access(instance_dir, os.W_OK)}")
    print(f"  Executable: {os.access(instance_dir, os.X_OK)}")

if os.path.exists(db_file):
    file_stat = os.stat(db_file)
    file_perms = oct(file_stat.st_mode)[-3:]
    print(f"\nDatabase file permissions: {file_perms}")
    print(f"  Readable: {os.access(db_file, os.R_OK)}")
    print(f"  Writable: {os.access(db_file, os.W_OK)}")

# 3. Check ownership
print("\n" + "=" * 80)
print("3. OWNERSHIP CHECK")
print("=" * 80)

import pwd
import grp

current_user = os.getenv('USER', 'unknown')
current_uid = os.getuid()
current_gid = os.getgid()

print(f"Current user: {current_user}")
print(f"Current UID: {current_uid}")
print(f"Current GID: {current_gid}")

if os.path.exists(instance_dir):
    dir_stat = os.stat(instance_dir)
    dir_owner = pwd.getpwuid(dir_stat.st_uid).pw_name
    dir_group = grp.getgrgid(dir_stat.st_gid).gr_name
    print(f"\nDirectory owner: {dir_owner}:{dir_group}")
    print(f"Directory UID: {dir_stat.st_uid}")
    print(f"Directory GID: {dir_stat.st_gid}")
    print(f"Ownership match: {dir_stat.st_uid == current_uid}")

if os.path.exists(db_file):
    file_stat = os.stat(db_file)
    file_owner = pwd.getpwuid(file_stat.st_uid).pw_name
    file_group = grp.getgrgid(file_stat.st_gid).gr_name
    print(f"\nFile owner: {file_owner}:{file_group}")
    print(f"File UID: {file_stat.st_uid}")
    print(f"File GID: {file_stat.st_gid}")
    print(f"Ownership match: {file_stat.st_uid == current_uid}")

# 4. Test write access
print("\n" + "=" * 80)
print("4. WRITE ACCESS TEST")
print("=" * 80)

test_file = f'{instance_dir}/test_write.tmp'
try:
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print("✅ Can write to instance directory")
except Exception as e:
    print(f"❌ Cannot write to instance directory: {e}")

# 5. Test SQLite access
print("\n" + "=" * 80)
print("5. SQLITE ACCESS TEST")
print("=" * 80)

try:
    import sqlite3
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    print(f"✅ Can open database with sqlite3")
    print(f"   Found {len(tables)} tables: {[t[0] for t in tables[:5]]}")
except Exception as e:
    print(f"❌ Cannot open database with sqlite3: {e}")

# 6. Check for file locks
print("\n" + "=" * 80)
print("6. FILE LOCK CHECK")
print("=" * 80)

lsof_output, _ = run_command(f'lsof {db_file} 2>/dev/null')
if lsof_output:
    print("Processes using the database:")
    print(lsof_output)
else:
    print("✅ No processes currently have the database file open")

# 7. PROPOSED FIX
print("\n" + "=" * 80)
print("7. PROPOSED FIX")
print("=" * 80)

fixes_needed = []

if os.path.exists(instance_dir):
    dir_stat = os.stat(instance_dir)
    if dir_stat.st_uid != current_uid:
        fixes_needed.append(f"sudo chown {current_user}:{current_user} {instance_dir}")
    
    dir_perms = oct(dir_stat.st_mode)[-3:]
    if dir_perms != '755':
        fixes_needed.append(f"chmod 755 {instance_dir}")

if os.path.exists(db_file):
    file_stat = os.stat(db_file)
    if file_stat.st_uid != current_uid:
        fixes_needed.append(f"sudo chown {current_user}:{current_user} {db_file}")
    
    file_perms = oct(file_stat.st_mode)[-3:]
    if file_perms not in ['664', '644']:
        fixes_needed.append(f"chmod 664 {db_file}")

if fixes_needed:
    print("⚠️  Issues found! Run these commands to fix:")
    print()
    for fix in fixes_needed:
        print(f"   {fix}")
    print()
    print("Or run this one-liner:")
    print(f"   sudo chown -R {current_user}:{current_user} {instance_dir} && chmod 755 {instance_dir} && chmod 664 {db_file}")
else:
    print("✅ No obvious permission issues found")
    print()
    print("The issue might be:")
    print("  1. SELinux/AppArmor restrictions")
    print("  2. Disk full (check with: df -h)")
    print("  3. Inode exhaustion (check with: df -i)")
    print("  4. Database corruption")

# 8. Additional checks
print("\n" + "=" * 80)
print("8. SYSTEM CHECKS")
print("=" * 80)

# Check disk space
df_output, _ = run_command('df -h /var/www/html/churn-prediction-platform')
print("Disk space:")
print(df_output)

# Check inodes
df_i_output, _ = run_command('df -i /var/www/html/churn-prediction-platform')
print("\nInode usage:")
print(df_i_output)

print("\n" + "=" * 80)