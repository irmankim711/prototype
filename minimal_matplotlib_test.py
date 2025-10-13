#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Minimal matplotlib test to isolate the null bytes issue
"""

def test_minimal_matplotlib():
    print("Testing minimal matplotlib...")
    
    try:
        import matplotlib
        print(f"Matplotlib version: {matplotlib.__version__}")
        
        matplotlib.use('Agg')
        print("Backend set to Agg")
        
        import matplotlib.pyplot as plt
        print("pyplot imported successfully")
        
        # Simple plot
        plt.figure(figsize=(6, 4))
        plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
        plt.title('Simple Test Plot')
        
        # Save to current directory
        import os
        chart_path = os.path.join(os.getcwd(), 'minimal_test_chart.png')
        plt.savefig(chart_path)
        plt.close()
        
        if os.path.exists(chart_path):
            print(f"SUCCESS: Chart saved to {chart_path}")
            return True
        else:
            print("FAILED: Chart not saved")
            return False
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_minimal_matplotlib()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
