#!/usr/bin/env python3
"""
Debug the DynamicForm template v-if conditions
Figure out why no child elements are rendering despite correct props
"""

import json
import requests

def debug_template_conditions():
    """Debug exactly why the template conditions aren't matching"""
    print("🔍 DEBUGGING: DynamicForm Template Conditions")
    print("Analyzing why v-if/v-else-if conditions aren't matching\n")
    
    try:
        # Get the actual parameter data
        response = requests.get("http://localhost:8000/api/workflows/hello-cloudgene/", timeout=10)
        workflow_data = response.json()
        parameters = workflow_data.get('parameters', [])
        
        print(f"📋 Analyzing {len(parameters)} parameters...\n")
        
        # Read the DynamicForm template to get the exact conditions
        with open('/home/ubuntu/dev/cloudgene-rebuild/frontend/src/components/workflows/form/DynamicForm.vue', 'r') as f:
            template_content = f.read()
        
        # Extract the condition sets from the template
        print("🔍 Template Condition Analysis:")
        
        for i, param in enumerate(parameters):
            param_id = param.get('id', param.get('parameter_id', 'unknown'))
            param_type = param.get('type', param.get('parameter_type', 'unknown'))
            
            print(f"\n{i+1}. Parameter '{param_id}':")
            print(f"   param.type = '{param_type}'")
            
            # Check each condition from the template
            conditions_checked = []
            
            # From DynamicForm.vue template:
            
            # v-if="param.type === 'separator'"
            cond1 = param_type == 'separator'
            conditions_checked.append(('separator', cond1))
            print(f"   ❓ param.type === 'separator': {cond1}")
            
            # v-else-if="param.type === 'info' || param.type === 'label'"
            cond2 = param_type == 'info' or param_type == 'label'
            conditions_checked.append(('info/label', cond2))
            print(f"   ❓ param.type === 'info' || 'label': {cond2}")
            
            # v-else-if="TEXT_TYPES.has(param.type)"
            # TEXT_TYPES = new Set(['text', 'number', 'string'])
            text_types = {'text', 'number', 'string'}
            cond3 = param_type in text_types
            conditions_checked.append(('text_types', cond3))
            print(f"   ❓ TEXT_TYPES.has('{param_type}'): {cond3}")
            
            # v-else-if="param.type === 'textarea'"
            cond4 = param_type == 'textarea'
            conditions_checked.append(('textarea', cond4))
            print(f"   ❓ param.type === 'textarea': {cond4}")
            
            # v-else-if="param.type === 'list' || param.type === 'binded_list' || param.type === 'app_list'"
            cond5 = param_type in ['list', 'binded_list', 'app_list']
            conditions_checked.append(('list_types', cond5))
            print(f"   ❓ list types: {cond5}")
            
            # v-else-if="param.type === 'radio'"
            cond6 = param_type == 'radio'
            conditions_checked.append(('radio', cond6))
            print(f"   ❓ param.type === 'radio': {cond6}")
            
            # v-else-if="param.type === 'checkbox' || param.type === 'agb_checkbox'"
            cond7 = param_type in ['checkbox', 'agb_checkbox']
            conditions_checked.append(('checkbox_types', cond7))
            print(f"   ❓ checkbox types: {cond7}")
            
            # v-else-if="param.type === 'terms_checkbox'"
            cond8 = param_type == 'terms_checkbox'
            conditions_checked.append(('terms_checkbox', cond8))
            print(f"   ❓ param.type === 'terms_checkbox': {cond8}")
            
            # v-else-if="FILE_TYPES.has(param.type)"
            # FILE_TYPES = new Set(['local_file', 'hdfs_file'])
            file_types = {'local_file', 'hdfs_file'}
            cond9 = param_type in file_types
            conditions_checked.append(('file_types', cond9))
            print(f"   ❓ FILE_TYPES.has('{param_type}'): {cond9}")
            
            # v-else-if="FOLDER_TYPES.has(param.type)"
            # FOLDER_TYPES = new Set(['local_folder', 'hdfs_folder'])
            folder_types = {'local_folder', 'hdfs_folder'}
            cond10 = param_type in folder_types
            conditions_checked.append(('folder_types', cond10))
            print(f"   ❓ FOLDER_TYPES.has('{param_type}'): {cond10}")
            
            # Check if ANY condition matched
            any_matched = any(cond[1] for cond in conditions_checked)
            print(f"   🎯 ANY condition matches: {'✅ YES' if any_matched else '❌ NO - WILL NOT RENDER'}")
            
            if not any_matched:
                print(f"   🚨 PROBLEM: This parameter will render NOTHING!")
                print(f"      The v-for loop will have an empty body for this param")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        total_params = len(parameters)
        
        # Count how many would render nothing
        no_render_count = 0
        for param in parameters:
            param_type = param.get('type', param.get('parameter_type', ''))
            
            # Check all conditions
            if not any([
                param_type == 'separator',
                param_type in ['info', 'label'],
                param_type in ['text', 'number', 'string'],
                param_type == 'textarea',
                param_type in ['list', 'binded_list', 'app_list'],
                param_type == 'radio',
                param_type in ['checkbox', 'agb_checkbox'],
                param_type == 'terms_checkbox',
                param_type in ['local_file', 'hdfs_file'],
                param_type in ['local_folder', 'hdfs_folder']
            ]):
                no_render_count += 1
        
        print(f"   Total parameters: {total_params}")
        print(f"   Parameters that won't render: {no_render_count}")
        print(f"   Parameters that should render: {total_params - no_render_count}")
        
        if no_render_count == total_params:
            print(f"\n🚨 ROOT CAUSE IDENTIFIED:")
            print(f"   ALL parameters fail to match ANY template condition!")
            print(f"   This explains why DynamicForm renders nothing.")
            
            # Show what the types actually are vs what template expects
            print(f"\n🔍 TYPE MISMATCH ANALYSIS:")
            actual_types = [p.get('type', p.get('parameter_type', '')) for p in parameters]
            print(f"   Actual types in data: {set(actual_types)}")
            
            expected_types = {
                'text', 'number', 'string', 'textarea', 'list', 'binded_list', 'app_list',
                'radio', 'checkbox', 'agb_checkbox', 'terms_checkbox', 'separator', 'info', 'label',
                'local_file', 'hdfs_file', 'local_folder', 'hdfs_folder'
            }
            print(f"   Expected types in template: {expected_types}")
            
            missing_types = set(actual_types) - expected_types
            if missing_types:
                print(f"   🎯 MISSING from template: {missing_types}")
                print(f"   ➡️  These types need to be added to DynamicForm template!")
                return False
            else:
                print(f"   🤔 All types are supported... there may be another issue")
                return True
        else:
            print(f"\n✅ Some parameters should render correctly")
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

def main():
    """Run the template condition debugging"""
    success = debug_template_conditions()
    
    if success:
        print("\n🎯 Template conditions look OK - may be another issue")
    else:
        print("\n🔧 Template conditions need to be updated!")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())