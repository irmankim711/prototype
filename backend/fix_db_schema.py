#!/usr/bin/env python3
"""
Fix database schema for MVP - increase password_hash column size
"""

from app import create_app, db
from sqlalchemy import text

def fix_password_hash_column():
    app = create_app()
    with app.app_context():
        try:
            # Update the password_hash column to accommodate longer hashes
            with db.engine.connect() as conn:
                # Check if we need to update the column
                result = conn.execute(text("""
                    SELECT character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' 
                    AND column_name = 'password_hash'
                """))
                
                current_length = result.fetchone()
                if current_length and current_length[0] == 128:
                    print("📝 Updating password_hash column from 128 to 255 characters...")
                    
                    # Alter the column
                    conn.execute(text("""
                        ALTER TABLE "user" 
                        ALTER COLUMN password_hash TYPE VARCHAR(255)
                    """))
                    conn.commit()
                    print("✅ Password hash column updated successfully!")
                else:
                    print("✅ Password hash column already has correct size")
                    
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing Database Schema for MVP")
    print("=" * 40)
    
    if fix_password_hash_column():
        print("🎉 Database schema update completed!")
        print("Now you can test user registration!")
    else:
        print("⚠️ Database schema update failed")
