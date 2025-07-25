import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in .env file")
    exit(1)

print("🔍 Testing database connection...")
print(f"Connecting to: {DATABASE_URL.split('@')[-1]}")

try:
    # Create engine with connection pool pre-ping to verify connection
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connection before using it
        connect_args={
            'connect_timeout': 5,  # 5 second timeout
            'sslmode': 'require'  # Force SSL
        }
    )
    
    # Try to connect
    with engine.connect() as connection:
        print("✅ Successfully connected to the database!")
        
        # Try a simple query with text()
        result = connection.execute(text("SELECT version()"))  # Removed semicolon
        db_version = result.scalar()
        print(f"📊 Database version: {db_version}")
        
        # Check if the users table exists
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """))  # Removed semicolon
        if result.scalar():
            print("✅ Users table exists")
        else:
            print("ℹ️ Users table does not exist")
            
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print("\nTroubleshooting steps:")
    print("1. Verify your database password in Supabase dashboard")
    print("2. Check if your IP is whitelisted in Supabase")
    print("3. Make sure the database is running and accessible")
    print("4. Try adding your current IP to allowed IPs in Supabase")
    print("5. Check if you need to use a VPN or different network")