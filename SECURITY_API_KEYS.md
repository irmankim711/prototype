# API Keys and Secrets Security Guide

## 🚨 CRITICAL SECURITY MEASURES IMPLEMENTED

This project has comprehensive protections against API key exposure:

### 1. Git Ignore Protection

- All `.env` files are ignored by Git
- Comprehensive patterns for API keys, secrets, and tokens
- Template files provided for safe reference

### 2. Pre-commit Hook

- Automatically scans for sensitive files and content
- Prevents commits containing API keys or secrets
- Checks for common patterns:
  - API keys (Google, OpenAI, etc.)
  - Client secrets
  - Access tokens
  - Passwords
  - Private keys

### 3. Environment File Structure

```
project/
├── .env.template          # Safe template files
├── .env                   # Your actual secrets (NEVER COMMIT)
├── frontend/
│   ├── .env.template      # Frontend template
│   └── .env               # Frontend secrets (NEVER COMMIT)
└── backend/
    ├── .env.template      # Backend template
    └── .env               # Backend secrets (NEVER COMMIT)
```

## 🔧 Setup Instructions

### For New Developers

1. Run the setup script:

   ```bash
   # Linux/Mac
   ./setup-env.sh

   # Windows
   .\setup-env.ps1
   ```

2. Edit the `.env` files with your actual API keys
3. Never commit `.env` files to version control

### Manual Setup

1. Copy template files:

   ```bash
   cp backend/.env.template backend/.env
   cp frontend/.env.template frontend/.env
   ```

2. Fill in your actual API keys in the `.env` files
3. Verify `.env` files are in `.gitignore`

## 🔑 Required API Keys

### Google APIs

- **Google Client ID**: Get from [Google Cloud Console](https://console.cloud.google.com/)
- **Google Client Secret**: From Google Cloud Console
- **Google API Key**: For accessing Google Forms API

### Optional APIs

- **OpenAI API Key**: For AI features
- **Microsoft Client ID/Secret**: For Microsoft integration

## 🛡️ Security Best Practices

### 1. Environment Separation

- Use different API keys for development/production
- Never use production keys in development
- Rotate keys regularly

### 2. Key Management

- Store production keys in secure environment variables
- Use key management services for production
- Monitor API key usage and quotas

### 3. Access Control

- Restrict API key permissions to minimum required
- Use domain restrictions where possible
- Enable audit logging

## ⚠️ What NOT to Do

❌ **NEVER** commit files containing:

- API keys
- Client secrets
- Access tokens
- Passwords
- Private keys
- Database credentials

❌ **NEVER** share API keys in:

- Chat messages
- Email
- Screenshots
- Documentation
- Comments in code

## 🔍 Detection and Prevention

### Pre-commit Hook Patterns

The pre-commit hook detects:

- Google API keys (`AIzaSy...`)
- Google Client Secrets (`GOCSPX-...`)
- OpenAI keys (`sk-...`)
- Slack tokens (`xox...`)
- GitHub tokens (`github_pat_...`)
- Generic API key patterns

### File Patterns Blocked

- `.env` files (unless templates)
- `credentials.json`
- `client_secret_*.json`
- Files containing `api_key`, `secret`, `token`

## 🚨 If You Accidentally Commit API Keys

1. **Immediately revoke the exposed keys**
2. **Generate new keys**
3. **Update your environment files**
4. **Consider using git-filter-repo to clean history**:
   ```bash
   git filter-repo --invert-paths --path-regex '.*\.env$'
   ```

## 📞 Support

If you need help with:

- Setting up API keys
- Configuring OAuth
- Security questions

Contact the development team or check the main README.md file.

---

**Remember: Security is everyone's responsibility! 🔒**
