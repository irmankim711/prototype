# API Testing Examples

This document provides comprehensive testing examples for the Production-Ready Automated Report Generation System using cURL commands and Postman collections.

## 🔑 Authentication Setup

First, you'll need to obtain a JWT token. Replace `<your-base-url>` with your actual backend URL (e.g., `http://localhost:5000`).

### Get JWT Token
```bash
curl -X POST <your-base-url>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Save the token for subsequent requests:**
```bash
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## 📊 Report Generation API Tests

### 1. Generate a New Report

```bash
curl -X POST <your-base-url>/api/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2024 Sales Report",
    "description": "Comprehensive sales analysis for Q1 2024",
    "data": {
      "period": "Q1 2024",
      "sales_data": [
        {
          "month": "January",
          "revenue": 125000,
          "units_sold": 1250,
          "growth_rate": 0.15
        }
      ]
    },
    "config": {
      "template": "business_report",
      "include_charts": true,
      "format": ["pdf", "docx", "excel"]
    }
  }'
```

### 2. Check Report Status

```bash
curl -X GET <your-base-url>/api/reports/123/status \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Download Generated Reports

```bash
# Download PDF
curl -X GET <your-base-url>/api/reports/123/download/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o "Q1_2024_Sales_Report.pdf"

# Download DOCX
curl -X GET <your-base-url>/api/reports/123/download/docx \
  -H "Authorization: Bearer $TOKEN" \
  -o "Q1_2024_Sales_Report.docx"

# Download Excel
curl -X GET <your-base-url>/api/reports/123/download/excel \
  -H "Authorization: Bearer $TOKEN" \
  -o "Q1_2024_Sales_Report.xlsx"
```

## 📋 Excel Export API Tests

### 1. Export Form to Excel

```bash
curl -X POST <your-base-url>/api/forms/1/export-excel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-03-31"
    },
    "include_metadata": true,
    "max_records": 10000,
    "immediate": false
  }'
```

### 2. Download Excel Export

```bash
curl -X GET <your-base-url>/api/forms/1/download-excel \
  -H "Authorization: Bearer $TOKEN" \
  -o "Form_1_Export.xlsx"
```

## 🏥 Health Check API Tests

### 1. Overall System Health

```bash
curl -X GET <your-base-url>/api/health
```

### 2. Database Health Check

```bash
curl -X GET <your-base-url>/api/health/database
```

### 3. Worker Health Check

```bash
curl -X GET <your-base-url>/api/health/workers
```

## 🧪 Testing Scripts

### Automated Testing Script

Create a file called `test_api.sh`:

```bash
#!/bin/bash

# Configuration
BASE_URL="http://localhost:5000"
EMAIL="your-email@example.com"
PASSWORD="your-password"

echo "🚀 Starting API Tests for Automated Report System"

# 1. Authentication
echo "1. Testing Authentication..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✅ Authentication successful"

# 2. Health Check
echo "2. Testing Health Check..."
HEALTH_RESPONSE=$(curl -s -X GET "$BASE_URL/api/health")
echo "Health Status: $HEALTH_RESPONSE"

echo "🎉 API Tests Completed Successfully!"
```

### Run the Test Script

```bash
chmod +x test_api.sh
./test_api.sh
```

## 🎯 Success Criteria

Your API tests are successful when:

1. ✅ Authentication returns valid JWT token
2. ✅ Health check shows all services as healthy
3. ✅ Report generation starts successfully
4. ✅ Report status progresses from pending → generating → completed
5. ✅ Files are downloadable (PDF, DOCX, Excel)
6. ✅ Excel export works for forms
7. ✅ Rate limiting is enforced
8. ✅ Error handling works gracefully
9. ✅ Background tasks complete successfully
10. ✅ File cleanup works properly

## 📝 Notes

- Replace `<your-base-url>` with your actual backend URL
- Update email/password in test scripts
- Monitor Celery worker logs during testing
- Check file system permissions for uploads directory
- Verify Redis connection for background tasks
- Monitor database performance during load tests

---

**Happy Testing! 🚀**
