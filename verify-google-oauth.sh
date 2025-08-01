#!/bin/bash

echo "🔧 Google OAuth Setup Verification Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Verify Client IDs match
echo -e "\n${YELLOW}📋 Step 1: Checking Client ID Configuration${NC}"

CLIENT_ID_IN_JSON="1008582896300-73rpvjuobgce2htujji13p7l8tuh6eef.apps.googleusercontent.com"
CLIENT_ID_IN_ENV=$(grep "client_id=" backend/.env | cut -d'=' -f2)
CLIENT_ID_IN_HTML=$(grep "data-client_id=" frontend/index.html | sed 's/.*data-client_id="\([^"]*\)".*/\1/')

echo "Client ID in JSON file: $CLIENT_ID_IN_JSON"
echo "Client ID in backend/.env: $CLIENT_ID_IN_ENV"
echo "Client ID in frontend/index.html: $CLIENT_ID_IN_HTML"

if [ "$CLIENT_ID_IN_JSON" = "$CLIENT_ID_IN_ENV" ] && [ "$CLIENT_ID_IN_JSON" = "$CLIENT_ID_IN_HTML" ]; then
    echo -e "${GREEN}✅ All Client IDs match!${NC}"
else
    echo -e "${RED}❌ Client IDs don't match. Please verify configuration.${NC}"
fi

# Check 2: Verify CORS Configuration
echo -e "\n${YELLOW}📋 Step 2: Checking CORS Configuration${NC}"

if grep -q "http://localhost:5173" backend/app/__init__.py; then
    echo -e "${GREEN}✅ CORS allows localhost:5173${NC}"
else
    echo -e "${RED}❌ CORS might not be configured for localhost:5173${NC}"
fi

# Check 3: Verify Vite Configuration
echo -e "\n${YELLOW}📋 Step 3: Checking Vite Configuration${NC}"

if grep -q "5173" frontend/vite.config.ts; then
    echo -e "${GREEN}✅ Vite configured for port 5173${NC}"
else
    echo -e "${YELLOW}⚠️  Vite might not be configured for port 5173${NC}"
fi

# Check 4: Dependencies
echo -e "\n${YELLOW}📋 Step 4: Checking Dependencies${NC}"

if [ -f "backend/requirements.txt" ] && grep -q "flask-cors" backend/requirements.txt; then
    echo -e "${GREEN}✅ Flask-CORS is in requirements.txt${NC}"
else
    echo -e "${RED}❌ Flask-CORS might be missing from requirements.txt${NC}"
fi

if [ -f "frontend/package.json" ] && grep -q "axios" frontend/package.json; then
    echo -e "${GREEN}✅ Axios is in package.json${NC}"
else
    echo -e "${RED}❌ Axios might be missing from package.json${NC}"
fi

echo -e "\n${YELLOW}🧪 Next Steps for Testing:${NC}"
echo "1. Make sure Google Cloud Console has these origins:"
echo "   - http://localhost:5173 (JavaScript origins)"
echo "   - http://localhost:5000/api/quick-auth/google-signin (Redirect URIs if needed)"
echo ""
echo "2. Start the backend:"
echo "   cd backend && python run.py"
echo ""
echo "3. Start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:5173 and test Google Sign-In"
echo ""
echo "5. Check browser DevTools for any CORS or JavaScript errors"

echo -e "\n${GREEN}🎉 Setup verification complete!${NC}"
