# Project Title: AI-Powered Report Generation and Form Builder

## Overview

This project is a comprehensive web application designed to streamline the creation, management, and analysis of reports. It features a dynamic form builder, allowing users to define data structures, and leverages AI for insightful data analysis. Reports can be generated asynchronously, and users can manage templates and view report history.

The application consists of a Python/Flask backend and a React/TypeScript frontend.

## Tech Stack

**Backend:**
*   Python 3.x
*   Flask: Micro web framework
*   SQLAlchemy: ORM for database interaction
*   PostgreSQL: Relational database
*   Celery: Distributed task queue for asynchronous report generation
*   Redis: Message broker for Celery
*   Flask-JWT-Extended: For JWT authentication
*   OpenAI API (inferred): For AI-powered data analysis
*   Google Cloud Storage (inferred): For file storage

**Frontend:**
*   React 18
*   TypeScript
*   Vite: Build tool and development server
*   Material-UI (MUI): React UI framework
*   React Query: Server state management
*   React Router: Client-side routing
*   React Hook Form: Form handling
*   Chart.js: For data visualization
*   Socket.IO Client: For real-time communication
*   Axios: HTTP client

## Features

*   **User Authentication:** Secure user registration and login using JWT.
*   **Dynamic Form Builder:** (Inferred from frontend structure) Interface for creating and managing custom forms.
*   **Asynchronous Report Generation:** Reports are generated in the background using Celery, allowing users to continue working without waiting.
*   **Report Management:**
    *   Create reports from data.
    *   View report status and history.
    *   Manage report templates.
*   **AI-Powered Data Analysis:** (Inferred from `ai_service` and OpenAI dependency) Integration with AI to analyze data submitted through forms or for reports.
*   **Dashboard:** (Inferred from frontend structure) Centralized view for users to access various features.
*   **User Profile Management:** (Inferred from frontend structure) Users can manage their profile settings.

## Prerequisites

*   Python 3.9+
*   Node.js 18.x+ and npm 9.x+
*   PostgreSQL server
*   Redis server

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file in the 'backend' directory (copy from a .env.example if available)
# and fill in the required values.
# Example .env content:
# FLASK_APP=backend.app
# FLASK_ENV=development
# SECRET_KEY=your_very_secret_key
# # For PostgreSQL (recommended for production):
# SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database_name
# # For SQLite (convenient for local development, creates a file 'backend/instance/app.db' by default):
# # SQLALCHEMY_DATABASE_URI=sqlite:///../instance/app.db 
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
# OPENAI_API_KEY=your_openai_api_key
# JWT_SECRET_KEY=another_very_secret_key_for_jwt
# # GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/gcp-credentials.json # If using GCP for storage or other services

# Initialize the database and apply migrations
# (Ensure your database server is running if using PostgreSQL, and the database specified in SQLALCHEMY_DATABASE_URI exists)
# flask db init  # Only if running for the very first time and the 'migrations' folder doesn't exist
# flask db migrate -m "Initial migration" # Use if you make changes to models and need new migration scripts
flask db upgrade # Applies existing migrations

# Run the backend development server (Flask)
# Ensure FLASK_APP=backend.app is set in .env or exported in your shell.
# This tells Flask to use the app factory in backend/app/__init__.py.
flask run

# Run Celery worker (in a separate terminal, ensure Redis is running)
# Navigate to the project root directory (one level above 'backend').
# Ensure your virtual environment (if created in 'backend/venv') is active.
# The Celery app instance is defined in backend/app/__init__.py.
# From the project root, the command would be:
celery -A backend.app.celery worker -l info
# If you are inside the 'backend' directory, it might be:
# celery -A app.celery worker -l info 
# Choose the command variant that works based on your current directory and PYTHONPATH.
```

**Note on `backend/app.py`:** There is a separate `backend/app.py` file that seems to define a simpler, standalone Flask application with different routes and functionalities (like Google Sheets integration). The setup instructions above pertain to the main, more complex application defined within the `backend/app/` directory structure (using `__init__.py`, `routes.py`, `models.py`, etc.). If you intend to run the simpler `backend/app.py`, you would typically execute `python backend/app.py` directly, and it would run on its own, without using the database, JWT, or Celery configurations from the main application.

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Run the frontend development server
npm run dev
```
The application should now be accessible at `http://localhost:5173` (or the port Vite assigns). The frontend will likely make requests to the backend API (defaulting to Flask's port 5000 if not configured otherwise).

## Running Tests

(Instructions to be added once testing infrastructure is robustly in place.)

*   **Backend:** `pytest` (run from the `backend` directory, ensure test database is configured if needed).
*   **Frontend:** `npm run lint` (for linting), `npm test` (if test scripts are configured in `package.json`).

## API Endpoints

The backend exposes several API endpoints under the `/api` prefix. Key endpoints include:

*   `POST /api/reports`: Create a new report (triggers async generation).
*   `GET /api/reports/<task_id>`: Get the status/result of a report generation task.
*   `GET /api/reports/templates`: Get available report templates.
*   `POST /api/ai/analyze`: Send data for AI analysis.

(Refer to `backend/app/routes.py` for more details. Consider generating API documentation using tools like Swagger/OpenAPI for better discoverability.)

## Deployment

(Details to be added. Consider Dockerizing the application for easier deployment. The `frontend/windsurf_deployment.yaml` might contain deployment configurations for a specific platform like Kubernetes or a similar orchestration tool.)

## Contributing

(To be defined. Standard guidelines usually include:
*   Fork the repository.
*   Create a new branch for your feature or bugfix.
*   Follow coding standards (e.g., PEP 8 for Python, ESLint rules for frontend).
*   Write tests for your changes.
*   Submit a pull request with a clear description of your changes.)

## License

(Specify the license for this project, e.g., MIT, Apache 2.0. If no license is chosen, the code is proprietary by default.)

