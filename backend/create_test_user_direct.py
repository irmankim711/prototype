#!/usr/bin/env python3
"""
Simple script to insert a test user directly into the database
"""

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_user_directly():
    """Create a test user by directly connecting to the database"""
    
    import psycopg2
    from datetime import datetime
    
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        
        # Extract connection parameters
        # Remove the postgresql+psycopg2:// prefix for psycopg2
        db_url = database_url.replace('postgresql+psycopg2://', '')
        
        # Connect to database
        conn = psycopg2.connect(database_url.replace('+psycopg2', ''))
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT id FROM users WHERE email = %s", ('test@example.com',))
        if cur.fetchone():
            print("✅ Test user already exists!")
            return
            
        # Create password hash
        password_hash = generate_password_hash('test123')
        
        # Insert test user
        cur.execute("""
            INSERT INTO users (email, password_hash, first_name, last_name, username, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ('test@example.com', password_hash, 'Test', 'User', 'testuser', True, datetime.utcnow(), datetime.utcnow()))
        
        conn.commit()
        print("✅ Test user created successfully!")
        print("   Email: test@example.com")
        print("   Password: test123")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_test_user_directly()
