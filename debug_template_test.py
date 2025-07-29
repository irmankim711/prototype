#!/usr/bin/env python3
"""
Simple debug test for template optimizer
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the backend path to sys.path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    from app.services.template_optimizer import TemplateOptimizerService
    print("✓ Successfully imported TemplateOptimizerService")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_simple_optimization():
    """Test template optimization with minimal data."""
    
    print("🔧 Creating simple test data...")
    
    # Create minimal Excel file
    data = {
        'Field': ['Title', 'Date', 'Location', 'Total Participants'],
        'Value': ['Test Program', '2025-01-01', 'Test Venue', '50']
    }
    df = pd.DataFrame(data)
    excel_file = 'debug_test.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"✓ Created test Excel file: {excel_file}")
    
    # Create minimal template
    template_content = """
\\documentclass{article}
\\begin{document}
\\title{{{program.title}}}
\\section{Program Information}
Date: {{program.date}}
Location: {{program.location}}
Total Participants: {{program.total_participants}}
\\end{document}
"""
    
    template_file = 'debug_template.tex'
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    print(f"✓ Created test template: {template_file}")
    
    # Test the optimizer
    print("\\n🧪 Testing template optimizer...")
    try:
        optimizer = TemplateOptimizerService()
        print("✓ Created optimizer instance")
        
        result = optimizer.optimize_template_with_excel(template_content, excel_file)
        print("✓ Optimization completed")
        
        if result['success']:
            print("✅ Template optimization successful!")
            print(f"   Context keys: {list(result.get('enhanced_context', {}).keys())}")
            print(f"   Missing fields: {len(result.get('missing_fields', []))}")
        else:
            print(f"❌ Optimization failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Exception during optimization: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        for file in [excel_file, template_file]:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️ Cleaned up: {file}")

if __name__ == "__main__":
    test_simple_optimization()
