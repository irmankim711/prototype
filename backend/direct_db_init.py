#!/usr/bin/env python3
"""
Direct SQLite database initialization
"""
import sqlite3
import os

def init_database_direct():
    """Initialize database directly with SQLite"""
    
    print("=" * 50)
    print("DIRECT SQLITE DATABASE INITIALIZATION")
    print("=" * 50)
    
    db_file = 'app.db'
    
    # Remove existing database file if it exists
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"🗑️ Removed existing database file: {db_file}")
    
    try:
        # Create new database connection
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("📋 Creating database tables...")
        
        # User table
        cursor.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created user table")
        
        # Report table
        cursor.execute("""
            CREATE TABLE report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created report table")
        
        # Report template table
        cursor.execute("""
            CREATE TABLE report_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                template_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created report_template table")
        
        # Program table
        cursor.execute("""
            CREATE TABLE program (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created program table")
        
        # Participant table
        cursor.execute("""
            CREATE TABLE participant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(120),
                program_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES program (id)
            )
        """)
        print("✅ Created participant table")
        
        # Form integration table
        cursor.execute("""
            CREATE TABLE form_integration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                integration_type VARCHAR(50),
                config_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created form_integration table")
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables created ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check database file size
        conn.close()
        file_size = os.path.getsize(db_file)
        print(f"\n💾 Database file size: {file_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_database_direct()
