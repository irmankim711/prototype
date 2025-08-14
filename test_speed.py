#!/usr/bin/env python3
"""
Quick test to measure form creation click speed
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_form_creation_speed():
    print("🏃‍♂️ Testing Form Creation Speed...")
    
    # Set up Chrome in headless mode for speed
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:5173")
        
        print("📄 Page loaded, measuring form creation speed...")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find the "Create New Form" button
        start_time = time.time()
        
        try:
            create_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create New Form')]"))
            )
            
            # Click the button
            click_time = time.time()
            create_button.click()
            
            # Wait for form builder to appear (look for form title input)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@label='Form Title' or contains(@placeholder, 'Form Title')]"))
            )
            
            load_time = time.time()
            
            total_time = (load_time - click_time) * 1000  # Convert to ms
            
            print(f"✅ SUCCESS!")
            print(f"🕐 Form Builder Load Time: {total_time:.0f}ms")
            
            if total_time < 1000:
                print("🚀 EXCELLENT: Form loads in under 1 second!")
            elif total_time < 2000:
                print("👍 GOOD: Form loads in under 2 seconds")
            else:
                print("⚠️  SLOW: Form takes over 2 seconds to load")
                
        except Exception as e:
            print(f"❌ Could not find Create New Form button: {e}")
            print("📝 This might be because authentication is required")
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        print("💡 Make sure Chrome is installed and frontend is running on localhost:5173")
    
    finally:
        if 'driver' in locals():
            driver.quit()

def test_basic_connectivity():
    """Test if servers are responsive"""
    print("\n🔌 Testing Server Connectivity...")
    
    try:
        # Test frontend
        frontend_start = time.time()
        response = requests.get("http://localhost:5173", timeout=5)
        frontend_time = (time.time() - frontend_start) * 1000
        
        print(f"📱 Frontend: {response.status_code} ({frontend_time:.0f}ms)")
        
        # Test backend
        backend_start = time.time()
        response = requests.get("http://localhost:5000/health", timeout=5)
        backend_time = (time.time() - backend_start) * 1000
        
        print(f"⚙️  Backend: {response.status_code} ({backend_time:.0f}ms)")
        
    except Exception as e:
        print(f"❌ Server connectivity test failed: {e}")

if __name__ == "__main__":
    test_basic_connectivity()
    test_form_creation_speed()
