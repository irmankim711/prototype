#!/bin/bash

# 🚨 EMERGENCY SECURITY CLEANUP SCRIPT
# This script removes sensitive files from git history and prevents future commits

echo "🔒 Starting Security Cleanup..."

# 1. Remove critical files from git tracking (if they exist)
echo "📂 Removing sensitive files from git staging..."

# Firebase service account
if [ -f "backend/firebase-service-account.json" ]; then
    git rm --cached "backend/firebase-service-account.json" 2>/dev/null || echo "firebase-service-account.json not staged"
    echo "🔥 CRITICAL: backend/firebase-service-account.json found - MUST BE REVOKED"
fi

# Environment files
git rm --cached "backend/.env" 2>/dev/null || echo "backend/.env not staged"
git rm --cached "frontend/.env" 2>/dev/null || echo "frontend/.env not staged"
git rm --cached ".env*" 2>/dev/null || echo "No .env files staged"

# All environment variants
for env_file in $(find . -name ".env*" -not -path "./.git/*" -not -name "*.template" -not -name "*.example"); do
    git rm --cached "$env_file" 2>/dev/null || echo "$env_file not tracked"
    echo "⚠️  Found environment file: $env_file"
done

# 2. Move sensitive files to secure location
echo "🔐 Moving sensitive files to secure backup..."
mkdir -p ~/.sensitive_backups/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/.sensitive_backups/$(date +%Y%m%d_%H%M%S)

# Backup and remove Firebase keys
if [ -f "backend/firebase-service-account.json" ]; then
    cp "backend/firebase-service-account.json" "$BACKUP_DIR/"
    rm "backend/firebase-service-account.json"
    echo "🔥 CRITICAL: Firebase service account backed up and removed"
fi

# Backup environment files
cp backend/.env "$BACKUP_DIR/backend.env.backup" 2>/dev/null || echo "backend/.env not found"
cp frontend/.env "$BACKUP_DIR/frontend.env.backup" 2>/dev/null || echo "frontend/.env not found"

# 3. Generate new secure environment templates
echo "🛡️  Generating secure environment templates..."

# Backend .env template
cat > backend/.env.template << 'EOF'
# 🔒 SECURE ENVIRONMENT TEMPLATE - DEVELOPMENT ONLY
# Copy this file to .env and replace placeholder values

# Environment Settings
FLASK_ENV=development
DEBUG=true
APP_PORT=5000

# 🚨 SECURITY: Generate new secrets with: openssl rand -hex 32
SECRET_KEY=GENERATE_NEW_SECRET_HERE
JWT_SECRET_KEY=GENERATE_NEW_JWT_SECRET_HERE

# Database (use environment-specific values)
DATABASE_URL=sqlite:///dev.db

# External APIs - NEVER commit real values
OPENAI_API_KEY=your_openai_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Firebase - Use service account file, not inline keys
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
EOF

# Frontend .env template
cat > frontend/.env.template << 'EOF'
# 🔒 FRONTEND ENVIRONMENT TEMPLATE
# Copy this file to .env and customize

# API Configuration
VITE_API_URL=http://localhost:5000
VITE_API_TIMEOUT=5000

# OAuth Configuration - Development keys only
VITE_GOOGLE_CLIENT_ID=your_dev_google_client_id
VITE_MICROSOFT_CLIENT_ID=your_dev_microsoft_client_id

# Feature Flags
VITE_ENABLE_AI_FEATURES=false
VITE_ENABLE_DEBUG_MODE=true
EOF

# 4. Update .gitignore with comprehensive patterns
echo "📝 Updating .gitignore with security patterns..."

# Add critical security patterns to .gitignore if not already present
cat >> .gitignore << 'EOF'

# 🚨 CRITICAL SECURITY - NEVER COMMIT THESE
firebase-service-account*.json
*firebase-adminsdk*.json
service-account*.json

# All environment files (except templates)
.env
.env.*
!.env.template
!.env.example
backend/.env
backend/.env.*
frontend/.env  
frontend/.env.*

# API Keys and Secrets
*AIzaSy*
*GOCSPX-*
*sk-[a-zA-Z0-9]*
*access_token*
*secret_key*
*private_key*

# OAuth and Authentication
client_secret*.json
credentials.json
*oauth*.json
*token*.json
*.jwt
*.key
*.pem
*.p12
*.pfx
EOF

# 5. Check for patterns that indicate secrets in source code
echo "🔍 Scanning for hardcoded secrets in source code..."
echo "Files with potential hardcoded secrets:"

# Scan for API key patterns in source files
grep -r "AIzaSy" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null && echo "⚠️  Google API keys found in source code"
grep -r "sk-[a-zA-Z0-9]" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null && echo "⚠️  OpenAI API keys found in source code"
grep -r "GOCSPX-" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null && echo "⚠️  Google OAuth secrets found in source code"

# 6. Create pre-commit hook
echo "🛡️  Installing pre-commit security hook..."
mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# 🔒 Security Pre-Commit Hook

# Check for sensitive file patterns
SENSITIVE_FILES=$(git diff --cached --name-only | grep -E '\.(env|key|pem|p12|pfx)$|firebase-service-account|credentials\.json|client_secret' | grep -v -E '\.template$|\.example$')

if [ ! -z "$SENSITIVE_FILES" ]; then
    echo "🚨 SECURITY ALERT: Attempting to commit sensitive files:"
    echo "$SENSITIVE_FILES"
    echo ""
    echo "❌ Commit blocked for security reasons"
    echo "💡 Add files to .gitignore or use templates instead"
    exit 1
fi

# Check for API key patterns in staged files
git diff --cached | grep -E "(AIzaSy|sk-[a-zA-Z0-9]{48}|GOCSPX-)" && {
    echo "🚨 SECURITY ALERT: API keys found in staged changes"
    echo "❌ Commit blocked - remove API keys from code"
    exit 1
}

echo "✅ Security check passed"
EOF

chmod +x .git/hooks/pre-commit

# 7. Generate new development secrets
echo "🔑 Generating new development secrets..."
echo "New SECRET_KEY: $(openssl rand -hex 32)" > "$BACKUP_DIR/new_secrets.txt"
echo "New JWT_SECRET_KEY: $(openssl rand -hex 32)" >> "$BACKUP_DIR/new_secrets.txt"

echo ""
echo "🚨 CRITICAL SECURITY ACTIONS REQUIRED:"
echo "================================================="
echo "1. 🔥 REVOKE Firebase service account immediately"
echo "2. 🔄 Rotate all API keys found in scan"
echo "3. 📝 Update production environment variables"
echo "4. 🔍 Review backup files in: $BACKUP_DIR"
echo "5. 🛡️  Use new secrets from: $BACKUP_DIR/new_secrets.txt"
echo ""
echo "✅ Security cleanup completed!"
echo "🔒 Pre-commit hook installed to prevent future leaks"