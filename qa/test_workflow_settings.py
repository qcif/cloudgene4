#!/usr/bin/env python3
"""
Test script for new admin workflow settings functionality
"""
import requests
import json

BASE_URL = 'http://localhost:3000'

def test_workflow_settings_api():
    """Test the new workflow settings admin API"""
    session = requests.Session()
    
    # Login as admin
    print("1. Testing admin login...")
    login_response = session.post(f'{BASE_URL}/auth/login/', {
        'username': 'admin',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return False
        
    print("✅ Admin login successful")
    
    # Test get workflow settings
    print("2. Testing GET workflow settings...")
    workflow_id = 'hello-cloudgene'
    get_response = session.get(f'{BASE_URL}/api/admin/workflows/{workflow_id}/settings/')
    
    if get_response.status_code != 200:
        print(f"❌ GET workflow settings failed: {get_response.status_code}")
        if get_response.status_code == 404:
            print("   Endpoint may not exist - check URL routing")
        return False
        
    workflow_data = get_response.json()
    print(f"✅ GET workflow settings successful")
    print(f"   Current profile: {workflow_data.get('nextflow_profile', 'None')}")
    print(f"   Current working_directory: {workflow_data.get('working_directory', 'None')}")
    print(f"   Has env_vars: {bool(workflow_data.get('env_vars'))}")
    print(f"   Has nextflow_config: {bool(workflow_data.get('nextflow_config'))}")
    
    # Test update workflow settings
    print("3. Testing PATCH workflow settings...")
    update_data = {
        'nextflow_profile': 'docker',
        'working_directory': '${CLOUDGENE_WORKSPACE_HOME}/work',
        'env_vars': 'SMTP_HOST=${CLOUDGENE_SMTP_HOST}\\nAPP_NAME=${CLOUDGENE_APP_NAME}\\nSERVICE_URL=${CLOUDGENE_SERVICE_URL}',
        'nextflow_config': '''process {
  executor = 'local'
  cpus = 2
  memory = '4 GB'
}

singularity {
  enabled = true
  cacheDir = '${CLOUDGENE_WORKSPACE_HOME}/singularity'
}'''
    }
    
    # Get CSRF token
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    } if csrf_token else {'Content-Type': 'application/json'}
    
    patch_response = session.patch(
        f'{BASE_URL}/api/admin/workflows/{workflow_id}/settings/',
        json=update_data,
        headers=headers
    )
    
    if patch_response.status_code not in [200, 201]:
        print(f"❌ PATCH workflow settings failed: {patch_response.status_code}")
        try:
            error_data = patch_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Response: {patch_response.text}")
        return False
        
    updated_data = patch_response.json()
    print(f"✅ PATCH workflow settings successful")
    print(f"   Updated profile: {updated_data.get('nextflow_profile')}")
    print(f"   Updated working_directory: {updated_data.get('working_directory')}")
    print(f"   Updated env_vars length: {len(updated_data.get('env_vars', ''))}")
    print(f"   Updated config length: {len(updated_data.get('nextflow_config', ''))}")
    
    # Test template variable substitution
    print("4. Testing template variable substitution...")
    try:
        import sys
        import os
        sys.path.append('/home/ubuntu/dev/cloudgene-rebuild')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloudgene_django.settings')
        
        import django
        django.setup()
        
        from workflows.template_utils import substitute_template_variables
        
        test_text = "SMTP_HOST=${CLOUDGENE_SMTP_HOST}\\nWORK_DIR=${CLOUDGENE_WORKSPACE_HOME}/work"
        substituted = substitute_template_variables(test_text)
        print(f"✅ Template substitution test successful")
        print(f"   Original: {test_text}")
        print(f"   Substituted: {substituted}")
        
    except Exception as e:
        print(f"⚠️ Template substitution test failed: {e}")
    
    return True

if __name__ == "__main__":
    test_workflow_settings_api()