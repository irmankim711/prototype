# 🔐 Environment Setup Guide

## 🚨 **CRITICAL: Security Update**

**Date**: July 20, 2025  
**Issue**: OpenAI API key was exposed in Git history  
**Action Taken**: Removed from history, rotated API key, updated security practices

## 📋 **Required Environment Files**

### 1. Backend Environment (`backend/.env`)
```bash
# Copy the example file
cp backend/env.example backend/.env

# Update with your credentials:
OPENAI_API_KEY=sk-your-new-api-key-here
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this
```

### 2. Auth Backend Environment (`auth-backend/.env`)
```bash
# Copy the example file
cp auth-backend/env.example auth-backend/.env

# Update with your credentials:
JWT_ACCESS_SECRET=your-jwt-access-secret-change-this
JWT_REFRESH_SECRET=your-jwt-refresh-secret-change-this
DATABASE_URL=your-database-connection-string
```

## 🔑 **API Keys & Credentials Setup**

### **OpenAI API Key**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Replace `sk-your-new-api-key-here` in `backend/.env`

### **Google OAuth (if using)**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Download the JSON file as `auth-backend/google-credentials.json`
4. Update `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `auth-backend/.env`

### **Database Setup**
- **Development**: SQLite (default)
- **Production**: PostgreSQL or MySQL
- Update `DATABASE_URL` in respective `.env` files

## 🛡️ **Security Best Practices**

### **✅ DO:**
- Use environment variables for all secrets
- Copy from `.env.example` files
- Rotate keys immediately if exposed
- Use strong, unique secrets for each environment

### **❌ DON'T:**
- Commit `.env` files to Git
- Share API keys in chat/email
- Use the same secrets across environments
- Store secrets in code

## 🔄 **Key Rotation Process**

If any secret is exposed:

1. **Immediately revoke** the exposed key
2. **Generate new key** from the service provider
3. **Update all environments** with the new key
4. **Notify team** about the rotation
5. **Update this document** with the date

## 📁 **File Structure**
```
prototype/
├── backend/
│   ├── .env                 # 🔒 Local secrets (not in Git)
│   └── env.example         # 📝 Template for team
├── auth-backend/
│   ├── .env                # 🔒 Local secrets (not in Git)
│   └── env.example         # 📝 Template for team
└── .gitignore              # 🛡️ Protects secrets
```

## 🚀 **Quick Setup for New Team Members**

1. **Clone the repository**
   ```bash
   git clone https://github.com/irmankim711/prototype.git
   cd prototype
   ```

2. **Create environment files**
   ```bash
   # Backend
   cp backend/env.example backend/.env
   
   # Auth Backend
   cp auth-backend/env.example auth-backend/.env
   ```

3. **Get API keys from team lead**
   - OpenAI API key
   - Database credentials
   - Email service credentials

4. **Update `.env` files** with your credentials

5. **Test the setup**
   ```bash
   # Backend
   cd backend
   python run.py
   
   # Auth Backend
   cd auth-backend
   npm start
   ```

## 🔍 **Troubleshooting**

### **Common Issues:**
- **"API key not found"**: Check `OPENAI_API_KEY` in `backend/.env`
- **"Database connection failed"**: Verify `DATABASE_URL` format
- **"JWT verification failed"**: Ensure JWT secrets are set correctly

### **Need Help?**
- Check the `.env.example` files for required variables
- Contact the team lead for API keys
- Review this document for setup steps

## 📞 **Emergency Contacts**

- **Team Lead**: [Your Name] - [Your Email]
- **Security Issues**: Report immediately to team lead
- **API Key Issues**: Contact service provider support

---

**Last Updated**: July 20, 2025  
**Next Review**: August 20, 2025 