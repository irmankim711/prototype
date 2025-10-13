#!/usr/bin/env python3
"""
Create missing user table in Supabase database
This fixes the 'relation "user" does not exist' error
"""

import os
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection - use environment variable for security
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/postgres')

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def create_user_table(cursor):
    """Create the user table with all required fields"""
    
    user_table_sql = """
    CREATE TABLE IF NOT EXISTS "user" (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        username VARCHAR(100) UNIQUE,
        phone VARCHAR(20),
        company VARCHAR(200),
        job_title VARCHAR(200),
        bio TEXT,
        avatar_url VARCHAR(500),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP WITH TIME ZONE,
        
        -- Additional fields for user management
        email_verified BOOLEAN DEFAULT false,
        email_verification_token VARCHAR(255),
        password_reset_token VARCHAR(255),
        password_reset_expires TIMESTAMP WITH TIME ZONE,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP WITH TIME ZONE,
        
        -- Profile fields
        timezone VARCHAR(50) DEFAULT 'UTC',
        language VARCHAR(10) DEFAULT 'en',
        theme VARCHAR(20) DEFAULT 'light',
        
        -- Metadata
        last_active TIMESTAMP WITH TIME ZONE,
        login_count INTEGER DEFAULT 0,
        
        -- Indexes for performance
        CONSTRAINT unique_email UNIQUE (email),
        CONSTRAINT unique_username UNIQUE (username)
    );
    """
    
    # Create indexes for better performance
    indexes_sql = [
        'CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email);',
        'CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username);',
        'CREATE INDEX IF NOT EXISTS idx_user_active ON "user" (is_active);',
        'CREATE INDEX IF NOT EXISTS idx_user_created_at ON "user" (created_at);',
        'CREATE INDEX IF NOT EXISTS idx_user_last_login ON "user" (last_login);'
    ]
    
    try:
        # Create the table
        cursor.execute(user_table_sql)
        logger.info("✅ User table created successfully")
        
        # Create indexes
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        logger.info("✅ User table indexes created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating user table: {e}")
        return False

def create_test_user(cursor):
    """Create a test user for testing login"""
    
    # Note: In production, passwords should be properly hashed using bcrypt
    # For this test, we'll create a simple user
    test_user_sql = """
    INSERT INTO "user" (
        email, password_hash, first_name, last_name, 
        username, is_active, email_verified
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    ) ON CONFLICT (email) DO NOTHING
    RETURNING id;
    """
    
    # Simple password hash for testing (in production, use proper bcrypt)
    import hashlib
    test_password = os.getenv('TEST_PASSWORD', 'testpassword123')
    # This is NOT secure - just for testing
    password_hash = hashlib.sha256(test_password.encode()).hexdigest()
    
    test_users = [
        ("test@example.com", password_hash, "Test", "User", "testuser", True, True),
        ("admin@example.com", password_hash, "Admin", "User", "admin", True, True),
        ("demo@demo.com", password_hash, "Demo", "User", "demo", True, True),
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            cursor.execute(test_user_sql, user_data)
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                created_users.append({"email": user_data[0], "id": user_id})
                logger.info(f"✅ Created test user: {user_data[0]} (ID: {user_id})")
            else:
                logger.info(f"ℹ️ Test user already exists: {user_data[0]}")
        except Exception as e:
            logger.error(f"❌ Error creating test user {user_data[0]}: {e}")
    
    return created_users

def fix_user_table_issue():
    """Main function to fix the user table issue"""
    
    logger.info("🔧 Starting user table fix...")
    logger.info("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        logger.info("✅ Connected to Supabase database")
        
        # Check if user table exists
        if check_table_exists(cursor, "user"):
            logger.info("ℹ️ User table already exists")
            
            # Check if it has data
            cursor.execute('SELECT COUNT(*) FROM "user";')
            user_count = cursor.fetchone()[0]
            logger.info(f"📊 Current users in table: {user_count}")
            
            if user_count == 0:
                logger.info("🔄 Creating test users...")
                created_users = create_test_user(cursor)
                conn.commit()
                
                if created_users:
                    logger.info(f"✅ Created {len(created_users)} test users")
                    for user in created_users:
                        logger.info(f"   • {user['email']} (ID: {user['id']})")
            else:
                logger.info("✅ User table has existing data")
                
        else:
            logger.info("❌ User table does not exist - creating it...")
            
            # Create the user table
            if create_user_table(cursor):
                logger.info("✅ User table created successfully")
                
                # Create test users
                logger.info("🔄 Creating test users...")
                created_users = create_test_user(cursor)
                conn.commit()
                
                if created_users:
                    logger.info(f"✅ Created {len(created_users)} test users")
                    for user in created_users:
                        logger.info(f"   • {user['email']} (ID: {user['id']})")
            else:
                logger.error("❌ Failed to create user table")
                return False
        
        # Test the table
        logger.info("\n🧪 Testing user table...")
        cursor.execute('SELECT email, first_name, last_name, is_active, created_at FROM "user" LIMIT 5;')
        users = cursor.fetchall()
        
        logger.info(f"📋 User table contents ({len(users)} users):")
        for user in users:
            email, first_name, last_name, is_active, created_at = user
            logger.info(f"   • {email} - {first_name} {last_name} (Active: {is_active}) - Created: {created_at}")
        
        cursor.close()
        conn.close()
        
        logger.info("\n🎉 User table fix completed successfully!")
        logger.info("💡 You should now be able to login with:")
        logger.info("   Email: test@example.com")
        logger.info(f"   Password: {os.getenv('TEST_PASSWORD', 'testpassword123')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing user table: {e}")
        return False

def main():
    """Main execution function"""
    print("🔧 USER TABLE FIX SCRIPT")
    print("=" * 40)
    print("This script will create the missing 'user' table in Supabase")
    print("and add test users to fix the login 500 error.")
    print()
    
    success = fix_user_table_issue()
    
    if success:
        print("\n✅ SUCCESS!")
        print("The user table has been created and populated.")
        print("You can now test the login endpoint with the test users.")
        print("\n🔧 Next steps:")
        print(f"1. Test login with test@example.com / {os.getenv('TEST_PASSWORD', 'testpassword123')}")
        print("2. If successful, the 500 error should be resolved")
        print("3. You can then create proper users through the registration endpoint")
    else:
        print("\n❌ FAILED!")
        print("Could not fix the user table issue.")
        print("Check the error messages above for details.")

if __name__ == '__main__':
    main()
