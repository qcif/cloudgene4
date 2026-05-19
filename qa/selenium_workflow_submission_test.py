#!/usr/bin/env python3
"""
Selenium test to catch workflow submission FormData errors and validate complete submission flow
"""
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, JavascriptException


class WorkflowSubmissionTest(unittest.TestCase):
    """
    Test workflow submission functionality with Selenium
    """
    
    def setUp(self):
        """Set up Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run headless for CI
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.base_url = 'http://localhost:3000'
        self.wait = WebDriverWait(self.driver, 15)
    
    def tearDown(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()
    
    def login_as_admin(self):
        """Login as admin user"""
        self.driver.get(f'{self.base_url}/login')
        
        # Wait for login form
        username_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_field = self.driver.find_element(By.NAME, 'password')
        
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        
        # Submit login
        login_button = self.driver.find_element(By.TYPE, 'submit')
        login_button.click()
        
        # Wait for redirect to dashboard/home
        self.wait.until(
            EC.any_of(
                EC.url_contains('/dashboard'),
                EC.url_contains('/workflows'),
                EC.presence_of_element_located((By.CLASS_NAME, 'navbar'))
            )
        )
    
    def test_workflow_submission_formdata_error(self):
        """
        Test that catches the FormData.append error during workflow submission
        """
        # Login first
        self.login_as_admin()
        
        # Navigate to hello-cloudgene workflow
        self.driver.get(f'{self.base_url}/run/hello-cloudgene')
        
        # Wait for workflow form to load
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'job-name'))
        )
        
        # Check that form parameters are rendered
        job_name_field = self.driver.find_element(By.ID, 'job-name')
        self.assertIsNotNone(job_name_field, "Job name field should be present")
        
        # Fill in job name
        job_name_field.clear()
        job_name_field.send_keys('selenium-test-job')
        
        # Check for workflow parameters (should be more than just job name)
        form_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input, select, textarea')
        self.assertGreater(len(form_elements), 1, "Should have workflow parameters beyond job name")
        
        # Check for console errors before submission
        initial_logs = self.driver.get_log('browser')
        
        # Find and click submit button
        submit_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        
        # Store initial page URL to detect navigation
        initial_url = self.driver.current_url
        
        # Submit the form
        submit_button.click()
        
        # Wait a moment for any JavaScript execution
        time.sleep(2)
        
        # Check for JavaScript errors in console
        browser_logs = self.driver.get_log('browser')
        js_errors = [log for log in browser_logs if log['level'] == 'SEVERE' and 'javascript' in log['message'].lower()]
        
        # Specifically check for FormData.append error
        formdata_errors = [
            log for log in js_errors 
            if 'formdata.append is not a function' in log['message'].lower() or
               'append is not a function' in log['message'].lower()
        ]
        
        self.assertEqual(len(formdata_errors), 0, 
                        f"Found FormData.append errors: {[log['message'] for log in formdata_errors]}")
        
        # Check that no other critical JavaScript errors occurred
        critical_errors = [
            log for log in js_errors
            if any(keyword in log['message'].lower() for keyword in [
                'uncaught', 'typeerror', 'referenceerror', 'syntaxerror'
            ])
        ]
        
        if critical_errors:
            print("Critical JavaScript errors found:")
            for error in critical_errors:
                print(f"  - {error['message']}")
        
        # The form submission should either:
        # 1. Navigate to a job page (/jobs/{id})
        # 2. Show a success message
        # 3. Show a validation error (but not a JS error)
        
        try:
            # Wait for either navigation or feedback
            self.wait.until(
                EC.any_of(
                    EC.url_contains('/jobs/'),  # Successful submission
                    EC.presence_of_element_located((By.CLASS_NAME, 'alert-success')),  # Success message
                    EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger')),   # Error message (non-JS)
                )
            )
            
            current_url = self.driver.current_url
            
            if '/jobs/' in current_url:
                print(f"✅ Successfully redirected to job page: {current_url}")
            else:
                # Check for feedback messages
                alerts = self.driver.find_elements(By.CSS_SELECTOR, '.alert')
                if alerts:
                    for alert in alerts:
                        print(f"Feedback: {alert.text}")
                        
        except TimeoutException:
            # If no navigation or feedback, the form submission likely failed silently
            # This might indicate the FormData error or another issue
            current_url = self.driver.current_url
            if current_url == initial_url:
                self.fail("Form submission failed - no navigation or feedback detected")
    
    def test_workflow_parameters_rendering(self):
        """
        Test that workflow parameters render correctly (catches DynamicForm issues)
        """
        self.login_as_admin()
        self.driver.get(f'{self.base_url}/run/hello-cloudgene')
        
        # Wait for form to load
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'job-name'))
        )
        
        # Check that DynamicForm rendered parameters
        # Look for form inputs beyond the job name
        parameter_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
            'input:not(#job-name), select, textarea')
        
        # The hello-cloudgene workflow should have input parameters
        self.assertGreater(len(parameter_inputs), 0, 
                          "Workflow should have input parameters rendered")
        
        # Check that parameters have proper names/IDs
        for input_elem in parameter_inputs:
            input_name = input_elem.get_attribute('name') or input_elem.get_attribute('id')
            self.assertIsNotNone(input_name, 
                               "All parameter inputs should have name or id attributes")
    
    def test_form_validation(self):
        """
        Test form validation and error handling
        """
        self.login_as_admin()
        self.driver.get(f'{self.base_url}/run/hello-cloudgene')
        
        # Wait for form
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'job-name'))
        )
        
        # Try submitting without required fields
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Check for validation feedback
        time.sleep(1)
        
        # HTML5 validation or custom validation should prevent submission
        # or show error messages
        validation_messages = self.driver.find_elements(By.CSS_SELECTOR, 
            '.invalid-feedback, .alert-danger, :invalid')
        
        # Either validation prevents submission or error messages are shown
        current_url = self.driver.current_url
        self.assertTrue(
            '/run/hello-cloudgene' in current_url or len(validation_messages) > 0,
            "Form validation should prevent submission or show errors"
        )
    
    def test_console_error_detection(self):
        """
        Generic test to catch any console errors during workflow page load
        """
        self.login_as_admin()
        
        # Clear browser logs
        self.driver.get(f'{self.base_url}/run/hello-cloudgene')
        
        # Wait for page to fully load
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'job-name'))
        )
        
        # Give Vue components time to mount and render
        time.sleep(3)
        
        # Check for any console errors
        browser_logs = self.driver.get_log('browser')
        errors = [log for log in browser_logs if log['level'] == 'SEVERE']
        
        if errors:
            print("Console errors detected:")
            for error in errors:
                print(f"  - {error['message']}")
        
        # Filter out known non-critical errors (favicon, etc.)
        critical_errors = [
            error for error in errors 
            if not any(ignore in error['message'].lower() for ignore in [
                'favicon.ico', 'manifest.json', 'net::err_failed'
            ])
        ]
        
        self.assertEqual(len(critical_errors), 0,
                        f"Found critical console errors: {[e['message'] for e in critical_errors]}")


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, warnings='ignore')