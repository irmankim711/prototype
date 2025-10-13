#!/usr/bin/env python3
"""
Create missing tables that match the model configuration
Fixed version that uses UUID data types to match Supabase schema
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get connection to Supabase database"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return None
            
        # Parse connection string
        if database_url.startswith('postgresql://'):
            conn_string = database_url.replace('postgresql://', '')
            
            if '@' in conn_string:
                auth_part, host_part = conn_string.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                else:
                    username, password = auth_part, ''
                
                if ':' in host_part:
                    host_port, database = host_part.split('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_part, '5432', 'postgres'
            else:
                print("❌ Invalid DATABASE_URL format")
                return None
            
            # Connect to database
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            print("✅ Successfully connected to Supabase database!")
            return conn
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def create_missing_tables(conn):
    """Create the missing tables that your models expect"""
    try:
        cursor = conn.cursor()
        
        print("\n🔨 Creating missing tables...")
        
        # 1. Create user_tokens table (using UUID to match users table)
        print("   Creating user_tokens table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                platform VARCHAR(50) NOT NULL,
                platform_user_id VARCHAR(255),
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type VARCHAR(20) DEFAULT 'Bearer',
                scopes JSONB,
                expires_at TIMESTAMP WITH TIME ZONE,
                issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true,
                revoked_at TIMESTAMP WITH TIME ZONE,
                revoke_reason VARCHAR(100),
                last_used TIMESTAMP WITH TIME ZONE,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        # 2. Create user_sessions table (using UUID to match users table)
        print("   Creating user_sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                browser VARCHAR(100),
                operating_system VARCHAR(100),
                device_type VARCHAR(50),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE,
                ended_at TIMESTAMP WITH TIME ZONE,
                login_method VARCHAR(50),
                is_suspicious BOOLEAN DEFAULT false,
                security_flags JSONB,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        # 3. Create programs table
        print("   Creating programs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                start_date DATE,
                end_date DATE,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 4. Create participants table (using UUID to match users and programs)
        print("   Creating participants table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                program_id UUID NOT NULL,
                user_id UUID NOT NULL,
                role VARCHAR(100),
                joined_date DATE DEFAULT CURRENT_DATE,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        # 5. Create attendance_records table (using UUID to match participants)
        print("   Creating attendance_records table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                participant_id UUID NOT NULL,
                session_date DATE NOT NULL,
                check_in_time TIMESTAMP WITH TIME ZONE,
                check_out_time TIMESTAMP WITH TIME ZONE,
                status VARCHAR(50) DEFAULT 'present',
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            );
        """)
        
        # 6. Create form_integrations table
        print("   Creating form_integrations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_integrations (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                form_id UUID,
                integration_type VARCHAR(100) NOT NULL,
                config JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                last_sync TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 7. Create form_responses table (using UUID to match users)
        print("   Creating form_responses table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_responses (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                form_id UUID,
                user_id UUID,
                response_data JSONB NOT NULL,
                submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'submitted',
                metadata JSONB,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)
        
        # Commit the changes
        conn.commit()
        cursor.close()
        
        print("✅ All missing tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False

def verify_tables_created(conn):
    """Verify that all expected tables now exist"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        expected_tables = [
            'users', 'user_tokens', 'user_sessions', 'programs', 
            'participants', 'attendance_records', 'form_integrations', 
            'form_responses', 'reports', 'report_templates'
        ]
        
        print(f"\n🔍 Verifying tables...")
        
        for table in expected_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()['exists']
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")

def main():
    """Main function to create missing tables"""
    print("=" * 60)
    print("🔨 CREATE MISSING TABLES FOR MODELS (UUID FIXED)")
    print("=" * 60)
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        # Create missing tables
        success = create_missing_tables(conn)
        
        if success:
            # Verify tables were created
            verify_tables_created(conn)
            
            print(f"\n" + "=" * 60)
            print("🎉 SUCCESS!")
            print("=" * 60)
            print("✅ All missing tables have been created!")
            print("✅ Your models should now work properly!")
            print("✅ Try signing in again!")
            
        else:
            print("❌ Failed to create tables")
            
    finally:
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
