# Selenium Testing for Workflow Submission

This directory contains Selenium tests designed to catch JavaScript errors and workflow submission issues that could occur in the browser.

## Test Coverage

### `selenium_workflow_submission_test.py`

**Purpose**: Comprehensive test for workflow submission functionality including the FormData error fix.

**Test Cases**:

1. **`test_workflow_submission_formdata_error`**
   - **What it catches**: The specific `TypeError: formData.append is not a function` error
   - **How**: Submits a workflow and monitors browser console for JavaScript errors
   - **Validation**: Ensures no FormData-related errors and proper form submission flow

2. **`test_workflow_parameters_rendering`** 
   - **What it catches**: DynamicForm rendering issues
   - **How**: Checks that workflow parameters are properly rendered beyond just job name
   - **Validation**: Ensures all parameter inputs have proper names/IDs

3. **`test_form_validation`**
   - **What it catches**: Form validation failures
   - **How**: Attempts submission with missing required fields
   - **Validation**: Ensures validation prevents submission or shows error messages

4. **`test_console_error_detection`**
   - **What it catches**: General JavaScript console errors
   - **How**: Monitors browser console during page load and interaction
   - **Validation**: Flags any critical JavaScript errors during workflow page usage

## Setup Requirements

### Install Dependencies
```bash
pip install selenium requests
```

### Install Chrome/Chromium
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# Or download ChromeDriver manually
```

### Verify Development Server
Make sure both frontend and backend are running:
- Frontend: `npm run dev` (http://localhost:3000)
- Backend: `python manage.py runserver` (http://localhost:8000)

## Running Tests

### Quick Test Run
```bash
python3 qa/run_selenium_test.py
```

### Direct Test Execution
```bash
python3 qa/selenium_workflow_submission_test.py
```

### Verbose Output
```bash
python3 -m unittest qa.selenium_workflow_submission_test -v
```

## Understanding Test Results

### ✅ Success Output
```
test_workflow_submission_formdata_error ... ok
✅ Successfully redirected to job page: http://localhost:3000/jobs/123
```

### ❌ FormData Error Detection
```
test_workflow_submission_formdata_error ... FAIL
Found FormData.append errors: ['TypeError: formData.append is not a function']
```

### ⚠️ JavaScript Errors
```
Console errors detected:
  - Uncaught TypeError: Cannot read properties of null (reading 'id')
  - ReferenceError: someFunction is not defined
```

## Test Strategy

### Browser Console Monitoring
The tests use `driver.get_log('browser')` to capture:
- JavaScript errors (TypeError, ReferenceError, etc.)
- Console warnings and errors
- Network failures affecting JavaScript

### Error Classification
Errors are categorized as:
- **Critical**: JavaScript exceptions that break functionality
- **FormData-specific**: The exact error we fixed
- **Validation**: Expected errors from form validation
- **Non-critical**: Favicon, manifest issues (filtered out)

### Navigation Validation
Tests verify that workflow submission either:
1. Redirects to job page (`/jobs/{id}`) - Success
2. Shows feedback message (success/error) - Handled gracefully  
3. Stays on form with validation - Expected behavior
4. **Never** fails silently due to JavaScript errors

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Selenium Tests
  run: |
    # Start servers
    npm run dev &
    python manage.py runserver &
    
    # Wait for servers
    sleep 10
    
    # Run tests
    python3 qa/run_selenium_test.py
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
python3 qa/run_selenium_test.py
```

## Extending Tests

### Adding New Test Cases
```python
def test_new_workflow_feature(self):
    """Test description"""
    self.login_as_admin()
    self.driver.get(f'{self.base_url}/run/workflow-name')
    
    # Test implementation
    # Always check console for errors:
    browser_logs = self.driver.get_log('browser')
    errors = [log for log in browser_logs if log['level'] == 'SEVERE']
    self.assertEqual(len(errors), 0, f"Console errors: {errors}")
```

### Testing Different Workflows
Update the test to iterate through multiple workflows:
```python
workflows = ['hello-cloudgene', 'another-workflow', 'complex-workflow']
for workflow in workflows:
    with self.subTest(workflow=workflow):
        self.driver.get(f'{self.base_url}/run/{workflow}')
        # Test logic here
```

## Troubleshooting

### Chrome Driver Issues
```bash
# Download specific ChromeDriver version
wget https://chromedriver.storage.googleapis.com/VERSION/chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
```

### Headless Mode Problems
Remove `--headless` from Chrome options for visual debugging:
```python
# chrome_options.add_argument('--headless')  # Comment out for debugging
```

### Server Connection Issues
Verify servers are running:
```bash
curl http://localhost:3000  # Frontend
curl http://localhost:8000  # Backend API
```

## Best Practices

1. **Always monitor console logs** for JavaScript errors
2. **Use explicit waits** instead of sleep() when possible
3. **Test both success and failure scenarios** 
4. **Clean up resources** in tearDown() method
5. **Use descriptive test names** that explain what error they catch
6. **Filter out non-critical errors** (favicon, etc.)
7. **Verify actual functionality** not just absence of errors

This test suite provides comprehensive coverage to prevent regression of the FormData error and catch similar JavaScript issues in workflow submission functionality.