#!/usr/bin/env python3
"""
Quick test of admin workflow settings page fix
"""
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_admin_workflow_settings():
    """Test admin workflow settings API endpoints"""
    session = requests.Session()
    
    # Login first
    print("1. Testing login...")
    login_response = session.post(f'{BASE_URL}/auth/login/', {
        'username': 'admin',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
        
    print("✅ Login successful")
    
    # Test workflow API
    print("2. Testing workflow API...")
    workflow_response = session.get(f'{BASE_URL}/api/workflows/hello-cloudgene/')
    
    if workflow_response.status_code != 200:
        print(f"❌ Workflow API failed: {workflow_response.status_code}")
        return False
        
    workflow_data = workflow_response.json()
    print(f"✅ Workflow API successful, has allowed_groups: {'allowed_groups' in workflow_data}")
    
    # Test groups API
    print("3. Testing groups API...")
    groups_response = session.get(f'{BASE_URL}/api/groups/')
    
    if groups_response.status_code != 200:
        print(f"❌ Groups API failed: {groups_response.status_code}")
        return False
        
    groups_data = groups_response.json()
    print(f"✅ Groups API successful, returned {len(groups_data.get('results', groups_data))} groups")
    
    # Check for null values in groups
    groups_list = groups_data.get('results', groups_data)
    null_count = sum(1 for g in groups_list if g is None)
    print(f"📊 Groups with null values: {null_count}")
    
    return True

if __name__ == "__main__":
    test_admin_workflow_settings()