# Claude AI Integration Guide

## Overview

This application now integrates **Claude AI by Anthropic** for intelligent report generation, data analysis, and insights extraction. Claude provides advanced natural language processing capabilities to transform raw data into professional, actionable reports.

## Features

### 1. AI-Powered Report Generation
- Generates comprehensive reports with multiple sections
- Supports different report types: analysis, summary, detailed, executive
- Automatically structures content with proper sections
- Provides context-aware analysis based on your data

### 2. Executive Summaries
- Creates concise, stakeholder-ready summaries
- Highlights key findings and insights
- Provides actionable recommendations
- Professional language suitable for decision-makers

### 3. Data Insights Analysis
- Identifies key trends and patterns in your data
- Detects anomalies and outliers
- Evaluates data quality
- Suggests data-driven recommendations

### 4. Visualization Suggestions
- Analyzes data structure and recommends appropriate charts
- Prioritizes visualizations by importance
- Provides configuration details for each visualization
- Supports multiple chart types: bar, line, pie, scatter, heatmap

## Setup Instructions

### 1. Install Required Package

```bash
cd backend
pip install anthropic>=0.39.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Add your Anthropic API key to the `.env.production` file:

```env
# Anthropic Claude Configuration (PRODUCTION READY)
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

To get an API key:
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into your `.env.production` file

### 3. Verify Installation

Run the test script to verify the integration:

```bash
cd backend
python test_claude_ai_integration.py
```

## API Endpoints

### 1. Generate Report Content

**Endpoint:** `POST /api/nextgen-report-builder/ai/generate-report-content`

**Request:**
```json
{
  "data": [
    {"product": "Widget A", "sales": 1500, "revenue": 45000},
    {"product": "Widget B", "sales": 2000, "revenue": 60000}
  ],
  "reportTitle": "Q4 Sales Analysis",
  "reportType": "analysis",
  "additionalContext": "Focus on year-over-year growth"
}
```

**Response:**
```json
{
  "success": true,
  "content": {
    "executive_summary": "...",
    "data_overview": "...",
    "key_findings": "...",
    "detailed_analysis": "...",
    "trends_patterns": "...",
    "recommendations": "...",
    "conclusion": "..."
  },
  "ai_generated": true,
  "model": "claude-sonnet-4",
  "timestamp": "2025-11-03T10:30:00Z"
}
```

### 2. Generate Executive Summary

**Endpoint:** `POST /api/nextgen-report-builder/ai/executive-summary`

**Request:**
```json
{
  "data": [
    {"quarter": "Q1", "revenue": 125000, "profit": 25000},
    {"quarter": "Q2", "revenue": 135000, "profit": 28000}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "summary": "The financial analysis reveals...",
  "ai_generated": true
}
```

### 3. Analyze Data Insights

**Endpoint:** `POST /api/nextgen-report-builder/ai/analyze-insights`

**Request:**
```json
{
  "data": [
    {"month": "Jan", "visitors": 5000, "conversions": 250},
    {"month": "Feb", "visitors": 5500, "conversions": 300}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "insights": {
    "key_trends": [
      "Visitor count increasing by 10% month-over-month",
      "Conversion rate improving from 5% to 5.45%"
    ],
    "anomalies": [],
    "data_quality": ["Data appears complete and consistent"],
    "recommendations": [
      "Continue current marketing strategies",
      "Consider A/B testing to further improve conversion"
    ]
  },
  "ai_generated": true
}
```

### 4. Suggest Visualizations

**Endpoint:** `POST /api/nextgen-report-builder/ai/suggest-visualizations`

**Request:**
```json
{
  "data": [
    {"category": "Electronics", "sales": 45000, "units": 120},
    {"category": "Clothing", "sales": 32000, "units": 450}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "visualizations": [
    {
      "type": "bar",
      "title": "Sales by Category",
      "x_axis": "category",
      "y_axis": "sales",
      "description": "Compare sales performance across categories",
      "priority": 5
    }
  ],
  "ai_generated": true
}
```

### 5. Check AI Status

**Endpoint:** `GET /api/nextgen-report-builder/ai/status`

**Response:**
```json
{
  "success": true,
  "ai_enabled": true,
  "service": "Claude AI (Anthropic)",
  "model": "claude-sonnet-4",
  "features": {
    "report_generation": true,
    "executive_summary": true,
    "data_insights": true,
    "visualization_suggestions": true
  }
}
```

## Usage Examples

### Python Usage

```python
from app.services.ai_report_service import AIReportService

# Initialize service
ai_service = AIReportService()

# Generate report content
data = [
    {"product": "A", "sales": 1500},
    {"product": "B", "sales": 2000}
]

result = ai_service.generate_report_content(
    data=data,
    report_title="Sales Report",
    report_type="analysis"
)

print(result['content']['executive_summary'])
```

### Frontend Integration

```javascript
// Generate AI report
const response = await fetch('/api/nextgen-report-builder/ai/generate-report-content', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    data: excelData,
    reportTitle: 'Monthly Analysis',
    reportType: 'executive'
  })
});

const result = await response.json();
console.log(result.content);
```

## Report Types

### 1. Analysis (Default)
- Detailed analysis with insights, trends, and patterns
- Suitable for technical audiences
- Comprehensive data examination

### 2. Summary
- Concise summary of key findings
- Quick overview of important points
- Best for time-sensitive reviews

### 3. Detailed
- Comprehensive detailed analysis
- All relevant metrics and statistics
- In-depth examination of data

### 4. Executive
- Executive-level summary
- Strategic insights
- High-level recommendations
- Suitable for stakeholders and decision-makers

## Fallback Behavior

If the Claude AI service is unavailable (no API key or service error), the system automatically falls back to:
- Basic statistical analysis using pandas
- Template-based report generation
- Simple data summaries
- Standard visualization suggestions

This ensures reports can still be generated even without AI.

## Cost Considerations

Claude AI uses a token-based pricing model:
- Input tokens: Text sent to the API
- Output tokens: Text generated by the API

Current model: **Claude Sonnet 4**
- Balanced performance and cost
- Suitable for production use
- Fast response times

Monitor your usage at: https://console.anthropic.com/

## Best Practices

1. **Data Quality**
   - Ensure data is clean and well-structured
   - Remove duplicates and null values
   - Use meaningful column names

2. **Context**
   - Provide additional context when available
   - Specify the audience for the report
   - Include relevant business objectives

3. **Report Types**
   - Use "executive" for stakeholders
   - Use "detailed" for technical teams
   - Use "summary" for quick reviews
   - Use "analysis" for general purposes

4. **Error Handling**
   - Always check the `success` field in responses
   - Handle fallback scenarios gracefully
   - Log errors for debugging

5. **Performance**
   - Cache frequently requested reports
   - Limit data size for faster processing
   - Use pagination for large datasets

## Troubleshooting

### Issue: "AI features unavailable"
**Solution:** Check that ANTHROPIC_API_KEY is set in your environment

### Issue: "API rate limit exceeded"
**Solution:** Monitor usage at console.anthropic.com and upgrade plan if needed

### Issue: "Invalid API key"
**Solution:** Verify the API key is correct and active

### Issue: "Slow response times"
**Solution:** Reduce data size or use summary report type

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── ai_report_service.py          # Main AI service
│   │   └── ai_enhanced_excel_service.py  # AI Excel generation
│   └── routes/
│       └── nextgen_report_builder.py     # API endpoints
├── test_claude_ai_integration.py         # Test script
├── requirements.txt                       # Updated with anthropic
└── .env.production                        # Contains ANTHROPIC_API_KEY
```

## Report Template Requirements

The report templates are located in:
```
backend/templates/
├── report_template_copy.docx
├── 04- LAPORAN FU _ PUNCAK ALAM_final.docx
└── report_templates/
    └── 04- LAPORAN FU _ PUNCAK ALAM (1).docx
```

Ensure these templates exist before generating reports. The system will automatically find and use appropriate templates based on the template ID provided.

## Security Notes

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables for configuration
   - Rotate keys periodically
   - Restrict key permissions if possible

2. **Data Privacy**
   - Be aware that data is sent to Anthropic's API
   - Review Anthropic's data usage policy
   - Consider data sensitivity before using AI features
   - Use fallback mode for highly sensitive data

## Support and Resources

- **Anthropic Documentation:** https://docs.anthropic.com/
- **API Reference:** https://docs.anthropic.com/claude/reference/
- **Claude Console:** https://console.anthropic.com/
- **Pricing:** https://www.anthropic.com/pricing

## Migration from OpenAI

If you were previously using OpenAI, Claude offers:
- Longer context windows
- More accurate analysis
- Better structured outputs
- Competitive pricing
- Strong safety features

The service includes automatic fallback, so both can coexist in your application.

## Next Steps

1. ✅ Add ANTHROPIC_API_KEY to `.env.production`
2. ✅ Run test script: `python test_claude_ai_integration.py`
3. ✅ Test endpoints using Postman or frontend
4. ✅ Monitor usage at console.anthropic.com
5. ✅ Integrate with your frontend application

## Changelog

### Version 1.0.0 (2025-11-03)
- Initial Claude AI integration
- Added AIReportService with 4 main features
- Created 5 new API endpoints
- Added comprehensive fallback support
- Created test suite and documentation
