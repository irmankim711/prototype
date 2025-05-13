# Report Automation Tool

A modern web application for automating report generation with AI-powered insights and Google Workspace integration.

## Features

- 📊 Automated report generation from form submissions
- 🤖 AI-powered data analysis and insights
- 📑 Custom report templates
- 📈 Google Sheets & Forms integration
- 📧 Automated PDF generation and email distribution
- 👥 User management and access control
- 📱 Responsive admin dashboard

## Tech Stack

### Frontend
- React 18 with TypeScript
- Material-UI v5 for UI components
- React Query for server state management
- React Hook Form for form handling
- React Router for navigation
- Vite for build tooling

### Backend
- Flask for the main API server
- Flask-RESTful for API organization
- SQLAlchemy for database ORM
- Celery for background tasks
- Redis for caching and job queue
- PostgreSQL for data storage

### Integrations
- OpenAI GPT-4 API for AI analysis
- Google Workspace APIs (Sheets, Docs)
- SendGrid for email automation

## Project Structure

```
/
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── theme.ts      # MUI theme configuration
│   └── package.json
│
├── backend/               # Flask backend application
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   └── tasks/        # Celery tasks
│   └── requirements.txt
│
└── README.md
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Start the backend server:
   ```bash
   flask run
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

### Additional Services

1. Start Redis server for caching and job queue:
   ```bash
   redis-server
   ```

2. Start Celery worker for background tasks:
   ```bash
   cd backend
   celery -A app.celery worker --loglevel=info
   ```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://localhost/report_automation
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

## API Documentation

The API documentation is available at `/api/docs` when running the backend server in development mode.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
