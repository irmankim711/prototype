#!/bin/bash
# Secure Environment Setup Script
# This script helps developers set up their environment variables securely

echo "🔐 Secure Environment Setup for Automated Report Platform"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "📋 Setting up environment files..."

# Backend environment setup
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env from template..."
    cp backend/.env.template backend/.env
    echo "✅ Created backend/.env"
    echo "⚠️  Please edit backend/.env and add your actual API keys and secrets"
else
    echo "ℹ️  backend/.env already exists"
fi

# Frontend environment setup
if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend/.env from template..."
    cp frontend/.env.template frontend/.env
    echo "✅ Created frontend/.env"
    echo "⚠️  Please edit frontend/.env and add your actual API keys"
else
    echo "ℹ️  frontend/.env already exists"
fi

# Check if .env files are in .gitignore
echo "🔍 Checking .gitignore configuration..."
if grep -q "\.env" .gitignore; then
    echo "✅ .env files are properly ignored by Git"
else
    echo "❌ WARNING: .env files are not in .gitignore!"
    echo "Adding .env to .gitignore..."
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
fi

# Check pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hook is installed"
else
    echo "⚠️  Pre-commit hook is not installed"
    echo "This hook prevents accidental commits of API keys"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Edit backend/.env with your actual API keys and secrets"
echo "2. Edit frontend/.env with your actual API keys"
echo "3. Never commit these .env files to version control"
echo "4. Use .env.template files as reference for required variables"
echo ""
echo "🔒 Security Tips:"
echo "- Use different API keys for development and production"
echo "- Rotate your API keys regularly"
echo "- Use environment-specific configurations"
echo "- Monitor your API key usage in the respective dashboards"
echo ""
echo "✅ Environment setup complete!"
