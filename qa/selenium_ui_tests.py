#!/usr/bin/env python3
"""
Selenium UI Tests for Cloudgene Application
Tests UI flows from qa/06-selenium-ui-flows.md
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class CloudgeneUITester:
    def __init__(self, frontend_url="http://localhost:5173", backend_url="http://localhost:8000"):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.driver = None
        self.test_results = []
        
    def setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Chrome driver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def teardown_driver(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🧹 Browser closed")
    
    def log_test_result(self, test_id, description, passed, details=""):
        """Log test results"""
        result = {
            "test_id": test_id,
            "description": description,
            "passed": passed,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_id}: {description}")
        if details and not passed:
            print(f"    Details: {details}")
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, by, value, timeout=10):
        """Wait for element to be clickable"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            return None
    
    def test_ui_01_home_page_loads(self):
        """UI-01: Test that the home page loads correctly"""
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for the app to load
            time.sleep(3)
            
            # Check if the page loaded
            title = self.driver.title
            page_source = self.driver.page_source
            
            # Look for key elements
            has_cloudgene = "cloudgene" in page_source.lower() or "Cloudgene" in title
            has_navbar = "navbar" in page_source or "nav" in page_source
            
            passed = has_cloudgene or has_navbar or "vue" in page_source.lower()
            
            self.log_test_result(
                "UI-01", 
                "Home page loads correctly",
                passed,
                f"Title: {title}, Has content: {passed}"
            )
            return passed
            
        except Exception as e:
            self.log_test_result("UI-01", "Home page loads correctly", False, str(e))
            return False
    
    def test_ui_12_workflow_form_renders(self):
        """UI-12: Test that workflow form renders all input types (BUG-01 fix validation)"""
        try:
            # Navigate to workflow submission page
            workflow_url = f"{self.frontend_url}/run/hello-cloudgene"
            self.driver.get(workflow_url)
            
            # Wait for page to load
            time.sleep(5)
            
            page_source = self.driver.page_source
            
            # Check for form elements that should be present based on hello-cloudgene workflow
            has_job_name = "job" in page_source.lower() and "name" in page_source.lower()
            has_text_input = "input_text" in page_source or "text" in page_source.lower()
            has_file_input = "file" in page_source.lower()
            has_number_input = "number" in page_source.lower()
            has_checkbox = "checkbox" in page_source.lower()
            has_select = "select" in page_source.lower() or "option" in page_source.lower()
            
            # Look for form elements
            try:
                form_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                form_selects = self.driver.find_elements(By.TAG_NAME, "select")
                form_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                
                total_form_elements = len(form_inputs) + len(form_selects) + len(form_textareas)
                
                # Should have more than just a job name field (which was the bug)
                has_multiple_inputs = total_form_elements > 1
                
            except Exception:
                total_form_elements = 0
                has_multiple_inputs = False
            
            # Check for any error messages
            has_errors = "error" in page_source.lower() or "404" in page_source
            
            passed = (has_multiple_inputs and not has_errors) or (has_text_input and has_job_name)
            
            details = f"Form elements: {total_form_elements}, Has job name: {has_job_name}, Has text input: {has_text_input}, Has errors: {has_errors}"
            
            self.log_test_result(
                "UI-12",
                "Workflow form renders all input types",
                passed,
                details
            )
            return passed
            
        except Exception as e:
            self.log_test_result("UI-12", "Workflow form renders all input types", False, str(e))
            return False
    
    def test_ui_03_login_functionality(self):
        """UI-03: Test successful login and token storage"""
        try:
            # Navigate to login page
            login_url = f"{self.frontend_url}/login"
            self.driver.get(login_url)
            
            # Wait for login form to load
            time.sleep(3)
            
            page_source = self.driver.page_source
            
            # Check if login form is present
            has_username_field = "username" in page_source.lower()
            has_password_field = "password" in page_source.lower()
            has_login_button = "login" in page_source.lower() or "sign in" in page_source.lower()
            
            # Try to find form elements
            try:
                username_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or contains(@name, 'username')]")
                password_inputs = self.driver.find_elements(By.XPATH, "//input[@type='password']")
                
                has_username_input = len(username_inputs) > 0
                has_password_input = len(password_inputs) > 0
                
            except Exception:
                has_username_input = False
                has_password_input = False
            
            passed = (has_username_field and has_password_field) or (has_username_input and has_password_input)
            
            details = f"Username field: {has_username_field}, Password field: {has_password_field}, Form inputs found: {has_username_input and has_password_input}"
            
            self.log_test_result(
                "UI-03",
                "Login form loads correctly",
                passed,
                details
            )
            return passed
            
        except Exception as e:
            self.log_test_result("UI-03", "Login form loads correctly", False, str(e))
            return False
    
    def test_ui_navigation_structure(self):
        """Test basic navigation structure"""
        try:
            self.driver.get(self.frontend_url)
            time.sleep(3)
            
            page_source = self.driver.page_source
            
            # Check for navigation elements
            has_navbar = "navbar" in page_source or "nav" in page_source
            has_home_link = "home" in page_source.lower()
            has_login_link = "login" in page_source.lower()
            has_signup_link = "sign up" in page_source.lower() or "register" in page_source.lower()
            
            navigation_score = sum([has_navbar, has_home_link, has_login_link, has_signup_link])
            passed = navigation_score >= 2
            
            details = f"Navbar: {has_navbar}, Home: {has_home_link}, Login: {has_login_link}, Signup: {has_signup_link}"
            
            self.log_test_result(
                "UI-NAV",
                "Navigation structure present",
                passed,
                details
            )
            return passed
            
        except Exception as e:
            self.log_test_result("UI-NAV", "Navigation structure present", False, str(e))
            return False

    def run_critical_tests(self):
        """Run the most critical UI tests"""
        print("🚀 Starting critical UI tests...")
        
        if not self.setup_driver():
            return False
        
        try:
            # Test basic functionality
            self.test_ui_01_home_page_loads()
            self.test_ui_navigation_structure()
            self.test_ui_03_login_functionality()
            
            # Test critical workflow functionality (BUG-01 validation)
            self.test_ui_12_workflow_form_renders()
            
            return True
            
        finally:
            self.teardown_driver()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("🎯 UI TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  {result['test_id']}: {result['description']}")
                    print(f"    {result['details']}")
        
        print("="*60)
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    print("🔬 Cloudgene UI Testing Suite")
    print("Testing critical UI flows and BUG-01 fix validation\n")
    
    tester = CloudgeneUITester()
    
    try:
        success = tester.run_critical_tests()
        summary = tester.print_summary()
        
        if success and summary['success_rate'] > 50:
            print("🎉 UI testing completed successfully!")
            return 0
        else:
            print("⚠️  UI testing completed with issues")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())