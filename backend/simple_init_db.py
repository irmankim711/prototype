#!/usr/bin/env python3
"""
Simple database initialization - create basic tables
"""
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database with basic tables"""
    
    print("=" * 50)
    print("SIMPLE DATABASE INITIALIZATION")
    print("=" * 50)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    print(f"Database URL: {database_url}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db = SQLAlchemy()
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create basic tables manually
            print("📋 Creating basic tables...")
            
            # User table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Report table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS report (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Report template table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS report_template (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    template_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Program table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS program (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Participant table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS participant (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(120),
                    program_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (program_id) REFERENCES program (id)
                )
            """))
            
            # Form integration table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS form_integration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    integration_type VARCHAR(50),
                    config_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Commit the changes
            db.session.commit()
            print("✅ Basic tables created successfully!")
            
            # Verify tables were created
            result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            
            print(f"\n📋 Tables created ({len(tables)}):")
            for table in tables:
                print(f"   - {table[0]}")
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    print("\n✅ Database initialization completed!")
    return True

if __name__ == "__main__":
    init_database()
