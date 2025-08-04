# 🤖 Automated Report Generation System

A full-stack platform that automatically generates AI-powered reports from form submissions. The system accepts submissions from Google Forms, Microsoft Forms, and custom public forms, then uses AI to analyze the data and create professional Word documents with charts and insights.

## 🎯 System Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ Form Users  │    │ Data Store   │    │ AI Analysis │    │ Report Gen   │
│             │───▶│              │───▶│             │───▶│              │
│ • Google    │    │ PostgreSQL   │    │ OpenAI GPT  │    │ Word + Charts│
│ • Microsoft │    │ Normalized   │    │ Insights    │    │ Email Export │
│ • Public    │    │ Form Data    │    │ Trends      │    │ Download     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## ✨ Key Features

### 🔄 **Automated Workflow**

- **Universal Form Support**: Google Forms, Microsoft Forms, and custom public forms
- **Automatic Triggers**: Reports generate automatically when forms receive submissions
- **Background Processing**: Celery-powered async report generation
- **Real-time Updates**: WebSocket-powered status tracking

### 🧠 **AI-Powered Analysis**

- **OpenAI Integration**: GPT-4 powered data analysis and insights
- **Trend Identification**: Automatic detection of patterns in form responses
- **Smart Recommendations**: AI-generated actionable insights
- **Key Metrics**: Automated calculation of important statistics

### 📊 **Professional Reports**

- **Word Documents**: Professional .docx reports with embedded charts
- **Interactive Charts**: Matplotlib-generated visualizations
- **Editable Content**: React-based report editor for customization
- **Multiple Formats**: Word, Excel, PDF export options

### 🌐 **Modern Frontend**

- **React Dashboard**: Real-time report monitoring and management
- **Material-UI Design**: Professional, responsive interface
- **Live Preview**: In-browser report preview before download
- **Batch Operations**: Multi-report management and bulk actions

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL or Supabase account
- OpenAI API key
- Redis (for Celery)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd automated-report-system

# Run the quick setup script
python quick_setup.py
```

### 2. Environment Configuration

```bash
# Backend environment (.env)
cp backend/env.example backend/.env

# Configure these essential variables:
DATABASE_URL=postgresql://user:pass@localhost:5432/reports_db
OPENAI_API_KEY=sk-your-openai-api-key
CELERY_BROKER_URL=redis://localhost:6379/0
SENDGRID_API_KEY=your-sendgrid-key
```

### 3. Database Setup

```bash
cd backend
python init_db.py
```

### 4. Start Services

```bash
# Backend
cd backend
python run.py

# Frontend (new terminal)
cd frontend
npm run dev

# Celery Worker (new terminal)
cd backend
celery -A app.celery worker --loglevel=info
```

## 📡 API Endpoints

### Form Submission

```http
POST /api/public-forms/submit
Content-Type: application/json

{
  "form_id": "survey-001",
  "form_title": "Customer Feedback",
  "data": {
    "customer_name": "John Doe",
    "rating": 5,
    "feedback": "Excellent service!"
  },
  "source": "public"
}
```

### Batch Submission

```http
POST /api/public-forms/batch-submit
Content-Type: application/json

{
  "submissions": [
    {
      "form_id": "survey-001",
      "data": { ... }
    }
  ]
}
```

### Trigger Report Generation

```http
POST /api/public-forms/generate-report
Content-Type: application/json

{
  "form_id": "survey-001",
  "title": "Monthly Analysis",
  "include_charts": true,
  "analysis_type": "comprehensive"
}
```

### Get Reports

```http
GET /api/public-forms/reports
GET /api/public-forms/reports?form_id=survey-001
GET /api/public-forms/reports/{report_id}
```

### Download Report

```http
GET /api/public-forms/reports/{report_id}/download
```

## 🔧 System Architecture

### Backend Components

#### **Data Flow Architecture**

```python
# app/routes/public_forms.py - Main API endpoints
# app/services/data_normalizer.py - Form data standardization
# app/services/ai_service.py - OpenAI integration
# app/services/report_generator.py - Word document creation
# app/services/email_service.py - Automated email delivery
# app/tasks/report_tasks.py - Celery background tasks
```

#### **Database Schema**

```sql
-- Form Submissions
CREATE TABLE form_submissions (
    id UUID PRIMARY KEY,
    form_id VARCHAR NOT NULL,
    form_title VARCHAR,
    data JSONB NOT NULL,
    normalized_data JSONB,
    source VARCHAR NOT NULL,
    submitted_at TIMESTAMP DEFAULT NOW()
);

-- Generated Reports
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    form_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    ai_insights JSONB,
    file_path VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **AI Service Integration**

```python
class AIService:
    def analyze_form_data_with_ai(self, form_data, form_title):
        """Analyze form data and generate insights"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "Analyze form data and provide insights..."
            }]
        )
        return self.parse_ai_response(response)
```

### Frontend Components

#### **React Component Structure**

```typescript
// src/components/ReportDashboard.tsx - Main dashboard
// src/components/ReportPreview.tsx - Report preview modal
// src/components/ReportEditor.tsx - Interactive report editor
// src/services/reportService.ts - API integration
// src/types/reports.ts - TypeScript type definitions
```

#### **State Management**

```typescript
// TanStack Query for server state
const { data: reports } = useQuery({
  queryKey: ["reports"],
  queryFn: () => reportService.getAllReports(),
  refetchInterval: 5000, // Real-time updates
});

// Mutations for actions
const generateMutation = useMutation({
  mutationFn: reportService.generateReport,
  onSuccess: () => queryClient.invalidateQueries(["reports"]),
});
```

## 🔌 External Integrations

### Google Forms Webhook

```http
POST /api/public-forms/webhooks/google-forms
Content-Type: application/json

{
  "form_id": "google-form-123",
  "form_title": "Survey",
  "responses": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "answers": {
        "Name": "John Doe",
        "Rating": "5"
      }
    }
  ]
}
```

### Microsoft Forms Integration

```http
POST /api/public-forms/webhooks/microsoft-forms
Content-Type: application/json

{
  "form_id": "ms-form-456",
  "form_title": "Feedback Form",
  "submissions": [
    {
      "submissionTime": "2024-01-15T10:30:00Z",
      "responses": {
        "r1": { "question": "Name", "answer": "Jane Smith" },
        "r2": { "question": "Rating", "answer": "4" }
      }
    }
  ]
}
```

## 📊 Sample AI Analysis Output

```json
{
  "summary": "Analysis of 150 customer feedback submissions reveals high satisfaction with an average rating of 4.2/5. Key strengths include product quality and customer service.",
  "trends": [
    "Customer satisfaction increased 15% over the past month",
    "Product quality mentions increased by 23%",
    "Delivery complaints decreased by 18%"
  ],
  "recommendations": [
    "Focus marketing on product quality advantages",
    "Implement feedback system for delivery improvements",
    "Consider expanding customer service team"
  ],
  "keyMetrics": {
    "averageRating": 4.2,
    "totalResponses": 150,
    "recommendationRate": 87,
    "completionRate": 94
  }
}
```

## 🧪 Testing

### Run System Tests

```bash
# Test the complete workflow
python test_automation_system.py

# Run backend tests
cd backend
python -m pytest tests/

# Run frontend tests
cd frontend
npm test
```

### Manual Testing Flow

1. Submit test forms via API
2. Trigger report generation
3. Monitor progress in React dashboard
4. Preview and edit reports
5. Download/email final reports

## 📦 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t report-backend ./backend
docker build -t report-frontend ./frontend
```

### Environment Variables

```env
# Backend
DATABASE_URL=postgresql://user:pass@db:5432/reports
OPENAI_API_KEY=sk-your-key
CELERY_BROKER_URL=redis://redis:6379/0
SENDGRID_API_KEY=your-sendgrid-key

# Frontend
REACT_APP_API_URL=https://api.yourapp.com
```

## 🔍 Monitoring & Debugging

### Backend Logs

```bash
# View Flask logs
tail -f backend/logs/app.log

# View Celery logs
tail -f backend/logs/celery.log
```

### Health Checks

```http
GET /api/health
GET /api/public-forms/status
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📋 Roadmap

### Phase 1 (Current)

- ✅ Core form submission API
- ✅ AI-powered analysis
- ✅ Word report generation
- ✅ React dashboard

### Phase 2 (Next)

- 🔄 Real-time WebSocket updates
- 🔄 Advanced chart types
- 🔄 Custom report templates
- 🔄 Scheduled report generation

### Phase 3 (Future)

- 📅 Multi-language support
- 📅 Advanced analytics dashboard
- 📅 API rate limiting
- 📅 Enterprise features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@yourapp.com
- 💬 Discord: [Your Discord Server]
- 📖 Documentation: [Your Docs URL]
- 🐛 Issues: [GitHub Issues](issues-url)

---

**Built with ❤️ using Flask, React, OpenAI, and lots of coffee ☕**
