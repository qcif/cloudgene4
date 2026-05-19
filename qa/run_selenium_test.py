#!/usr/bin/env python3
"""
Simple runner for Selenium workflow submission test
"""
import subprocess
import sys
import time
import requests


def check_server_running(url='http://localhost:3000'):
    """Check if the development server is running"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    print("🧪 Selenium Workflow Submission Test Runner")
    print("=" * 50)
    
    # Check if server is running
    print("1. Checking if development server is running...")
    if not check_server_running():
        print("❌ Development server not running at http://localhost:3000")
        print("   Please start the server first with:")
        print("   npm run dev (frontend)")
        print("   python manage.py runserver (backend)")
        sys.exit(1)
    
    print("✅ Development server is running")
    
    # Check if Chrome/Chromium is available
    print("\n2. Checking Chrome/Chromium installation...")
    try:
        result = subprocess.run(['which', 'google-chrome'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            result = subprocess.run(['which', 'chromium-browser'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Chrome or Chromium not found")
                print("   Install with: sudo apt-get install chromium-browser")
                sys.exit(1)
        print("✅ Chrome/Chromium found")
    except Exception as e:
        print(f"❌ Error checking for Chrome: {e}")
        sys.exit(1)
    
    # Run the test
    print("\n3. Running Selenium tests...")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            'python3', 'qa/selenium_workflow_submission_test.py'
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("The FormData error and other workflow submission issues are resolved.")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            print("Check the output above for specific test failures.")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()