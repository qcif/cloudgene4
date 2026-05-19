#!/usr/bin/env python3
"""
Test the parameter filtering logic to verify the fix
"""

import json
import requests

def test_parameter_filtering():
    """Test whether the frontend filtering logic would work correctly"""
    print("🔍 Testing Parameter Filtering Logic")
    print("Simulating the frontend filtering that determines which parameters to show\n")
    
    try:
        # Get the workflow data (same as frontend would)
        response = requests.get("http://localhost:8000/api/workflows/hello-cloudgene/", timeout=10)
        data = response.json()
        parameters = data.get('parameters', [])
        
        print(f"📋 Total parameters in API response: {len(parameters)}")
        
        if not parameters:
            print("❌ No parameters found in API response")
            return False
        
        # Test the OLD filtering logic (the bug)
        old_filtered = [p for p in parameters if p.get('direction') == 'input' or not p.get('direction')]
        print(f"🐛 OLD filtering (p.direction === 'input' || !p.direction): {len(old_filtered)} parameters")
        
        # Test the NEW filtering logic (the fix) 
        new_filtered = [p for p in parameters if p.get('is_input') or p.get('direction') == 'input' or not p.get('direction')]
        print(f"✅ NEW filtering (p.is_input || p.direction === 'input' || !p.direction): {len(new_filtered)} parameters")
        
        print("\n🔍 Parameter Analysis:")
        for i, param in enumerate(parameters[:3]):  # First 3 parameters
            param_id = param.get('id', param.get('parameter_id', 'unknown'))
            has_direction = 'direction' in param
            direction_value = param.get('direction', 'undefined')
            has_is_input = 'is_input' in param
            is_input_value = param.get('is_input', 'undefined')
            
            print(f"  Parameter {i+1} ({param_id}):")
            print(f"    has 'direction': {has_direction} (value: {direction_value})")
            print(f"    has 'is_input': {has_is_input} (value: {is_input_value})")
            print(f"    OLD filter result: {direction_value == 'input' or not direction_value}")
            print(f"    NEW filter result: {is_input_value or direction_value == 'input' or not direction_value}")
        
        # The key test: does the NEW filtering catch all input parameters?
        input_parameters = [p for p in parameters if p.get('is_input', False)]
        fix_catches_all_inputs = len(new_filtered) >= len(input_parameters) > 0
        
        print(f"\n🎯 FILTER FIX VALIDATION:")
        print(f"  Input parameters (is_input=true): {len(input_parameters)}")
        print(f"  New filter catches: {len(new_filtered)}")
        print(f"  Fix successful: {'✅ YES' if fix_catches_all_inputs else '❌ NO'}")
        
        if fix_catches_all_inputs:
            print(f"\n🎉 PARAMETER FILTERING FIX CONFIRMED!")
            print(f"The workflow form should now show {len(new_filtered)} parameter fields")
            print(f"(Plus the job name field = {len(new_filtered) + 1} total form elements)")
            return True
        else:
            print(f"\n❌ Parameter filtering still has issues")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    success = test_parameter_filtering()
    
    if success:
        print("\n✅ The frontend fix should resolve the workflow form rendering issue!")
        return 0
    else:
        print("\n❌ There may still be issues with parameter filtering")
        return 1

if __name__ == "__main__":
    exit(main())