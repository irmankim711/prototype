# StratoSys Auth Backend

Authentication microservice for StratoSys with multi-tenant support.

## Quick Start

### Option 1: Using Docker (Recommended)

1. **Start PostgreSQL database:**
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

### Option 2: Using Supabase

1. **Create a Supabase project:**
   - Go to [https://supabase.com](https://supabase.com)
   - Create a new project
   - Get your database connection string from Settings > Database

2. **Update .env file:**
   ```bash
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

### Option 3: Local PostgreSQL

1. **Install PostgreSQL locally**
2. **Create database:**
   ```sql
   CREATE DATABASE stratosys_db;
   ```
3. **Update .env file with your credentials**
4. **Start the development server:**
   ```bash
   npm run dev
   ```

## Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/stratosys_db

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_REFRESH_SECRET=your-super-secret-refresh-jwt-key-change-this-in-production

# Server
PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3002
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset

## Database Schema

The application automatically creates the required tables on startup:
- `organizations` - Organization management
- `users` - User accounts with roles
- `refresh_tokens` - JWT refresh tokens
- `email_verifications` - Email verification tokens
- `password_resets` - Password reset tokens

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Troubleshooting

### Database Connection Issues

1. **Check if PostgreSQL is running:**
   ```bash
   docker-compose ps
   ```

2. **View database logs:**
   ```bash
   docker-compose logs postgres
   ```

3. **Reset database:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Common Errors

- `ECONNREFUSED 127.0.0.1:5432` - PostgreSQL is not running
- `JWT_SECRET is required` - Missing environment variables
- `relation "users" does not exist` - Database schema not initialized
