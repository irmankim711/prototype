import requests
import json

# Test the AI functionality endpoints
BASE_URL = "http://127.0.0.1:5000"

def test_ai_health():
    """Test AI health check endpoint"""
    print("Testing AI Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/mvp/ai/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ai_analyze():
    """Test AI data analysis endpoint"""
    print("\nTesting AI Data Analysis...")
    try:
        test_data = {
            "context": "financial",
            "data": {
                "revenue": 1250000,
                "expenses": 980000,
                "profit_margin": 0.216,
                "employees": 25,
                "growth_rate": 0.15,
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
                "quarterly_revenue": [300000, 320000, 315000, 315000]
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/mvp/ai/analyze", json=test_data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Summary: {result.get('summary', 'No summary')}")
        print(f"Insights: {result.get('insights', [])}")
        print(f"Recommendations: {result.get('recommendations', [])}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ai_report_suggestions():
    """Test AI report suggestions endpoint"""
    print("\nTesting AI Report Suggestions...")
    try:
        test_data = {
            "report_type": "quarterly_financial",
            "data": {
                "period": "Q4 2024",
                "revenue": 1250000,
                "profit": 270000,
                "team_size": 25,
                "key_projects": 3
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/mvp/ai/report-suggestions", json=test_data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        if result.get('suggestions'):
            print("Suggestions available!")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ai_smart_placeholders():
    """Test AI smart placeholders endpoint"""
    print("\nTesting AI Smart Placeholders...")
    try:
        test_data = {
            "context": "financial",
            "industry": "technology"
        }
        
        response = requests.post(f"{BASE_URL}/api/mvp/ai/smart-placeholders", json=test_data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        if result.get('placeholders'):
            print("Placeholders generated!")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ai_data_validation():
    """Test AI data validation endpoint"""
    print("\nTesting AI Data Validation...")
    try:
        test_data = {
            "data": {
                "name": "John Doe",
                "age": 25,
                "salary": 50000,
                "department": "Engineering",
                "join_date": "2024-01-15",
                "incomplete_field": ""
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/mvp/ai/validate-data", json=test_data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        if result.get('validation'):
            quality_score = result['validation'].get('overall_quality_score', 0)
            print(f"Data Quality Score: {quality_score}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting AI Functionality Tests...")
    print("="*50)
    
    # Run all tests
    tests = [
        test_ai_health,
        test_ai_analyze,
        test_ai_report_suggestions,
        test_ai_smart_placeholders,
        test_ai_data_validation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nTest Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All AI functionality tests passed!")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
