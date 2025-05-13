from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
celery = Celery(__name__)
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    
    # Celery configuration
    celery.conf.update(
        broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    )
    
    # Register blueprints
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')
    
    return app
