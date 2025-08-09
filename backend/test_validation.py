import pytest
import json
from app import create_app, db
from app.models import User, Form, FormSubmission
from app.validation.schemas import FormCreationSchema, FormSubmissionSchema, UserRegistrationSchema
from marshmallow import ValidationError

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "SECRET_KEY": "test-secret"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User"
        )
        db.session.add(user)
        db.session.commit()
        return user

def test_form_creation_validation():
    """Test form creation schema validation."""
    schema = FormCreationSchema()
    
    # Test valid data
    valid_data = {
        "title": "Test Form",
        "description": "A test form",
        "is_public": False,
        "is_active": True,
        "schema": {
            "fields": [
                {
                    "id": "name",
                    "type": "text",
                    "label": "Full Name",
                    "required": True,
                    "placeholder": "Enter your name"
                }
            ]
        }
    }
    
    result = schema.load(valid_data)
    assert result["title"] == "Test Form"
    assert result["schema"]["fields"][0]["id"] == "name"
    
    # Test invalid data - missing title
    invalid_data = {
        "description": "A test form",
        "schema": {
            "fields": [
                {
                    "id": "name",
                    "type": "text",
                    "label": "Full Name",
                    "required": True
                }
            ]
        }
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(invalid_data)
    
    assert "title" in exc_info.value.messages

def test_form_submission_validation():
    """Test form submission schema validation."""
    schema = FormSubmissionSchema()
    
    # Test valid submission data
    valid_data = {
        "data": {
            "name": "John Doe",
            "email": "john@example.com"
        },
        "submitter_email": "john@example.com"
    }
    
    result = schema.load(valid_data)
    assert result["data"]["name"] == "John Doe"
    assert result["submitter_email"] == "john@example.com"
    
    # Test invalid data - missing data field
    invalid_data = {
        "submitter_email": "john@example.com"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(invalid_data)
    
    assert "data" in exc_info.value.messages

def test_user_registration_validation():
    """Test user registration schema validation."""
    schema = UserRegistrationSchema()
    
    # Test valid registration data
    valid_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    result = schema.load(valid_data)
    assert result["email"] == "test@example.com"
    assert result["first_name"] == "John"
    
    # Test invalid email
    invalid_data = {
        "email": "invalid-email",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(invalid_data)
    
    assert "email" in exc_info.value.messages

def test_password_strength_validation():
    """Test password strength validation."""
    schema = UserRegistrationSchema()
    
    # Test weak password
    weak_passwords = [
        "123456",           # Too short, no letters, no special chars
        "password",         # No uppercase, no numbers, no special chars
        "Password",         # No numbers, no special chars
        "Password123",      # No special chars
        "password123!"      # No uppercase
    ]
    
    for weak_password in weak_passwords:
        with pytest.raises(ValidationError) as exc_info:
            schema.load({
                "email": "test@example.com",
                "password": weak_password,
                "first_name": "John",
                "last_name": "Doe"
            })
        
        assert "password" in exc_info.value.messages

def test_field_id_validation():
    """Test form field ID validation."""
    schema = FormCreationSchema()
    
    # Test invalid field IDs
    invalid_field_ids = [
        "123name",      # Starts with number
        "name-field",   # Contains hyphen
        "name field",   # Contains space
        "name.field",   # Contains dot
        "",             # Empty
    ]
    
    for invalid_id in invalid_field_ids:
        invalid_data = {
            "title": "Test Form",
            "schema": {
                "fields": [
                    {
                        "id": invalid_id,
                        "type": "text",
                        "label": "Test Field",
                        "required": True
                    }
                ]
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(invalid_data)
        
        # Check that validation error mentions field ID
        error_messages = str(exc_info.value.messages)
        assert "id" in error_messages or "Field ID" in error_messages

def test_unique_field_ids_validation():
    """Test that form field IDs must be unique."""
    schema = FormCreationSchema()
    
    # Test duplicate field IDs
    invalid_data = {
        "title": "Test Form",
        "schema": {
            "fields": [
                {
                    "id": "name",
                    "type": "text",
                    "label": "First Name",
                    "required": True
                },
                {
                    "id": "name",  # Duplicate ID
                    "type": "text",
                    "label": "Last Name",
                    "required": True
                }
            ]
        }
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(invalid_data)
    
    # Check that validation error mentions duplicate IDs
    error_messages = str(exc_info.value.messages)
    assert "duplicate" in error_messages.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
