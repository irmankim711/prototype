#!/usr/bin/env python3
"""
Initialize database - create tables and run migrations
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database with tables"""
    
    print("=" * 50)
    print("INITIALIZING DATABASE")
    print("=" * 50)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db = SQLAlchemy()
    db.init_app(app)
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        try:
            # Import models to register them
            from app.models import User, Report, ReportTemplate, Program, Participant, FormIntegration
            
            print("📋 Creating all tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Check what tables were created
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n📋 Tables in database ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")
                
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n✅ Database initialization completed!")
    return True

if __name__ == "__main__":
    init_database()
