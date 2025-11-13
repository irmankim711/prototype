"""
Reassign all reports to the current authenticated user
This is useful after clearing Firestore data
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Report, User

def reassign_all_reports(target_user_id):
    """Reassign all reports to a specific user_id"""
    app = create_app()

    with app.app_context():
        # Check if target user exists
        target_user = User.query.get(target_user_id)
        if not target_user:
            print(f"❌ User with ID {target_user_id} not found")
            print("\n📋 Available users:")
            users = User.query.all()
            if not users:
                print("   No users found in database")
            else:
                for user in users:
                    print(f"   - ID: {user.id}, Email: {user.email}, Role: {user.role}")
            return

        print(f"\n👤 Target User:")
        print(f"   ID: {target_user.id}")
        print(f"   Email: {target_user.email}")
        print(f"   Role: {target_user.role}")

        # Get all reports
        reports = Report.query.all()
        print(f"\n📊 Found {len(reports)} reports in database")

        if not reports:
            print("   No reports to reassign")
            return

        # Show current ownership
        print("\n📋 Current ownership:")
        ownership_map = {}
        for report in reports:
            user_id = report.user_id
            if user_id not in ownership_map:
                ownership_map[user_id] = []
            ownership_map[user_id].append(report.id)

        for user_id, report_ids in ownership_map.items():
            print(f"   User {user_id}: {len(report_ids)} reports")

        # Ask for confirmation
        print(f"\n⚠️  This will reassign ALL {len(reports)} reports to user {target_user_id} ({target_user.email})")
        response = input("Continue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("\n❌ Operation cancelled")
            return

        # Reassign all reports
        updated_count = 0
        for report in reports:
            old_user_id = report.user_id
            report.user_id = target_user_id
            updated_count += 1
            if updated_count <= 5:  # Show first 5 as examples
                print(f"   Report {report.id} ({report.title[:50]}): user {old_user_id} → {target_user_id}")

        if updated_count > 5:
            print(f"   ... and {updated_count - 5} more reports")

        # Commit changes
        db.session.commit()

        print(f"\n✅ Successfully reassigned {updated_count} reports to user {target_user_id}")
        print(f"\n🎉 All reports now belong to {target_user.email}")

if __name__ == '__main__':
    # Default to user_id 7 (from your logs: firebts5k@gmail.com)
    target_user_id = 7

    if len(sys.argv) > 1:
        try:
            target_user_id = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid user_id '{sys.argv[1]}'. Must be an integer.")
            sys.exit(1)

    print(f"🔄 Reassigning all reports to user_id: {target_user_id}")
    reassign_all_reports(target_user_id)
