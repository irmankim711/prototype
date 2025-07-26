#!/usr/bin/env python3
"""
Script to add sample report data for testing the reports history functionality
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Report, User
from datetime import datetime, timedelta
import random

def create_sample_reports():
    """Create sample reports for testing"""
    app = create_app()
    
    with app.app_context():
        # Get the first user (or create one if none exists)
        user = User.query.first()
        if not user:
            print("No users found. Creating a test user...")
            user = User(
                email="test@example.com",
                username="testuser",
                first_name="Test",
                last_name="User"
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            print(f"Created test user: {user.email}")
        
        # Sample report data
        sample_reports = [
            {
                "title": "Monthly Sales Report",
                "description": "Sales performance report for the current month",
                "status": "completed",
                "template_id": "Temp1.docx",
                "data": {"company": "ABC Corp", "month": "July", "sales": "$45,000"},
                "output_url": "/mvp/static/generated/report_001.docx"
            },
            {
                "title": "Employee Performance Review",
                "description": "Quarterly performance review template",
                "status": "completed",
                "template_id": "Temp1.docx",
                "data": {"employee": "John Doe", "quarter": "Q2 2025", "rating": "Excellent"},
                "output_url": "/mvp/static/generated/report_002.docx"
            },
            {
                "title": "Project Status Update",
                "description": "Weekly project status report",
                "status": "processing",
                "template_id": "Temp1.docx",
                "data": {"project": "Website Redesign", "week": "Week 30", "progress": "85%"},
                "output_url": None
            },
            {
                "title": "Financial Summary",
                "description": "Annual financial report summary",
                "status": "failed",
                "template_id": "Temp1.docx",
                "data": {"year": "2024", "revenue": "$2.5M", "profit": "$450K"},
                "output_url": None
            },
            {
                "title": "Customer Feedback Analysis",
                "description": "Monthly customer satisfaction report",
                "status": "draft",
                "template_id": "Temp1.docx",
                "data": {"month": "July 2025", "responses": 245, "satisfaction": "4.2/5"},
                "output_url": None
            },
            {
                "title": "Inventory Report",
                "description": "Weekly inventory status and updates",
                "status": "completed",
                "template_id": "Temp1.docx",
                "data": {"week": "Week 30", "items": 1250, "low_stock": 15},
                "output_url": "/mvp/static/generated/report_003.docx"
            }
        ]
        
        # Check if sample reports already exist
        existing_count = Report.query.filter_by(user_id=user.id).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing reports for user {user.email}")
            response = input("Do you want to add more sample reports? (y/n): ")
            if response.lower() != 'y':
                print("Skipping sample data creation.")
                return
        
        # Create sample reports
        created_count = 0
        for i, report_data in enumerate(sample_reports):
            # Create reports with varying creation dates
            days_ago = random.randint(1, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            report = Report(
                title=report_data["title"],
                description=report_data["description"],
                status=report_data["status"],
                user_id=user.id,
                template_id=report_data["template_id"],
                data=report_data["data"],
                output_url=report_data["output_url"],
                created_at=created_at,
                updated_at=created_at + timedelta(hours=random.randint(1, 24))
            )
            
            db.session.add(report)
            created_count += 1
        
        try:
            db.session.commit()
            print(f"✅ Successfully created {created_count} sample reports for user {user.email}")
            
            # Display summary
            total_reports = Report.query.filter_by(user_id=user.id).count()
            status_counts = db.session.query(
                Report.status, 
                db.func.count(Report.id)
            ).filter_by(user_id=user.id).group_by(Report.status).all()
            
            print(f"\n📊 Report Summary:")
            print(f"Total reports: {total_reports}")
            for status, count in status_counts:
                print(f"  {status}: {count}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample reports: {str(e)}")

if __name__ == "__main__":
    print("🎯 Creating sample report data for testing...")
    create_sample_reports()
    print("✨ Done!")
