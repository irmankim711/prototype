"""
Fix all user roles - convert any uppercase values to lowercase
"""
from app import create_app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_all_roles():
    """Update all user roles to lowercase"""
    app = create_app()
    with app.app_context():
        try:
            # Use raw SQL to check current roles
            result = db.session.execute(db.text('SELECT id, email, role FROM users')).fetchall()

            logger.info(f'Found {len(result)} users in database')

            needs_update = []
            for row in result:
                if row.role and row.role != row.role.lower():
                    needs_update.append((row.id, row.email, row.role))
                    logger.info(f'  User {row.email}: role="{row.role}" (needs update)')
                else:
                    logger.info(f'  User {row.email}: role="{row.role}" (OK)')

            if needs_update:
                logger.info(f'\nUpdating {len(needs_update)} users with uppercase roles...')

                # Update each user individually
                for user_id, email, old_role in needs_update:
                    new_role = old_role.lower()
                    db.session.execute(
                        db.text('UPDATE users SET role = :new_role WHERE id = :user_id'),
                        {'new_role': new_role, 'user_id': user_id}
                    )
                    logger.info(f'✅ Updated {email}: "{old_role}" -> "{new_role}"')

                db.session.commit()
                logger.info(f'\n✅ Successfully updated {len(needs_update)} users')
            else:
                logger.info('\n✅ All user roles are already lowercase')

            # Verify the changes
            logger.info('\nVerifying all roles...')
            result = db.session.execute(db.text('SELECT id, email, role FROM users')).fetchall()
            for row in result:
                logger.info(f'  {row.email}: role="{row.role}"')

        except Exception as e:
            logger.error(f'❌ Error fixing roles: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_all_roles()
