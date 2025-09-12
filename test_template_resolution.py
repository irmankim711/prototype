#!/usr/bin/env python3
"""
Test Template Resolution Fix
Test script to verify the template_id resolution from generation_config works correctly
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Test imports
try:
    from app.routes.reports_api import resolve_template_id
    print("✓ Successfully imported resolve_template_id function")
except ImportError as e:
    print(f"✗ Failed to import resolve_template_id: {e}")
    sys.exit(1)

def test_template_resolution():
    """Test different template resolution scenarios"""
    
    test_cases = [
        # Test case 1: template_used = "Temp1"
        {
            'name': 'template_used = "Temp1"',
            'config': {'template_used': 'Temp1'},
            'expected_type': int
        },
        
        # Test case 2: template_used = "temp1" (case insensitive)
        {
            'name': 'template_used = "temp1" (case insensitive)',
            'config': {'template_used': 'temp1'},
            'expected_type': int
        },
        
        # Test case 3: Empty config (should return default 1)
        {
            'name': 'Empty config (should return default)',
            'config': {},
            'expected_type': int,
            'expected_value': 1
        },
        
        # Test case 4: None config (should return default 1)
        {
            'name': 'None config (should return default)',
            'config': None,
            'expected_type': int,
            'expected_value': 1
        },
        
        # Test case 5: template_uuid
        {
            'name': 'template_uuid = "1"',
            'config': {'template_uuid': '1'},
            'expected_type': int
        }
    ]
    
    print("\n=== Testing Template Resolution ===")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        try:
            result = resolve_template_id(test_case['config'])
            print(f"   Result: {result} (type: {type(result).__name__})")
            
            # Check type
            if isinstance(result, test_case['expected_type']):
                print("   ✓ Type check passed")
            else:
                print(f"   ✗ Type check failed: expected {test_case['expected_type']}, got {type(result)}")
            
            # Check specific value if expected
            if 'expected_value' in test_case:
                if result == test_case['expected_value']:
                    print("   ✓ Value check passed")
                else:
                    print(f"   ✗ Value check failed: expected {test_case['expected_value']}, got {result}")
            else:
                # Just check it's a positive integer
                if isinstance(result, int) and result > 0:
                    print("   ✓ Valid template ID returned")
                else:
                    print(f"   ✗ Invalid template ID: {result}")
                    
        except Exception as e:
            print(f"   ✗ Error: {e}")

if __name__ == '__main__':
    test_template_resolution()