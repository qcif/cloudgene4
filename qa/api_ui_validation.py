#!/usr/bin/env python3
"""
API-based UI Validation Tests
Validates that the APIs provide the correct data structure for UI components
Focus on BUG-01 fix validation and critical user flows
"""

import json
import requests
import time
from datetime import datetime

class APIUIValidator:
    def __init__(self, backend_url="http://localhost:8000", frontend_url="http://localhost:5173"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = []
        self.auth_token = None
    
    def log_test_result(self, test_id, description, passed, details=""):
        """Log test results"""
        result = {
            "test_id": test_id,
            "description": description,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_id}: {description}")
        if details and not passed:
            print(f"    Details: {details}")
        return passed
    
    def test_frontend_serving(self):
        """Test that frontend is being served correctly"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            
            has_vue_structure = all([
                '<div id="app"></div>' in response.text,
                'script type="module"' in response.text,
                response.status_code == 200
            ])
            
            return self.log_test_result(
                "FRONTEND-01",
                "Frontend application is being served",
                has_vue_structure,
                f"Status: {response.status_code}, Has Vue: {has_vue_structure}"
            )
        except Exception as e:
            return self.log_test_result("FRONTEND-01", "Frontend application is being served", False, str(e))
    
    def test_workflow_api_structure(self):
        """Test BUG-01 fix: Workflow API provides both field name formats"""
        try:
            response = requests.get(f"{self.backend_url}/api/workflows/hello-cloudgene/", timeout=10)
            
            if response.status_code != 200:
                return self.log_test_result(
                    "UI-12-API",
                    "Workflow API returns hello-cloudgene data",
                    False,
                    f"API returned status {response.status_code}"
                )
            
            data = response.json()
            parameters = data.get('parameters', [])
            
            if not parameters:
                return self.log_test_result(
                    "UI-12-API", 
                    "Workflow has parameters (BUG-01 validation)",
                    False,
                    "No parameters found in API response"
                )
            
            # Check for BUG-01 fix: both old and new field names should be present
            first_param = parameters[0]
            
            has_old_fields = 'parameter_id' in first_param and 'parameter_type' in first_param
            has_new_fields = 'id' in first_param and 'type' in first_param
            has_compatibility_fields = 'label' in first_param and 'value' in first_param
            
            bug01_fixed = has_old_fields and has_new_fields
            
            details = {
                "total_parameters": len(parameters),
                "has_parameter_id": has_old_fields,
                "has_id_field": has_new_fields,
                "has_compatibility": has_compatibility_fields,
                "sample_param_keys": list(first_param.keys())[:8]  # First 8 keys
            }
            
            return self.log_test_result(
                "UI-12-API",
                "Workflow API provides compatible field names (BUG-01 fix)",
                bug01_fixed,
                json.dumps(details, indent=2)
            )
            
        except Exception as e:
            return self.log_test_result("UI-12-API", "Workflow API structure validation", False, str(e))
    
    def test_authentication_flow(self):
        """Test authentication endpoints (BUG-02/BUG-03 validation)"""
        try:
            # Test login without session cookies (should work)
            login_data = {
                "username": "testuser",
                "password": "Testpass1"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/auth/login/",
                json=login_data,
                timeout=10
            )
            
            login_success = response.status_code == 200 and 'token' in response.json()
            
            if login_success:
                self.auth_token = response.json()['token']
            
            # Test login with session simulation (BUG-02 validation)
            session = requests.Session()
            # First request to create session
            session.get(f"{self.backend_url}/", timeout=5)
            
            # Login with session (should work after fix)
            response_with_session = session.post(
                f"{self.backend_url}/api/auth/login/",
                json=login_data,
                timeout=10
            )
            
            session_login_success = response_with_session.status_code == 200
            
            return self.log_test_result(
                "UI-03-API",
                "Login works reliably with/without sessions (BUG-02 fix)",
                login_success and session_login_success,
                f"Basic login: {login_success}, Session login: {session_login_success}"
            )
            
        except Exception as e:
            return self.log_test_result("UI-03-API", "Authentication flow validation", False, str(e))
    
    def test_password_reset_flow(self):
        """Test password reset functionality (BUG-03 validation)"""
        try:
            # Test password reset request
            reset_data = {"email": "testuser@example.com"}
            
            response = requests.post(
                f"{self.backend_url}/api/auth/password-reset/",
                json=reset_data,
                timeout=10
            )
            
            reset_success = response.status_code == 200 and 'message' in response.json()
            
            # Test with session simulation
            session = requests.Session()
            session.get(f"{self.backend_url}/", timeout=5)
            
            response_with_session = session.post(
                f"{self.backend_url}/api/auth/password-reset/",
                json=reset_data,
                timeout=10
            )
            
            session_reset_success = response_with_session.status_code == 200
            
            return self.log_test_result(
                "UI-09-API",
                "Password reset works with/without sessions (BUG-03 fix)",
                reset_success and session_reset_success,
                f"Basic reset: {reset_success}, Session reset: {session_reset_success}"
            )
            
        except Exception as e:
            return self.log_test_result("UI-09-API", "Password reset flow validation", False, str(e))
    
    def test_protected_endpoints(self):
        """Test protected endpoints work with token auth"""
        if not self.auth_token:
            return self.log_test_result("UI-AUTH", "Protected endpoints test", False, "No auth token available")
        
        try:
            headers = {"Authorization": f"Token {self.auth_token}"}
            
            # Test jobs endpoint
            response = requests.get(f"{self.backend_url}/api/jobs/", headers=headers, timeout=10)
            jobs_access = response.status_code == 200
            
            # Test user profile-like endpoint  
            response = requests.get(f"{self.backend_url}/api/users/", headers=headers, timeout=10)
            users_access = response.status_code in [200, 403]  # 403 is fine for non-admin
            
            return self.log_test_result(
                "UI-AUTH",
                "Token-based authentication works for protected endpoints",
                jobs_access and users_access,
                f"Jobs access: {jobs_access}, Users response: {response.status_code}"
            )
            
        except Exception as e:
            return self.log_test_result("UI-AUTH", "Protected endpoints test", False, str(e))
    
    def test_workflow_submission_readiness(self):
        """Test that workflow submission APIs are ready"""
        if not self.auth_token:
            return self.log_test_result("UI-16-API", "Workflow submission readiness", False, "No auth token")
        
        try:
            headers = {"Authorization": f"Token {self.auth_token}"}
            
            # Get workflow details
            response = requests.get(
                f"{self.backend_url}/api/workflows/hello-cloudgene/", 
                timeout=10
            )
            
            if response.status_code != 200:
                return self.log_test_result(
                    "UI-16-API",
                    "Workflow submission endpoint readiness",
                    False,
                    f"Workflow API not accessible: {response.status_code}"
                )
            
            workflow_data = response.json()
            input_params = [p for p in workflow_data.get('parameters', []) if p.get('is_input', True)]
            
            # Check if jobs endpoint is ready for submission
            response = requests.get(f"{self.backend_url}/api/jobs/", headers=headers, timeout=10)
            jobs_ready = response.status_code == 200
            
            submission_ready = len(input_params) > 0 and jobs_ready
            
            return self.log_test_result(
                "UI-16-API",
                "Workflow submission APIs are ready",
                submission_ready,
                f"Input params: {len(input_params)}, Jobs API ready: {jobs_ready}"
            )
            
        except Exception as e:
            return self.log_test_result("UI-16-API", "Workflow submission readiness", False, str(e))
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🔬 API-based UI Validation Suite")
        print("Validating backend readiness for UI functionality\n")
        
        # Test frontend serving
        self.test_frontend_serving()
        
        # Test critical bug fixes
        self.test_workflow_api_structure()
        self.test_authentication_flow()
        self.test_password_reset_flow()
        
        # Test functionality readiness
        self.test_protected_endpoints()
        self.test_workflow_submission_readiness()
        
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*70)
        print("🎯 API-UI VALIDATION SUMMARY")
        print("="*70)
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  {result['test_id']}: {result['description']}")
        
        # Specific validation for UI readiness
        workflow_api_passed = any(r['test_id'] == 'UI-12-API' and r['passed'] for r in self.test_results)
        auth_passed = any(r['test_id'] == 'UI-03-API' and r['passed'] for r in self.test_results)
        reset_passed = any(r['test_id'] == 'UI-09-API' and r['passed'] for r in self.test_results)
        
        critical_tests_passed = workflow_api_passed and auth_passed and reset_passed
        
        print("\n📋 CRITICAL UI TEST READINESS:")
        print(f"  UI-12 to UI-16 (Workflow forms): {'✅ READY' if workflow_api_passed else '❌ NOT READY'}")
        print(f"  UI-03 to UI-08 (Login flows): {'✅ READY' if auth_passed else '❌ NOT READY'}")  
        print(f"  UI-09 to UI-11 (Password reset): {'✅ READY' if reset_passed else '❌ NOT READY'}")
        
        if critical_tests_passed:
            print("\n🎉 ALL CRITICAL BACKEND APIS ARE READY FOR UI TESTING!")
        else:
            print("\n⚠️  Some critical APIs need attention before full UI testing")
            
        print("="*70)
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'critical_ready': critical_tests_passed,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    validator = APIUIValidator()
    
    try:
        summary = validator.run_all_tests()
        
        if summary['critical_ready'] and summary['success_rate'] > 80:
            print("🎉 Validation completed successfully - UI testing can proceed!")
            return 0
        else:
            print("⚠️  Validation completed with issues")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())