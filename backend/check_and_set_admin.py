"""
Check and set admin role for user
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import User, UserRole

def check_and_set_admin(email):
    """Check user role and optionally set as admin"""
    app = create_app()

    with app.app_context():
        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"❌ User not found: {email}")
            return

        print(f"\n👤 User Information:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Current Role: {user.role}")
        print(f"   Is Active: {user.is_active}")

        # Check if already admin
        if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            print(f"\n✅ User already has admin privileges ({user.role})")
            return

        # Ask to upgrade
        print(f"\n⚠️  User currently has role: {user.role}")
        response = input("Do you want to upgrade this user to ADMIN? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            user.role = UserRole.ADMIN
            db.session.commit()
            print(f"\n✅ User role updated to ADMIN!")
            print(f"   User {email} can now:")
            print(f"   - Delete any report")
            print(f"   - Access any report")
            print(f"   - Manage all users")
        else:
            print("\n❌ Role not changed")

if __name__ == '__main__':
    # Check the logged-in user from logs
    email = 'firebts5k@gmail.com'

    if len(sys.argv) > 1:
        email = sys.argv[1]

    print(f"Checking user: {email}")
    check_and_set_admin(email)
