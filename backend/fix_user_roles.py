"""
Fix user roles - convert uppercase USER to lowercase user
"""
from app import create_app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_user_roles():
    """Update user roles from uppercase to lowercase"""
    app = create_app()
    with app.app_context():
        try:
            # Use raw SQL to update the role values
            result = db.session.execute(
                db.text("UPDATE users SET role = 'user' WHERE role = 'USER'")
            )
            db.session.commit()

            logger.info(f"✅ Updated {result.rowcount} user roles from 'USER' to 'user'")

            # Also check for other uppercase variants
            for old_role, new_role in [('ADMIN', 'admin'), ('VIEWER', 'viewer'), ('API_USER', 'api_user')]:
                result = db.session.execute(
                    db.text(f"UPDATE users SET role = :new_role WHERE role = :old_role"),
                    {'new_role': new_role, 'old_role': old_role}
                )
                if result.rowcount > 0:
                    db.session.commit()
                    logger.info(f"✅ Updated {result.rowcount} user roles from '{old_role}' to '{new_role}'")

            logger.info("✅ All user roles have been normalized to lowercase")

        except Exception as e:
            logger.error(f"❌ Error fixing user roles: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_user_roles()
