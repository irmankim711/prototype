#!/usr/bin/env python3
"""
Test Supabase database connection
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def test_supabase_connection():
    """Test connection to Supabase database"""
    
    print("=" * 50)
    print("TESTING SUPABASE DATABASE CONNECTION")
    print("=" * 50)
    
    # Supabase connection string
    supabase_url = "postgresql://postgres.kprvqvugkggcpqwsisnz:GoGM5YXlRX8QFwbs@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    
    print(f"🔗 Connecting to: aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
    
    try:
        # Connect to Supabase
        conn = psycopg2.connect(supabase_url)
        print("✅ Successfully connected to Supabase!")
        
        # Create cursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"📋 PostgreSQL Version: {version['version']}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Database tables ({len(tables)}):")
        
        if tables:
            for table in tables:
                table_name = table['table_name']
                # Get row count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()
                    print(f"   - {table_name}: {count['count']} rows")
                except Exception as e:
                    print(f"   - {table_name}: Error getting count - {e}")
        else:
            print("   No tables found in public schema")
        
        # Check database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
        """)
        db_size = cursor.fetchone()
        print(f"\n💾 Database size: {db_size['db_size']}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n🎉 Supabase connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_flask_with_supabase():
    """Test if Flask can connect to Supabase"""
    
    print("\n" + "=" * 50)
    print("TESTING FLASK WITH SUPABASE")
    print("=" * 50)
    
    try:
        # Set environment variable for this test
        os.environ['DATABASE_URL'] = "postgresql://postgres.kprvqvugkggcpqwsisnz:GoGM5YXlRX8QFwbs@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
        
        # Import Flask components
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        # Create minimal Flask app
        app = Flask(__name__)
        
        # Configure database for Supabase
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 30,
        }
        
        # Initialize SQLAlchemy
        db = SQLAlchemy()
        db.init_app(app)
        
        with app.app_context():
            print("✅ Flask app context created successfully")
            
            # Test database connection
            try:
                # Simple query to test connection
                result = db.session.execute(db.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
                count = result.scalar()
                print(f"✅ Supabase connection successful - Found {count} tables")
                
                return True
                
            except Exception as e:
                print(f"❌ Database query failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Supabase database connectivity...")
    
    # Test direct connection
    direct_test = test_supabase_connection()
    
    # Test Flask integration
    flask_test = test_flask_with_supabase()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Direct Supabase Connection: {'✅ PASS' if direct_test else '❌ FAIL'}")
    print(f"Flask + Supabase Integration: {'✅ PASS' if flask_test else '❌ FAIL'}")
    
    if direct_test and flask_test:
        print("\n🎉 All Supabase connectivity tests passed!")
        print("Your Flask app is now connected to Supabase!")
    else:
        print("\n⚠️ Some Supabase connectivity tests failed. Check the errors above.")
