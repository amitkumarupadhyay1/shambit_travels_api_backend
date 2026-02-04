#!/usr/bin/env python3
"""
Test script to validate requirements.txt compatibility
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path

def test_requirements_file(requirements_file):
    """Test if a requirements file can be installed successfully"""
    print(f"Testing {requirements_file}...")
    
    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_venv"
        
        try:
            # Create virtual environment
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True, capture_output=True)
            
            # Get pip path
            if os.name == 'nt':  # Windows
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:  # Unix/Linux/macOS
                pip_path = venv_path / "bin" / "pip"
            
            # Upgrade pip
            subprocess.run([
                str(pip_path), "install", "--upgrade", "pip"
            ], check=True, capture_output=True)
            
            # Test install requirements
            result = subprocess.run([
                str(pip_path), "install", "-r", requirements_file, "--dry-run"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {requirements_file} - All dependencies are compatible")
                return True
            else:
                print(f"❌ {requirements_file} - Compatibility issues found:")
                print(result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ {requirements_file} - Error during testing:")
            print(e.stderr.decode() if e.stderr else str(e))
            return False

def main():
    """Test all requirements files"""
    requirements_files = [
        "requirements.txt",
        "requirements-stable.txt", 
        "requirements-django5.txt",
        "requirements-pinned.txt"
    ]
    
    results = {}
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            results[req_file] = test_requirements_file(req_file)
        else:
            print(f"⚠️ {req_file} - File not found")
            results[req_file] = False
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("="*50)
    
    all_passed = True
    for req_file, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{req_file}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All requirements files are compatible!")
        return 0
    else:
        print("\n⚠️ Some requirements files have compatibility issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())