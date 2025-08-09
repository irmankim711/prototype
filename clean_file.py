#!/usr/bin/env python3
"""
Clean null bytes from Python files
"""

def clean_null_bytes(file_path):
    """Remove null bytes from a Python file"""
    try:
        print(f"Cleaning file: {file_path}")
        
        # Read the file with error handling
        with open(file_path, 'rb') as f:
            content = f.read()
        
        print(f"Original file size: {len(content)} bytes")
        
        # Count null bytes
        null_count = content.count(b'\x00')
        print(f"Found {null_count} null bytes")
        
        if null_count > 0:
            # Remove null bytes
            cleaned_content = content.replace(b'\x00', b'')
            
            # Write back as UTF-8
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content.decode('utf-8', errors='ignore'))
            
            print(f"Successfully cleaned {file_path} - removed {null_count} null bytes")
        else:
            print(f"No null bytes found in {file_path}")
        
    except Exception as e:
        print(f"Error cleaning file: {e}")

def main():
    # Files to clean
    files_to_clean = [
        r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\services\automated_report_system.py",
        r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\services\enhanced_report_service.py",
        r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\services\google_forms_service.py"
    ]
    
    for file_path in files_to_clean:
        try:
            clean_null_bytes(file_path)
            print("-" * 50)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            print("-" * 50)

if __name__ == "__main__":
    main()
