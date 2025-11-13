"""
Add missing columns to users table for Firebase authentication
"""
from app import create_app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_users_table():
    """Add missing columns to users table"""
    app = create_app()
    with app.app_context():
        try:
            # Check if columns exist first
            result = db.session.execute(db.text('PRAGMA table_info(users)')).fetchall()
            existing_columns = [col[1] for col in result]

            logger.info(f"Existing columns: {existing_columns}")

            # Add firebase_uid column if it doesn't exist
            if 'firebase_uid' not in existing_columns:
                db.session.execute(db.text(
                    "ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(255)"
                ))
                db.session.commit()
                logger.info("✅ Added firebase_uid column")
            else:
                logger.info("ℹ️ firebase_uid column already exists")

            # Add role column if it doesn't exist
            if 'role' not in existing_columns:
                # SQLite doesn't support ENUM directly, use VARCHAR
                db.session.execute(db.text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"
                ))
                db.session.commit()
                logger.info("✅ Added role column")

                # Set default role for existing users
                db.session.execute(db.text(
                    "UPDATE users SET role = 'user' WHERE role IS NULL"
                ))
                db.session.commit()
                logger.info("✅ Set default role for existing users")
            else:
                logger.info("ℹ️ role column already exists")

            # Add last_login column if it doesn't exist (update from last_login_at)
            if 'last_login' not in existing_columns and 'last_login_at' in existing_columns:
                # Rename last_login_at to last_login
                db.session.execute(db.text(
                    """
                    CREATE TABLE users_new AS
                    SELECT
                        id, email, username, password_hash, first_name, last_name, phone,
                        company, job_title, bio, avatar_url, is_active, is_verified,
                        created_at, updated_at, last_login_at as last_login,
                        failed_login_attempts, locked_until, timezone, language, theme,
                        email_notifications, push_notifications, firebase_uid, role
                    FROM users
                    """
                ))
                db.session.execute(db.text("DROP TABLE users"))
                db.session.execute(db.text("ALTER TABLE users_new RENAME TO users"))
                db.session.commit()
                logger.info("✅ Renamed last_login_at to last_login")
            elif 'last_login' not in existing_columns:
                db.session.execute(db.text(
                    "ALTER TABLE users ADD COLUMN last_login DATETIME"
                ))
                db.session.commit()
                logger.info("✅ Added last_login column")

            # Verify the changes
            result = db.session.execute(db.text('PRAGMA table_info(users)')).fetchall()
            new_columns = [col[1] for col in result]
            logger.info(f"✅ Updated columns: {new_columns}")

            logger.info("✅ Database migration completed successfully")

        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_users_table()
