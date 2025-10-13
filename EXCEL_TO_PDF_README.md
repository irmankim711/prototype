# Excel-to-PDF Report Generation System

A comprehensive system for uploading Excel files and generating professional PDF reports using ConvertAPI integration.

## 🚀 Features

- **Excel File Upload**: Support for `.xlsx`, `.xls`, and `.xlsm` files
- **Automatic Data Analysis**: Extract insights, statistics, and recommendations from Excel data
- **Multiple Output Formats**: Generate reports in both DOCX and PDF formats
- **ConvertAPI Integration**: High-quality DOCX-to-PDF conversion using ConvertAPI service
- **Professional Templates**: Multiple report templates for different use cases
- **Real-time Progress**: Live progress tracking during upload and generation
- **Download Management**: Easy download links for generated reports

## 📋 Prerequisites

1. **Backend Dependencies**:
   ```bash
   pip install pandas openpyxl python-docx reportlab requests
   ```

2. **ConvertAPI Account**:
   - Sign up at [ConvertAPI](https://www.convertapi.com/)
   - Get your API key
   - Add to your `.env` file: `convertAPI=your_api_key_here`

3. **Frontend Dependencies**:
   ```bash
   npm install @mui/material @mui/icons-material react-dropzone
   ```

## 🛠️ Installation & Setup

### Backend Setup

1. **Environment Configuration**:
   ```bash
   # In your .env file
   convertAPI=your_convertapi_key_here
   UPLOAD_FOLDER=uploads
   ```

2. **Service Registration**:
   The system automatically registers the following services:
   - `ConvertAPIService`: Handles DOCX-to-PDF conversion
   - `ExcelReportService`: Processes Excel files and generates reports
   - `ExcelToPDFAPI`: REST API endpoints

### Frontend Setup

1. **Component Import**:
   ```typescript
   import ExcelReportUploader from './components/ExcelUpload/ExcelReportUploader';
   ```

2. **Usage**:
   ```typescript
   <ExcelReportUploader
     onReportGenerated={(report) => console.log('Report generated:', report)}
     maxFiles={1}
     maxSize={10 * 1024 * 1024} // 10MB
     disabled={false}
   />
   ```

## 🔧 API Endpoints

### 1. Upload and Generate Report
**POST** `/api/excel-to-pdf/upload-and-generate`

**Form Data:**
- `file`: Excel file (.xlsx, .xls, .xlsm)
- `title`: Report title (optional)
- `formats`: Comma-separated formats (e.g., "docx,pdf")
- `template`: Template type ("excel_analysis", "financial", "executive")

**Response:**
```json
{
  "success": true,
  "report_id": 123,
  "title": "Analysis Report - data.xlsx",
  "formats": {
    "docx": {
      "url": "/api/reports/download/report_20250101_120000.docx",
      "filename": "report_20250101_120000.docx",
      "size": 1024000
    },
    "pdf": {
      "url": "/api/reports/download/report_20250101_120000.pdf",
      "filename": "report_20250101_120000.pdf",
      "size": 2048000,
      "method": "convertapi"
    }
  },
  "metadata": {
    "source_file": "data.xlsx",
    "generated_at": "2025-01-01T12:00:00Z",
    "template": "excel_analysis",
    "sheets_processed": 3
  }
}
```

### 2. Get Supported Formats
**GET** `/api/excel-to-pdf/supported-formats`

### 3. Test ConvertAPI Connection
**POST** `/api/excel-to-pdf/convert-test`

### 4. Get User Reports Status
**GET** `/api/excel-to-pdf/status`

## 🎨 Report Templates

### 1. Excel Data Analysis (`excel_analysis`)
- Comprehensive data overview
- Sheet-by-sheet analysis
- Statistical summaries
- Data quality assessment
- Insights and recommendations

### 2. Financial Report (`financial`)
- Optimized for financial data
- Emphasis on numerical analysis
- Charts and trends
- Performance metrics

### 3. Executive Summary (`executive`)
- High-level overview
- Key insights only
- Presentation-ready format
- Minimal technical details

## 🔍 How It Works

1. **File Upload**: User uploads an Excel file through the drag-and-drop interface
2. **Data Processing**: Backend extracts and analyzes data from all sheets
3. **Report Generation**:
   - Creates DOCX report using python-docx
   - Generates comprehensive analysis with statistics and insights
4. **PDF Conversion**:
   - Primary: Uses ConvertAPI for high-quality DOCX-to-PDF conversion
   - Fallback: Uses ReportLab for direct PDF generation
5. **Download**: User can download both DOCX and PDF versions

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_excel_to_pdf_workflow.py
```

The test script will:
- Check application health
- Verify ConvertAPI connection
- Test supported formats endpoint
- Create sample Excel data
- Upload file and generate report
- Verify download URLs

## 📊 Data Analysis Features

The system automatically analyzes Excel data and provides:

### Statistics Per Sheet:
- Row and column counts
- Data type identification
- Missing data analysis
- Numeric column statistics (mean, min, max)
- Text column unique values
- Date range analysis

### Insights Generation:
- Dataset overview
- Largest sheet identification
- Data type distribution
- Quality assessment

### Recommendations:
- Data cleaning suggestions
- Analysis opportunities
- Optimization recommendations

## 🛡️ Error Handling

The system includes comprehensive error handling for:

- **File Validation**: Size, type, and format validation
- **ConvertAPI Failures**: Automatic fallback to direct PDF generation
- **Data Processing Errors**: Graceful handling of corrupted Excel files
- **Authentication**: Firebase token validation
- **Rate Limiting**: Prevents API abuse

## 🔐 Security Features

- **File Type Validation**: Only allows Excel files
- **Size Limits**: Configurable file size restrictions
- **Authentication**: Firebase token required
- **Temporary File Cleanup**: Automatic cleanup of uploaded files
- **Input Sanitization**: Secure handling of user inputs

## 📈 Performance Optimization

- **Async Processing**: Large files processed asynchronously
- **Progress Tracking**: Real-time upload and processing progress
- **Efficient Memory Usage**: Streaming file processing
- **Caching**: ConvertAPI response caching for repeated requests

## 🚨 Troubleshooting

### Common Issues:

1. **ConvertAPI Failures**:
   - Check API key validity
   - Verify account credits
   - System falls back to ReportLab PDF generation

2. **Large File Processing**:
   - Files > 5MB automatically use async processing
   - Increase timeout settings if needed

3. **Memory Issues**:
   - Limit Excel data to first 1000 rows for processing
   - Use streaming for large datasets

4. **Authentication Errors**:
   - Ensure Firebase token is valid
   - Check token expiration

## 📝 Configuration Options

### Backend (.env):
```bash
convertAPI=your_api_key_here
UPLOAD_FOLDER=uploads
MAX_EXCEL_ROWS=1000
ASYNC_THRESHOLD_MB=5
```

### Frontend:
```typescript
<ExcelReportUploader
  maxFiles={1}                    // Maximum files per upload
  maxSize={10 * 1024 * 1024}     // Maximum file size (bytes)
  disabled={false}                // Disable component
  onReportGenerated={callback}    // Success callback
/>
```

## 🔄 Future Enhancements

- [ ] Chart generation from Excel data
- [ ] Custom template builder
- [ ] Batch processing for multiple files
- [ ] Advanced data visualization
- [ ] Email delivery of reports
- [ ] Scheduled report generation
- [ ] Custom branding options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Run the test script to verify setup
- Review the error logs for detailed information
- Contact the development team

---

**Note**: This system requires a valid ConvertAPI subscription for optimal PDF generation. The free tier includes 100 conversions per month.