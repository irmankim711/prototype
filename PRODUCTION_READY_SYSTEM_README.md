# Production-Ready Automated Report Generation System

A comprehensive, production-ready system that automatically generates PDF, DOCX, and Excel reports from form submissions with end-to-end automation, background processing, and real-time monitoring.

## 🚀 Features

### Core Functionality
- **Multi-Format Report Generation**: PDF (reportlab), DOCX (python-docx), Excel (openpyxl)
- **Automated Pipeline**: Form submission → Excel export → PDF/DOCX report generation
- **Background Processing**: Celery + Redis for scalable task processing
- **Real-time Status**: Progress tracking and status monitoring
- **Inline Editing**: Edit report data and regenerate reports
- **Preview System**: View reports before download
- **Bulk Operations**: Export multiple forms simultaneously

### Production Features
- **Health Monitoring**: Comprehensive system health checks
- **Error Handling**: Graceful error handling with retry logic
- **Rate Limiting**: API rate limiting for security
- **JWT Authentication**: Secure API access
- **CORS Support**: Frontend integration ready
- **File Management**: Automatic cleanup and storage optimization
- **Scalability**: Handles 1,000+ records efficiently

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Flask Backend  │    │  Celery Workers │
│                 │    │                 │    │                 │
│ • Report Preview│◄──►│ • API Endpoints │◄──►│ • PDF Generation│
│ • Edit Interface│    │ • Authentication│    │ • DOCX Creation │
│ • Download UI   │    │ • Rate Limiting │    │ • Excel Export  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │                 │
                       │ • Users         │
                       │ • Forms         │
                       │ • Submissions   │
                       │ • Reports       │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      Redis      │
                       │                 │
                       │ • Task Queue    │
                       │ • Result Store  │
                       │ • Caching       │
                       └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Git

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prototype
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create `.env` file in the backend directory:

```env
# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
BASE_URL=http://localhost:5000

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/report_system

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Upload Directories
UPLOAD_FOLDER=uploads
REPORTS_FOLDER=uploads/reports
EXPORTS_FOLDER=uploads/exports

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/0
```

#### Database Setup
```bash
# Initialize database
python init_db.py

# Run migrations (if using Flask-Migrate)
flask db upgrade
```

#### Start Celery Worker
```bash
# Start Celery worker
celery -A app.celery_enhanced worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A app.celery_enhanced beat --loglevel=info
```

#### Start Backend Server
```bash
# Development
python run.py

# Production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Environment Configuration
Create `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:5000
VITE_APP_NAME=Automated Report System
```

#### Start Development Server
```bash
npm run dev
```

#### Build for Production
```bash
npm run build
```

## 🔌 API Endpoints

### Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Report Generation

#### Generate Report
```http
POST /api/reports/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Monthly Sales Report",
  "description": "Comprehensive sales analysis for Q1 2024",
  "data": {
    "period": "Q1 2024",
    "sales_data": [...],
    "analytics": {...}
  },
  "config": {
    "template": "business_report",
    "include_charts": true,
    "format": ["pdf", "docx", "excel"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report generation started",
  "report_id": 123,
  "status": "pending",
  "download_urls": {
    "pdf": "/api/reports/123/download/pdf",
    "docx": "/api/reports/123/download/docx",
    "excel": "/api/reports/123/download/excel"
  }
}
```

#### Get Report Status
```http
GET /api/reports/{report_id}/status
Authorization: Bearer <token>
```

#### Preview Report
```http
GET /api/reports/{report_id}/preview
Authorization: Bearer <token>
```

#### Edit Report
```http
PUT /api/reports/{report_id}/edit
Content-Type: application/json
Authorization: Bearer <token>

{
  "generated_data": {
    "updated_data": "..."
  }
}
```

#### Download Report
```http
GET /api/reports/{report_id}/download/{file_type}
Authorization: Bearer <token>
```

### Excel Export

#### Export Form to Excel
```http
POST /api/forms/{form_id}/export-excel
Content-Type: application/json
Authorization: Bearer <token>

{
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-03-31"
  },
  "filters": {
    "status": "approved"
  },
  "include_metadata": true,
  "max_records": 10000,
  "immediate": false
}
```

#### Download Excel Export
```http
GET /api/forms/{form_id}/download-excel
Authorization: Bearer <token>
```

### Health Monitoring

#### System Health Check
```http
GET /api/health
```

#### Database Health
```http
GET /api/health/database
```

#### Worker Health
```http
GET /api/health/workers
```

#### Detailed Health Check
```http
GET /api/health/detailed
```

## 📱 Frontend Components

### Report Preview & Edit Component

The `ReportPreviewEdit` component provides:

- **Preview Tab**: View report information and status
- **Edit Tab**: Modify report data with JSON editor
- **Downloads Tab**: Download generated files (PDF, DOCX, Excel)
- **Real-time Updates**: Progress tracking and status updates

### Usage Example

```tsx
import ReportPreviewEdit from './components/ReportPreviewEdit';

function App() {
  const [showReport, setShowReport] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);

  const handleReportUpdated = (reportId: number) => {
    // Handle report update
    console.log(`Report ${reportId} updated`);
  };

  return (
    <div>
      {showReport && selectedReportId && (
        <ReportPreviewEdit
          reportId={selectedReportId}
          onClose={() => setShowReport(false)}
          onReportUpdated={handleReportUpdated}
        />
      )}
    </div>
  );
}
```

## 🔄 Background Tasks

### Celery Tasks

The system uses Celery for background processing:

- **Report Generation**: `generate_comprehensive_report_task`
- **Excel Export**: `export_form_to_excel_task`
- **Auto-Report Generation**: `auto_generate_form_report_task`
- **Cleanup**: `cleanup_old_reports_task`
- **Health Monitoring**: `health_check_task`

### Task Configuration

```python
# Celery configuration
CELERY_CONFIG = {
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_routes': {
        'app.tasks.report_tasks.*': {'queue': 'reports'},
        'app.tasks.export_tasks.*': {'queue': 'exports'},
    }
}
```

## 🚀 Production Deployment

### Docker Deployment

#### Backend Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/reports
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: ./backend
    command: celery -A app.celery_enhanced worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/reports
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: reports
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Environment Variables

#### Production Environment
```env
FLASK_ENV=production
SECRET_KEY=<strong-secret-key>
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
BASE_URL=https://yourdomain.com
UPLOAD_FOLDER=/app/uploads
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **`/api/health`**: Overall system health
- **`/api/health/database`**: Database connectivity
- **`/api/health/workers`**: Celery worker status
- **`/api/health/detailed`**: Comprehensive health check

### Health Check Response

```json
{
  "service": "automated_report_platform",
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "connection": "connected",
      "tables": {
        "users": 150,
        "forms": 25,
        "submissions": 1250,
        "reports": 89
      }
    },
    "redis": {
      "status": "healthy",
      "connection": "connected",
      "workers": "active"
    },
    "filesystem": {
      "status": "healthy",
      "upload_directory": "accessible",
      "permissions": "read_write"
    }
  }
}
```

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- CORS configuration

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- File upload security
- Secure file storage

## 📈 Performance & Scalability

### Optimization Features
- Background task processing
- Efficient database queries
- File streaming for large downloads
- Automatic cleanup of old files
- Redis caching

### Scalability Considerations
- Horizontal scaling with multiple Celery workers
- Database connection pooling
- Load balancing ready
- Microservices architecture support

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Testing
```bash
cd frontend
npm test
```

### API Testing
```bash
# Test report generation
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Report",
    "data": {"test": "data"},
    "config": {"template": "default"}
  }'

# Test health check
curl http://localhost:5000/api/health
```

## 📝 Example Workflows

### 1. Form Submission → Auto-Report Generation

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Celery
    participant Database

    User->>Frontend: Submit Form
    Frontend->>Backend: POST /api/forms/submit
    Backend->>Database: Save Submission
    Backend->>Celery: Trigger Auto-Report Task
    Celery->>Backend: Generate Excel Export
    Celery->>Backend: Generate PDF Report
    Celery->>Backend: Generate DOCX Report
    Backend->>Database: Update Report Status
    Backend->>Frontend: Report Ready Notification
```

### 2. Manual Report Generation

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Celery

    User->>Frontend: Request Report
    Frontend->>Backend: POST /api/reports/generate
    Backend->>Celery: Start Report Generation
    Backend->>Frontend: Task ID & Status
    Frontend->>Backend: Poll Status
    Backend->>Frontend: Progress Updates
    Backend->>Frontend: Completion Notification
    User->>Frontend: Download Report
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Celery Worker Not Starting
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
celery -A app.celery_enhanced inspect active
```

#### 2. Database Connection Issues
```bash
# Test database connection
python -c "from app import db; db.session.execute('SELECT 1')"
```

#### 3. File Upload Issues
```bash
# Check directory permissions
ls -la uploads/
chmod 755 uploads/
```

#### 4. Memory Issues with Large Reports
```bash
# Increase Celery memory limits
celery -A app.celery_enhanced worker --loglevel=info --max-memory-per-child=500000
```

### Logs

#### Backend Logs
```bash
# Flask logs
tail -f logs/app.log

# Celery logs
tail -f logs/celery.log
```

#### Frontend Logs
```bash
# Browser console
# Check Network tab for API calls
```

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [React Documentation](https://reactjs.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Dependencies
- **Backend**: Flask, SQLAlchemy, Celery, Redis, PostgreSQL
- **Frontend**: React, TypeScript, Tailwind CSS
- **Report Generation**: reportlab, python-docx, openpyxl

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Check system health endpoints

---

**Built with ❤️ for production-ready report automation**
