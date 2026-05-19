#!/usr/bin/env python3
"""
Specific test for the Hello Cloudgene workflow submission page
Tests whether the form fields actually render in the browser
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

class WorkflowPageTester:
    def __init__(self, frontend_url="http://localhost:5173"):
        self.frontend_url = frontend_url
        self.driver = None
        
    def setup_firefox_driver(self):
        """Try Firefox as alternative to Chrome"""
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            print("✅ Firefox driver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Firefox driver failed: {e}")
            return False
    
    def setup_chrome_driver_basic(self):
        """Try simpler Chrome setup"""
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--window-size=1920,1080")
            # Try without headless first
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Chrome driver failed: {e}")
            return False
    
    def setup_driver(self):
        """Try different browser drivers"""
        # Try Firefox first
        if self.setup_firefox_driver():
            return True
        
        # Try Chrome as fallback
        if self.setup_chrome_driver_basic():
            return True
            
        print("❌ Could not initialize any browser driver")
        return False
    
    def test_workflow_page_rendering(self):
        """Test the actual workflow page in browser"""
        if not self.setup_driver():
            return False
        
        try:
            print(f"🌐 Navigating to {self.frontend_url}/run/hello-cloudgene")
            self.driver.get(f"{self.frontend_url}/run/hello-cloudgene")
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Get page source for debugging
            page_source = self.driver.page_source
            print(f"📄 Page title: {self.driver.title}")
            
            # Check if we're getting an error page
            if "404" in page_source or "Not Found" in page_source:
                print("❌ Page shows 404 error")
                return False
            
            # Check if Vue app has loaded
            vue_app_loaded = self.driver.find_elements(By.ID, "app")
            print(f"🎯 Vue app container found: {len(vue_app_loaded) > 0}")
            
            # Look for form elements
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            all_selects = self.driver.find_elements(By.TAG_NAME, "select")
            all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            total_form_elements = len(all_inputs) + len(all_selects) + len(all_textareas)
            
            print(f"📋 Form elements found:")
            print(f"  Inputs: {len(all_inputs)}")
            print(f"  Selects: {len(all_selects)}")
            print(f"  Textareas: {len(all_textareas)}")
            print(f"  Total: {total_form_elements}")
            
            # Log what inputs we found
            if all_inputs:
                print("🔍 Input elements details:")
                for i, input_elem in enumerate(all_inputs[:5]):  # First 5 only
                    try:
                        input_type = input_elem.get_attribute("type") or "text"
                        input_name = input_elem.get_attribute("name") or "no-name"
                        input_placeholder = input_elem.get_attribute("placeholder") or ""
                        print(f"  Input {i+1}: type='{input_type}', name='{input_name}', placeholder='{input_placeholder}'")
                    except Exception as e:
                        print(f"  Input {i+1}: Could not get attributes - {e}")
            
            # Check for specific workflow-related text
            has_job_name = "job" in page_source.lower() and "name" in page_source.lower()
            has_workflow_content = "hello-cloudgene" in page_source.lower() or "workflow" in page_source.lower()
            has_parameter_content = "input" in page_source.lower()
            
            print(f"📝 Content analysis:")
            print(f"  Has job name field: {has_job_name}")
            print(f"  Has workflow content: {has_workflow_content}")
            print(f"  Has input/parameter content: {has_parameter_content}")
            
            # Look for error messages or loading indicators
            error_indicators = [
                "error", "404", "not found", "failed", "loading", "undefined"
            ]
            
            errors_found = [err for err in error_indicators if err in page_source.lower()]
            if errors_found:
                print(f"⚠️  Potential issues found: {errors_found}")
            
            # Check JavaScript console for errors (if possible)
            try:
                logs = self.driver.get_log('browser')
                if logs:
                    print("🐛 Browser console messages:")
                    for log in logs[-5:]:  # Last 5 logs
                        print(f"  {log['level']}: {log['message'][:100]}...")
            except Exception:
                print("📝 Could not retrieve console logs")
            
            # The key test: Do we have MORE than just a job name field?
            # This directly tests BUG-01
            expected_min_fields = 2  # Job name + at least one parameter field
            bug01_fixed = total_form_elements >= expected_min_fields
            
            print(f"\n🎯 BUG-01 TEST RESULT:")
            print(f"Expected minimum fields: {expected_min_fields}")
            print(f"Actual form elements: {total_form_elements}")
            print(f"BUG-01 fixed: {'✅ YES' if bug01_fixed else '❌ NO - Still shows only job name'}")
            
            if not bug01_fixed:
                print("\n🔍 DEBUGGING INFO:")
                print("If you still see only the job name field, possible causes:")
                print("1. Frontend not using the new API field names (id/type)")
                print("2. JavaScript errors preventing form rendering")
                print("3. Vue component not loading workflow data properly")
                print("4. API call timing issues")
            
            return bug01_fixed
            
        except Exception as e:
            print(f"💥 Test failed with error: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🧹 Browser closed")

def main():
    """Run the specific workflow page test"""
    print("🧪 Testing Hello Cloudgene Workflow Submission Page")
    print("This test directly validates whether BUG-01 is fixed in the browser\n")
    
    tester = WorkflowPageTester()
    
    try:
        success = tester.test_workflow_page_rendering()
        
        if success:
            print("\n🎉 Workflow page test PASSED!")
            print("The form renders multiple fields beyond just job name")
            return 0
        else:
            print("\n❌ Workflow page test FAILED!")
            print("The form still shows only the job name field - BUG-01 may not be fully fixed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())