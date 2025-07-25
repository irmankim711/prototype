from sqlalchemy import text
from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        print("Database connection successful!")
        
        # Test user query
        user = User.query.first()
        print(f"First user: {user}")
        
    except Exception as e:
        print(f"Database error: {str(e)}")
