#!/usr/bin/env python3
"""
Debug the exact workflow rendering issue 
Simulates the full data flow from API to Vue component
"""

import json
import requests

def debug_workflow_data_flow():
    """Debug exactly what data the Vue component receives"""
    print("🔬 DEBUGGING: Workflow Form Rendering Data Flow")
    print("Tracing the exact path from API → Vue component → DOM\n")
    
    try:
        # Step 1: API Call (what WorkflowSubmitView.vue does in onMounted)
        print("1️⃣ API Call: GET /api/workflows/hello-cloudgene/")
        response = requests.get("http://localhost:8000/api/workflows/hello-cloudgene/", timeout=10)
        workflow_data = response.json()
        
        print(f"   ✅ Status: {response.status_code}")
        print(f"   ✅ Has parameters: {len(workflow_data.get('parameters', []))} found")
        
        # Step 2: Parameter filtering (what inputParams() function does)
        print("\n2️⃣ Parameter Filtering:")
        all_params = workflow_data.get('parameters', [])
        
        # Using the EXACT logic from WorkflowSubmitView.vue line 32 (before our fix)
        filtered_params = [p for p in all_params if p.get('direction') == 'input' or not p.get('direction')]
        print(f"   Original filter result: {len(filtered_params)} parameters")
        
        # Step 3: What DynamicForm receives as props
        print("\n3️⃣ DynamicForm Props (:params=\"inputParams()\"):")
        print(f"   Receives array of {len(filtered_params)} parameter objects")
        
        if not filtered_params:
            print("   ❌ NO PARAMETERS - This would explain empty form!")
            return False
        
        # Step 4: DynamicForm template rendering simulation
        print("\n4️⃣ DynamicForm Template Rendering:")
        print("   For each parameter, checking v-if conditions...")
        
        rendered_components = []
        
        for i, param in enumerate(filtered_params[:3]):  # Check first 3
            param_id = param.get('id', 'MISSING_ID')
            param_type = param.get('type', 'MISSING_TYPE')
            
            print(f"\n   Parameter {i+1}:")
            print(f"     id: '{param_id}'")
            print(f"     type: '{param_type}'")
            
            # Simulate the v-for and v-if logic from DynamicForm.vue
            if param_type == 'separator':
                rendered_components.append('HR')
                print(f"     → Renders: <hr>")
            elif param_type in ['info', 'label']:
                rendered_components.append('INFO')
                print(f"     → Renders: <p> (info)")
            elif param_type in ['text', 'number', 'string']:
                rendered_components.append('TEXT_INPUT')
                print(f"     → Renders: TextInput component")
            elif param_type == 'textarea':
                rendered_components.append('TEXTAREA')
                print(f"     → Renders: TextareaInput component")
            elif param_type in ['list', 'binded_list', 'app_list']:
                rendered_components.append('SELECT')
                print(f"     → Renders: SelectInput component")
            elif param_type == 'radio':
                rendered_components.append('RADIO')
                print(f"     → Renders: RadioInput component")
            elif param_type in ['checkbox', 'agb_checkbox']:
                rendered_components.append('CHECKBOX')
                print(f"     → Renders: CheckboxInput component")
            elif param_type == 'terms_checkbox':
                rendered_components.append('TERMS')
                print(f"     → Renders: TermsInput component")
            elif param_type in ['local_file', 'hdfs_file', 'file']:
                rendered_components.append('FILE_INPUT')
                print(f"     → Renders: FileInput component (single)")
            elif param_type in ['local_folder', 'hdfs_folder', 'folder']:
                rendered_components.append('FOLDER_INPUT')  
                print(f"     → Renders: FileInput component (multiple)")
            else:
                rendered_components.append('NONE')
                print(f"     → Renders: NOTHING (no matching v-if condition)")
        
        print(f"\n5️⃣ Final Rendering Result:")
        print(f"   Components that would render: {len([c for c in rendered_components if c != 'NONE'])}")
        print(f"   Components: {rendered_components}")
        
        # The key insight
        if len([c for c in rendered_components if c != 'NONE']) == 0:
            print(f"\n❌ PROBLEM IDENTIFIED:")
            print(f"   No components would render! This explains the empty form.")
            print(f"   Check parameter types - they may not match the v-if conditions.")
            return False
        else:
            print(f"\n✅ COMPONENTS SHOULD RENDER:")
            print(f"   The form should show multiple input fields beyond just job name.")
            
            # If components should render but user sees only job name, 
            # the issue might be:
            print(f"\n🤔 If you still see only job name field, possible causes:")
            print(f"   1. JavaScript errors preventing component execution")
            print(f"   2. CSS hiding the rendered components")
            print(f"   3. Vue reactivity issues with data updates")
            print(f"   4. API call timing - components render before data loads")
            print(f"   5. The route /run/hello-cloudgene may not be configured properly")
            
            return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

def check_vue_router_config():
    """Check if the route is configured properly"""
    print("\n6️⃣ Vue Router Configuration Check:")
    try:
        with open('/home/ubuntu/dev/cloudgene-rebuild/frontend/src/router/index.js', 'r') as f:
            router_content = f.read()
        
        has_workflow_route = '/run/:workflowId' in router_content or 'WorkflowSubmit' in router_content
        print(f"   Has workflow submission route: {has_workflow_route}")
        
        if not has_workflow_route:
            print("   ❌ Missing route configuration - this could cause 404 or empty page")
            return False
        else:
            print("   ✅ Route appears to be configured")
            return True
            
    except Exception as e:
        print(f"   ❌ Could not check router config: {e}")
        return False

def main():
    """Run the debugging analysis"""
    data_flow_ok = debug_workflow_data_flow()
    router_ok = check_vue_router_config()
    
    if data_flow_ok and router_ok:
        print("\n🎯 DEBUGGING CONCLUSION:")
        print("   The backend data and frontend logic appear correct.")
        print("   If you still see only the job name field, the issue is likely:")
        print("   - JavaScript runtime errors")
        print("   - CSS/styling issues")  
        print("   - Vue component lifecycle problems")
        print("   - Browser caching of old code")
        print("\n   Try: Hard refresh (Ctrl+F5) and check browser console for errors")
        return 0
    else:
        print("\n❌ ISSUES FOUND in the data flow or routing")
        return 1

if __name__ == "__main__":
    exit(main())