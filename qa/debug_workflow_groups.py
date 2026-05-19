#!/usr/bin/env python3
"""
Debug script to check workflow groups data structure
"""
import requests
import json

BASE_URL = 'http://localhost:3000'

def debug_workflow_groups():
    """Debug workflow and group data"""
    session = requests.Session()
    
    # Login as admin
    print("1. Admin login...")
    login_response = session.post(f'{BASE_URL}/auth/login/', {
        'username': 'admin',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
        
    print("✅ Login successful")
    
    # Get workflows
    print("\n2. Fetching workflows...")
    workflows_response = session.get(f'{BASE_URL}/api/workflows/')
    
    if workflows_response.status_code != 200:
        print(f"❌ Workflows API failed: {workflows_response.status_code}")
        return False
        
    workflows_data = workflows_response.json()
    workflows = workflows_data.get('results', workflows_data)
    
    print(f"✅ Found {len(workflows)} workflows")
    
    # Get groups
    print("\n3. Fetching groups...")
    groups_response = session.get(f'{BASE_URL}/api/groups/')
    
    if groups_response.status_code != 200:
        print(f"❌ Groups API failed: {groups_response.status_code}")
        return False
        
    groups_data = groups_response.json()
    groups = groups_data.get('results', groups_data)
    
    print(f"✅ Found {len(groups)} groups")
    for group in groups:
        print(f"   - {group}")
    
    # Analyze workflow group data
    print("\n4. Analyzing workflow group assignments...")
    for workflow in workflows:
        print(f"\nWorkflow: {workflow.get('name')} ({workflow.get('id')})")
        print(f"   Public: {workflow.get('public')}")
        print(f"   Allowed Groups: {workflow.get('allowed_groups', 'None')}")
        
        # Check workflow settings if available
        print(f"   Checking workflow settings...")
        settings_response = session.get(f'{BASE_URL}/api/admin/workflows/{workflow.get("id")}/settings/')
        if settings_response.status_code == 200:
            settings = settings_response.json()
            print(f"   Settings allowed_groups: {settings.get('allowed_groups', 'None')}")
        else:
            print(f"   ❌ Settings not accessible: {settings_response.status_code}")
    
    return True

if __name__ == "__main__":
    debug_workflow_groups()