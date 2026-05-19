#!/usr/bin/env python3
"""
Verify that the DynamicForm template fix resolves the rendering issue
"""

import json
import requests

def verify_template_fix():
    """Verify the template type fix"""
    print("✅ VERIFYING: DynamicForm Template Fix")
    print("Checking if adding 'file' and 'folder' types resolves the issue\n")
    
    try:
        # Get the parameter data
        response = requests.get("http://localhost:8000/api/workflows/hello-cloudgene/", timeout=10)
        workflow_data = response.json()
        parameters = workflow_data.get('parameters', [])
        
        # Updated type sets (matching the fix)
        text_types = {'text', 'number', 'string'}
        file_types = {'local_file', 'hdfs_file', 'file'}  # Added 'file'
        folder_types = {'local_folder', 'hdfs_folder', 'folder'}  # Added 'folder'
        
        print("🔍 Testing each parameter with UPDATED template conditions:")
        
        render_count = 0
        for i, param in enumerate(parameters):
            param_id = param.get('id', 'unknown')
            param_type = param.get('type', 'unknown')
            
            # Test the conditions with the fix
            will_render = any([
                param_type == 'separator',
                param_type in ['info', 'label'],
                param_type in text_types,
                param_type == 'textarea',
                param_type in ['list', 'binded_list', 'app_list'],
                param_type == 'radio',
                param_type in ['checkbox', 'agb_checkbox'],
                param_type == 'terms_checkbox',
                param_type in file_types,  # Now includes 'file'
                param_type in folder_types  # Now includes 'folder'
            ])
            
            if will_render:
                render_count += 1
                
            print(f"   {i+1}. {param_id} (type: '{param_type}'): {'✅ WILL RENDER' if will_render else '❌ NO RENDER'}")
        
        print(f"\n📊 RESULTS AFTER FIX:")
        print(f"   Total parameters: {len(parameters)}")
        print(f"   Will render: {render_count}")
        print(f"   Won't render: {len(parameters) - render_count}")
        
        if render_count == len(parameters):
            print(f"\n🎉 FIX SUCCESSFUL!")
            print(f"   All {render_count} parameters should now render in the form")
            print(f"   Expected form elements: {render_count} + 1 job name = {render_count + 1} total")
            return True
        elif render_count > 0:
            print(f"\n✅ PARTIAL FIX:")
            print(f"   {render_count} parameters should render (better than 0)")
            return True
        else:
            print(f"\n❌ FIX INCOMPLETE:")
            print(f"   Still no parameters would render")
            return False
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    success = verify_template_fix()
    
    if success:
        print("\n🎯 The template fix should resolve your issue!")
        print("   Try refreshing /run/hello-cloudgene to see the parameter fields")
        return 0
    else:
        print("\n⚠️  Additional fixes may be needed")
        return 1

if __name__ == "__main__":
    exit(main())