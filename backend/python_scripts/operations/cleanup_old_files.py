#!/usr/bin/env python3
"""
Project Cleanup Script

Maintains project organization by:
- Archiving old reports
- Archiving old custom exports
- Removing outdated log files
- Providing disk usage summary
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Configuration (operations/ -> python_scripts/ -> backend/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / 'reports'
EXPORTS_DIR = PROJECT_ROOT / 'exports'
LOGS_DIR = PROJECT_ROOT / 'logs'
ARCHIVE_DIR = EXPORTS_DIR / 'archive'


def get_folder_size(path: Path) -> int:
    """Calculate folder size in bytes"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def archive_old_reports(days_to_keep=90, dry_run=True):
    """Archive reports older than specified days"""
    print("\n📦 Archiving Old Reports...")
    print("-" * 70)
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    archive_reports = ARCHIVE_DIR / 'reports'
    archive_reports.mkdir(parents=True, exist_ok=True)
    
    archived_count = 0
    freed_space = 0
    
    for file in REPORTS_DIR.glob('weekly-report-*'):
        file_time = datetime.fromtimestamp(file.stat().st_mtime)
        
        if file_time < cutoff_date:
            file_size = file.stat().st_size
            
            if dry_run:
                print(f"   Would archive: {file.name} ({format_size(file_size)})")
            else:
                shutil.move(str(file), str(archive_reports / file.name))
                print(f"   ✅ Archived: {file.name} ({format_size(file_size)})")
            
            archived_count += 1
            freed_space += file_size
    
    if archived_count == 0:
        print("   ✅ No old reports to archive")
    else:
        print(f"\n   Total: {archived_count} files, {format_size(freed_space)} freed")
    
    if dry_run:
        print(f"\n   ⚠️  DRY RUN - No files actually moved")
        print(f"   Run with --execute to perform cleanup")


def archive_old_custom_exports(days_to_keep=30, dry_run=True):
    """Archive custom Tableau exports older than specified days"""
    print("\n📦 Archiving Old Custom Exports...")
    print("-" * 70)
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    tableau_dir = EXPORTS_DIR / 'tableau'
    
    archived_count = 0
    freed_space = 0
    
    for file in tableau_dir.glob('tableau_custom_*.csv'):
        file_time = datetime.fromtimestamp(file.stat().st_mtime)
        
        if file_time < cutoff_date:
            file_size = file.stat().st_size
            
            if dry_run:
                print(f"   Would archive: {file.name} ({format_size(file_size)})")
            else:
                shutil.move(str(file), str(ARCHIVE_DIR / file.name))
                print(f"   ✅ Archived: {file.name} ({format_size(file_size)})")
            
            archived_count += 1
            freed_space += file_size
    
    if archived_count == 0:
        print("   ✅ No old custom exports to archive")
    else:
        print(f"\n   Total: {archived_count} files, {format_size(freed_space)} freed")
    
    if dry_run:
        print(f"\n   ⚠️  DRY RUN - No files actually moved")


def clean_old_logs(days_to_keep=30, dry_run=True):
    """Remove log files older than specified days"""
    print("\n🗑️  Cleaning Old Logs...")
    print("-" * 70)
    
    if not LOGS_DIR.exists():
        print("   ✅ No logs directory")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    removed_count = 0
    freed_space = 0
    
    for file in LOGS_DIR.glob('*.log'):
        file_time = datetime.fromtimestamp(file.stat().st_mtime)
        
        if file_time < cutoff_date:
            file_size = file.stat().st_size
            
            if dry_run:
                print(f"   Would remove: {file.name} ({format_size(file_size)})")
            else:
                file.unlink()
                print(f"   ✅ Removed: {file.name} ({format_size(file_size)})")
            
            removed_count += 1
            freed_space += file_size
    
    if removed_count == 0:
        print("   ✅ No old logs to clean")
    else:
        print(f"\n   Total: {removed_count} files, {format_size(freed_space)} freed")
    
    if dry_run:
        print(f"\n   ⚠️  DRY RUN - No files actually removed")


def show_disk_usage():
    """Show disk usage summary"""
    print("\n💾 Disk Usage Summary")
    print("=" * 70)
    
    folders = [
        ('backend/python_scripts', 'Python Scripts'),
        ('backend/scripts', 'Node.js Scripts (Legacy)'),
        ('docs', 'Documentation'),
        ('reports', 'Generated Reports'),
        ('exports/tableau', 'Tableau Exports'),
        ('exports/archive', 'Archived Files'),
        ('logs', 'Log Files'),
        ('venv', 'Python Virtual Env')
    ]
    
    total_size = 0
    
    for folder, name in folders:
        path = PROJECT_ROOT / folder
        if path.exists():
            size = get_folder_size(path)
            total_size += size
            print(f"   {name:30} {format_size(size):>12}")
        else:
            print(f"   {name:30} {'(empty)':>12}")
    
    print("-" * 70)
    print(f"   {'TOTAL':30} {format_size(total_size):>12}")
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old project files')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform cleanup (default is dry-run)')
    parser.add_argument('--reports-days', type=int, default=90,
                       help='Keep reports from last N days (default: 90)')
    parser.add_argument('--exports-days', type=int, default=30,
                       help='Keep custom exports from last N days (default: 30)')
    parser.add_argument('--logs-days', type=int, default=30,
                       help='Keep logs from last N days (default: 30)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧹 PROJECT CLEANUP SCRIPT")
    print("=" * 70)
    
    if not args.execute:
        print("\n⚠️  DRY RUN MODE - No files will be modified")
        print("   Use --execute to actually perform cleanup")
    else:
        print("\n⚡ EXECUTE MODE - Files will be moved/deleted")
    
    # Show current disk usage
    show_disk_usage()
    
    # Perform cleanup
    archive_old_reports(args.reports_days, dry_run=not args.execute)
    archive_old_custom_exports(args.exports_days, dry_run=not args.execute)
    clean_old_logs(args.logs_days, dry_run=not args.execute)
    
    # Show final disk usage
    if args.execute:
        print("\n" + "=" * 70)
        print("✅ CLEANUP COMPLETE")
        print("=" * 70)
        show_disk_usage()
    else:
        print("\n" + "=" * 70)
        print("💡 To perform cleanup, run:")
        print("   npm run py:cleanup")
        print("=" * 70)


if __name__ == '__main__':
    main()
