#!/usr/bin/env python3
"""
Setup verification script.
Checks that all dependencies are installed and the project structure is correct.
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required = ['requests', 'python-dateutil', 'tqdm']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_structure():
    """Check project structure."""
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'src/__init__.py',
        'src/jira_client.py',
        'src/scraper.py',
        'src/state_manager.py',
        'src/data_transformer.py'
    ]
    
    all_present = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_present = False
    
    return all_present

def main():
    """Run all checks."""
    print("Apache Jira Scraper - Setup Verification")
    print("=" * 60)
    
    print("\n1. Checking Python version...")
    if not check_python_version():
        sys.exit(1)
    
    print("\n2. Checking project structure...")
    if not check_structure():
        print("\n❌ Project structure is incomplete")
        sys.exit(1)
    
    print("\n3. Checking dependencies...")
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install them with: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All checks passed! The scraper is ready to use.")
    print("=" * 60)
    print("\nRun the scraper with:")
    print("  python main.py")
    print("\nOr see README.md for more options.")

if __name__ == '__main__':
    main()

