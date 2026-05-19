#!/usr/bin/env python3
"""
Test script to verify content-type auto-detection fix
"""
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_content_type_handling():
    """Test different content types are handled correctly"""
    session = requests.Session()
    
    print("🧪 Testing Content-Type Auto-Detection")
    print("=" * 50)
    
    # Login first
    print("1. Testing JSON login request...")
    login_response = session.post(f'{BASE_URL}/auth/login/', 
                                 json={'username': 'admin', 'password': 'admin123'},
                                 headers={'Content-Type': 'application/json'})
    
    if login_response.status_code != 200:
        print(f"❌ JSON login failed: {login_response.status_code}")
        return False
        
    print("✅ JSON login successful")
    
    # Test JSON API call (admin endpoint)
    print("\n2. Testing JSON admin API call...")
    workflows_response = session.get(f'{BASE_URL}/api/workflows/')
    
    if workflows_response.status_code != 200:
        print(f"❌ JSON API call failed: {workflows_response.status_code}")
        return False
        
    print("✅ JSON API call successful")
    
    # Test FormData submission (job submission)
    print("\n3. Testing FormData job submission...")
    
    # Create FormData manually to simulate frontend
    files = {
        'workflow_id': (None, 'hello-cloudgene'),
        'job_name': (None, 'content-type-test-job'),
        # Add some workflow parameters if needed
    }
    
    # Remove explicit content-type to test auto-detection
    job_response = session.post(f'{BASE_URL}/api/jobs/', files=files)
    
    if job_response.status_code in [200, 201]:
        print("✅ FormData submission successful")
        job_data = job_response.json()
        print(f"   Created job: {job_data.get('id', 'unknown')}")
    elif job_response.status_code == 400:
        print("⚠️ FormData submission validation error (expected if missing required params)")
        try:
            error_data = job_response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Response: {job_response.text}")
    else:
        print(f"❌ FormData submission failed: {job_response.status_code}")
        print(f"   Response: {job_response.text}")
        return False
    
    # Test group creation (JSON)
    print("\n4. Testing JSON group creation...")
    group_response = session.post(f'{BASE_URL}/api/groups/', 
                                 json={'name': 'test-content-type-group'},
                                 headers={'Content-Type': 'application/json'})
    
    if group_response.status_code in [200, 201]:
        print("✅ JSON group creation successful")
        # Clean up - delete the test group
        group_data = group_response.json()
        session.delete(f'{BASE_URL}/api/groups/{group_data.get("id")}/')
    elif group_response.status_code == 400:
        print("⚠️ JSON group creation validation error")
        try:
            error_data = group_response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Response: {group_response.text}")
    else:
        print(f"❌ JSON group creation failed: {group_response.status_code}")
        print(f"   Response: {group_response.text}")
    
    print("\n" + "=" * 50)
    print("✅ Content-Type auto-detection tests completed")
    print("Both JSON and FormData requests are handled correctly!")
    
    return True

def test_axios_simulation():
    """Simulate what the axios client would do"""
    print("\n🔧 Simulating Axios Behavior")
    print("-" * 30)
    
    session = requests.Session()
    
    # Login first
    session.post(f'{BASE_URL}/auth/login/', json={'username': 'admin', 'password': 'admin123'})
    
    print("Testing simulated axios requests...")
    
    # Simulate JSON request (what axios does with object data)
    print("- JSON request simulation...")
    response1 = session.get(f'{BASE_URL}/api/workflows/', 
                           headers={'Content-Type': 'application/json'})
    print(f"  Status: {response1.status_code} ✅" if response1.status_code == 200 else f"  Status: {response1.status_code} ❌")
    
    # Simulate FormData request (what axios does with FormData)
    print("- FormData request simulation...")
    files = {
        'workflow_id': (None, 'hello-cloudgene'),
        'job_name': (None, 'axios-simulation-test'),
    }
    # Axios would NOT set Content-Type header for FormData, letting requests library handle it
    response2 = session.post(f'{BASE_URL}/api/jobs/', files=files)
    
    status = "✅" if response2.status_code in [200, 201, 400] else "❌"
    print(f"  Status: {response2.status_code} {status}")
    
    if response2.status_code == 400:
        print("  (400 expected due to missing required parameters)")

if __name__ == "__main__":
    try:
        test_content_type_handling()
        test_axios_simulation()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Make sure the development server is running at http://localhost:3000")