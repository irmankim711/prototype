"""
Production Database Models - ZERO MOCK DATA
Real database models for production form automation system
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
import uuid
import logging

# Setup logging for this module
logger = logging.getLogger(__name__)

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    oauth_tokens = relationship("UserOAuthToken", back_populates="user")
    form_analyses = relationship("FormAnalysis", back_populates="user")
    programs = relationship("Program", back_populates="user")
    reports = relationship("Report", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.email}>'

class UserOAuthToken(db.Model):
    """OAuth tokens for external service integration"""
    __tablename__ = 'user_oauth_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google', 'microsoft'
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="oauth_tokens")
    
    def __repr__(self):
        return f'<UserOAuthToken {self.provider} for User {self.user_id}>'

class Program(db.Model):
    """Programs for real data tracking"""
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Real program data (no mock values)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    funding_source = db.Column(db.String(255), nullable=True)
    program_type = db.Column(db.String(100), nullable=True)
    target_population = db.Column(db.String(255), nullable=True)
    geographic_scope = db.Column(db.String(255), nullable=True)
    
    # Performance metrics (real data)
    participants_enrolled = db.Column(db.Integer, default=0)
    participants_completed = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    satisfaction_score = db.Column(db.Float, default=0.0)
    
    # Administrative details
    program_manager = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    
    # Status and tracking
    status = db.Column(db.String(50), default='active')  # active, completed, cancelled, planned
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="programs")
    form_analyses = relationship("FormAnalysis", back_populates="program")
    reports = relationship("Report", back_populates="program")
    
    def __repr__(self):
        return f'<Program {self.name}>'

class FormAnalysis(db.Model):
    """Analysis results from real form data"""
    __tablename__ = 'form_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=True)
    
    # Form identification
    form_id = db.Column(db.String(255), nullable=False)
    form_provider = db.Column(db.String(50), nullable=False)  # 'google', 'microsoft'
    form_title = db.Column(db.String(500), nullable=True)
    form_url = db.Column(db.Text, nullable=True)
    
    # Analysis data (real AI analysis results)
    analysis_data = db.Column(db.JSON, nullable=False)
    response_count = db.Column(db.Integer, default=0)
    analysis_type = db.Column(db.String(100), default='ai_analysis')
    
    # Quality metrics
    confidence_score = db.Column(db.Float, default=0.0)
    completeness_score = db.Column(db.Float, default=0.0)
    
    # Status tracking
    status = db.Column(db.String(50), default='completed')  # processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    processing_time_seconds = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="form_analyses")
    program = relationship("Program", back_populates="form_analyses")
    reports = relationship("Report", back_populates="form_analysis")
    
    def __repr__(self):
        return f'<FormAnalysis {self.form_id} by User {self.user_id}>'

class Report(db.Model):
    """Generated reports from real data"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=True)
    form_analysis_id = db.Column(db.Integer, db.ForeignKey('form_analyses.id'), nullable=True)
    
    # Report metadata
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(100), nullable=False)  # 'automated', 'custom', 'summary'
    
    # Report content (real data)
    content_data = db.Column(db.JSON, nullable=False)
    charts_data = db.Column(db.JSON, nullable=True)
    statistics_data = db.Column(db.JSON, nullable=True)
    
    # File information
    file_path = db.Column(db.String(500), nullable=True)
    file_format = db.Column(db.String(20), default='pdf')  # pdf, docx, excel
    file_size_bytes = db.Column(db.Integer, nullable=True)
    
    # Generation details
    template_used = db.Column(db.String(255), nullable=True)
    generation_method = db.Column(db.String(100), default='automated')
    ai_generated = db.Column(db.Boolean, default=True)
    
    # Status and tracking
    status = db.Column(db.String(50), default='draft')  # draft, completed, published, archived
    is_public = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    program = relationship("Program", back_populates="reports")
    form_analysis = relationship("FormAnalysis", back_populates="reports")
    
    def __repr__(self):
        return f'<Report {self.title} by User {self.user_id}>'

class APILog(db.Model):
    """API usage logs for monitoring and analytics"""
    __tablename__ = 'api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Request details
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Float, nullable=True)
    
    # API provider tracking
    external_api_called = db.Column(db.String(50), nullable=True)  # google, microsoft, openai
    external_api_status = db.Column(db.String(20), nullable=True)
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)
    stack_trace = db.Column(db.Text, nullable=True)
    
    # Request metadata
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    request_size_bytes = db.Column(db.Integer, nullable=True)
    response_size_bytes = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<APILog {self.method} {self.endpoint} - {self.status_code}>'

class SystemConfiguration(db.Model):
    """System configuration for production settings"""
    __tablename__ = 'system_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(50), default='string')  # string, integer, boolean, json
    description = db.Column(db.Text, nullable=True)
    
    # Security and validation
    is_sensitive = db.Column(db.Boolean, default=False)
    requires_restart = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<SystemConfiguration {self.key}>'

# Create tables function
def create_production_tables(app):
    """Create all production tables with enhanced error handling and retry logic"""
    from ..core.database import with_db_retry, get_db_manager
    import logging
    
    logger = logging.getLogger(__name__)
    
    @with_db_retry(max_retries=3, base_delay=2.0)
    def _create_tables_with_retry():
        """Create tables with retry logic"""
        with app.app_context():
            try:
                # Test database connection before proceeding
                db_manager = get_db_manager()
                health_status = db_manager.health_check(force=True)
                logger.info(f"Database health before table creation: {health_status}")
                
                # Create tables
                db.create_all()
                logger.info("Production database tables created successfully!")
                
                return True
            except Exception as e:
                logger.error(f"Failed to create tables: {str(e)}")
                raise
    
    @with_db_retry(max_retries=3, base_delay=1.0)
    def _create_default_configs_with_retry():
        """Create default configurations with retry logic"""
        with app.app_context():
            try:
                # Create default system configurations
                default_configs = [
                    {
                        'key': 'MOCK_MODE_DISABLED',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'Disable all mock data and use real API integrations'
                    },
                    {
                        'key': 'ENABLE_REAL_GOOGLE_FORMS',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'Enable real Google Forms API integration'
                    },
                    {
                        'key': 'ENABLE_REAL_MICROSOFT_FORMS',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'Enable real Microsoft Forms API integration'
                    },
                    {
                        'key': 'ENABLE_REAL_AI',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'Enable real AI analysis using OpenAI API'
                    },
                    {
                        'key': 'PRODUCTION_MODE',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'System running in production mode'
                    }
                ]
                
                for config in default_configs:
                    existing_config = SystemConfiguration.query.filter_by(key=config['key']).first()
                    if not existing_config:
                        new_config = SystemConfiguration(**config)
                        db.session.add(new_config)
                
                db.session.commit()
                logger.info("Default system configurations created!")
                return True
            except Exception as e:
                logger.error(f"Failed to create default configurations: {str(e)}")
                raise
    
    # Execute table creation and configuration setup with retry logic
    try:
        # Create tables first
        _create_tables_with_retry()
        
        # Then create default configurations
        _create_default_configs_with_retry()
        
        logger.info("Production database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to setup production database: {str(e)}")
        raise

# Migration scripts
def migrate_from_mock_to_production(app):
    """Migrate existing mock data to production schema with enhanced error handling"""
    from ..core.database import with_db_retry, get_db_manager
    import logging
    
    logger = logging.getLogger(__name__)
    
    @with_db_retry(max_retries=3, base_delay=2.0)
    def _migrate_with_retry():
        """Execute migration with retry logic"""
        with app.app_context():
            try:
                # Check database health before migration
                db_manager = get_db_manager()
                health_status = db_manager.health_check(force=True)
                logger.info(f"Database health before migration: {health_status}")
                
                # Check if there are any existing users to migrate
                logger.info("Starting migration from mock to production data...")
                
                # This would be customized based on existing schema
                # For now, we'll just ensure the tables exist
                create_production_tables(app)
                
                logger.info("Migration completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Migration failed: {str(e)}")
                raise
    
    try:
        _migrate_with_retry()
    except Exception as e:
        logger.error(f"Migration failed after retries: {str(e)}")
        raise

if __name__ == "__main__":
    # This can be run standalone to create tables
    from flask import Flask
    from ..core.database import get_db_manager, check_database_health, get_database_info
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    app = Flask(__name__)
    
    # Use environment-based database configuration
    from ..core.config import get_database_config
    db_config = get_database_config()
    app.config.update(db_config)
    
    # Initialize database manager
    db_manager = get_db_manager()
    
    try:
        # Test database connection
        health_status = check_database_health(force=True)
        logger.info(f"Database health check: {health_status}")
        
        # Get connection info
        conn_info = get_database_info()
        logger.info(f"Database connection info: {conn_info}")
        
        # Initialize Flask-SQLAlchemy
        db.init_app(app)
        
        # Create tables
        create_production_tables(app)
        
        logger.info("Production tables created successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create production tables: {str(e)}")
        raise
    finally:
        # Clean up database connections
        db_manager.close()
