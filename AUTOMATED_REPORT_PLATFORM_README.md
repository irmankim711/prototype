# 🤖 Automated Report Generation Platform

A full-stack platform that automatically generates AI-powered reports from form submissions with charts, insights, and Word document export capabilities.

## 🚀 Features

### Core Functionality
- **Form Submission Processing**: Accepts data from Google Forms, Microsoft Forms, and custom forms
- **AI-Powered Analysis**: Uses OpenAI to generate insights and recommendations
- **Automated Chart Generation**: Creates matplotlib/seaborn visualizations
- **Word Document Export**: Generates professional .docx reports with embedded charts
- **Real-time Status Updates**: Live progress tracking for report generation
- **Scheduled Reports**: Automated report generation on daily/weekly/monthly schedules

### Advanced Capabilities
- **Multi-format Export**: PDF, Excel, CSV, and JSON export options
- **Email Integration**: Automatic report delivery via SendGrid
- **Report Templates**: Customizable report layouts and styles
- **Data Validation**: Intelligent data quality checks and cleaning
- **Trend Analysis**: Time-series analysis and pattern recognition
- **Collaborative Features**: Report sharing and team collaboration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (Flask)       │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - API Routes    │    │ - Forms         │
│ - Report Builder│    │ - Celery Tasks  │    │ - Submissions   │
│ - Real-time UI  │    │ - AI Services   │    │ - Reports       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         └──────────────►│   Redis Queue   │◄────────────┘
                        │                 │
                        │ - Task Queue    │
                        │ - Caching       │
                        └─────────────────┘
```

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI** for modern UI components
- **TanStack Query** for data fetching
- **Socket.io** for real-time updates
- **Vite** for fast development

### Backend
- **Flask** with Python 3.11
- **Celery** for background task processing
- **Redis** for task queue and caching
- **PostgreSQL** for data persistence
- **OpenAI API** for AI analysis

### Data Processing
- **pandas** for data manipulation
- **matplotlib/seaborn** for chart generation
- **python-docx** for Word document creation
- **openpyxl** for Excel export

### Infrastructure
- **Docker** for containerization
- **GitHub Actions** for CI/CD
- **Prometheus/Grafana** for monitoring

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. Clone the Repository
```bash
git clone <repository-url>
cd automated-report-platform
```

### 2. Set Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Database
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/report_platform

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your-openai-api-key
GOOGLE_AI_API_KEY=your-google-ai-key

# Email
SENDGRID_API_KEY=your-sendgrid-key

# Security
JWT_SECRET_KEY=your-secret-key
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Manual Setup (Alternative)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Start backend
python run.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Start Celery Workers
```bash
cd backend
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info
```

## 📊 Usage Examples

### 1. HR Satisfaction Survey Reports
```python
# Automatically generate monthly HR reports
POST /api/reports/automated/generate
{
  "form_id": 1,
  "report_type": "summary",
  "date_range": "last_30_days"
}
```

### 2. Customer Feedback Analysis
```python
# Generate detailed customer feedback reports
POST /api/reports/automated/generate
{
  "form_id": 2,
  "report_type": "detailed",
  "date_range": "last_90_days"
}
```

### 3. Incident Report Summaries
```python
# Daily incident summaries with trends
POST /api/reports/automated/generate
{
  "form_id": 3,
  "report_type": "trends",
  "date_range": "last_7_days"
}
```

## 🔧 API Endpoints

### Form Submissions
```http
POST /api/forms/submit
Content-Type: application/json

{
  "form_id": 1,
  "data": {
    "employee_name": "John Doe",
    "satisfaction_score": 8,
    "feedback": "Great work environment"
  },
  "submitter": {
    "email": "john@company.com"
  },
  "source": "google_forms"
}
```

### Report Generation
```http
POST /api/reports/automated/generate
Authorization: Bearer <token>

{
  "form_id": 1,
  "report_type": "summary",
  "date_range": "last_30_days"
}
```

### Report Status
```http
GET /api/reports/automated/status/<task_id>
Authorization: Bearer <token>
```

### Download Report
```http
GET /api/reports/automated/<report_id>/download
Authorization: Bearer <token>
```

## 📈 Report Types

### Summary Reports
- Executive overview with key metrics
- Top insights and recommendations
- Basic charts and visualizations

### Detailed Reports
- Comprehensive data analysis
- Deep insights and patterns
- Multiple chart types and comparisons

### Trends Reports
- Time-series analysis
- Pattern recognition
- Predictive insights

## 🎨 Customization

### Report Templates
```json
{
  "name": "HR Monthly Report",
  "sections": [
    {
      "title": "Executive Summary",
      "type": "text",
      "content": "AI-generated summary"
    },
    {
      "title": "Key Metrics",
      "type": "metrics",
      "fields": ["satisfaction_score", "response_rate"]
    },
    {
      "title": "Charts",
      "type": "charts",
      "charts": ["daily_trend", "satisfaction_distribution"]
    }
  ]
}
```

### Chart Customization
```python
# Custom chart configuration
chart_config = {
  "daily_trend": {
    "type": "line",
    "title": "Daily Submissions",
    "x_axis": "date",
    "y_axis": "count",
    "style": "seaborn"
  }
}
```

## 🔄 Workflow

1. **Form Submission**: Data received from external forms
2. **Data Processing**: Normalize and store in PostgreSQL
3. **Trigger Analysis**: Celery task queues report generation
4. **AI Analysis**: OpenAI processes data for insights
5. **Chart Generation**: matplotlib creates visualizations
6. **Document Creation**: python-docx builds Word document
7. **Export & Share**: Download or email the report

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python -m pytest tests/integration/ -v
```

### Test Report Generation
```bash
cd backend
python test_automated_reports.py
```

### Performance Testing
```bash
cd backend
python -m locust -f tests/performance/locustfile.py
```

## 📊 Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:5000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Metrics Dashboard
- Access Grafana at `http://localhost:3000`
- Default credentials: `admin/admin`
- View system metrics and performance data

## 🚀 Deployment

### Production Setup
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with monitoring
docker-compose -f docker-compose.prod.yml --profile production --profile monitoring up -d
```

### Environment Variables
```env
# Production settings
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
OPENAI_API_KEY=your-production-key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Write comprehensive tests
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

#### Report Generation Fails
```bash
# Check Celery worker logs
docker-compose logs celery_worker

# Verify OpenAI API key
echo $OPENAI_API_KEY

# Check database connection
docker-compose exec backend python -c "from app import db; print(db.engine.execute('SELECT 1').fetchone())"
```

#### Charts Not Generating
```bash
# Install system dependencies
sudo apt-get install libfreetype6-dev libpng-dev

# Check matplotlib backend
python -c "import matplotlib; print(matplotlib.get_backend())"
```

#### Frontend Not Loading
```bash
# Clear node modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check API connection
curl http://localhost:5000/health
```

### Getting Help
- Check the [Issues](https://github.com/your-repo/issues) page
- Review the [Documentation](docs/)
- Join our [Discord](https://discord.gg/your-server)

## 🎯 Roadmap

### Upcoming Features
- [ ] Real-time collaborative editing
- [ ] Advanced chart types (3D, interactive)
- [ ] Machine learning predictions
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced scheduling options
- [ ] Report versioning
- [ ] Advanced analytics dashboard

### Performance Improvements
- [ ] Redis caching optimization
- [ ] Database query optimization
- [ ] Frontend bundle optimization
- [ ] CDN integration
- [ ] Load balancing

---

**Built with ❤️ by the Automated Report Platform Team** 