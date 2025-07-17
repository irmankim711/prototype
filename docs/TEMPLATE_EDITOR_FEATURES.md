# Template Editor Features

## Overview

The report builder system now includes advanced template editing capabilities with live preview functionality. This allows users to:

1. **Live Preview**: See a real-time preview of how their filled template will look
2. **Template Content Analysis**: View the structure and placeholders in their templates
3. **Advanced Data Mapping**: Auto-map Excel data to template placeholders
4. **Interactive Editing**: Edit template content directly in the browser

## New Backend Endpoints

### 1. Template Content Extraction
```
GET /mvp/templates/{template_name}/content
```
Extracts the raw content from a Word template for frontend editing. Returns:
- `content`: Array of template paragraphs with styling information
- `placeholders`: List of all placeholders found in the template

### 2. Live Preview Generation
```
POST /mvp/templates/{template_name}/preview
```
Generates a live preview of the filled template as a PDF. Accepts:
- `data`: Object containing placeholder values

Returns:
- `preview`: Base64-encoded PDF data URL
- `filename`: Generated preview filename

### 3. Enhanced Template Listing
```
GET /mvp/templates/list
```
Returns available Word templates with metadata.

### 4. Placeholder Extraction
```
GET /mvp/templates/{template_name}/placeholders
```
Extracts all placeholders from a Word template.

## Frontend Components

### TemplateEditor Component

The new `TemplateEditor` component provides a tabbed interface with:

#### Tab 1: Data Fields
- Editable form fields for each template placeholder
- Auto-populated from Excel data
- Real-time validation and updates

#### Tab 2: Live Preview
- Generate PDF preview of filled template
- Embedded iframe display
- Refresh functionality for updated previews

#### Tab 3: Template Content
- View template structure and placeholders
- Analyze template complexity
- Understand template requirements

## Features

### Live Preview
- **Backend-rendered PDFs**: Uses ReportLab to generate accurate PDF previews
- **Real-time updates**: Preview refreshes when data changes
- **Embedded display**: PDFs displayed directly in the browser
- **Error handling**: Graceful fallbacks for preview generation failures

### Template Analysis
- **Placeholder detection**: Automatically identifies all template variables
- **Content structure**: Shows template paragraphs and styling
- **Complexity assessment**: Helps users understand template requirements

### Data Mapping
- **Auto-mapping**: Matches Excel column names to template placeholders
- **Manual override**: Users can manually adjust mappings
- **Validation**: Ensures all required placeholders are filled

### Interactive Editing
- **Field-level editing**: Edit individual placeholder values
- **Bulk operations**: Clear or update multiple fields at once
- **Real-time validation**: Immediate feedback on data changes

## Technical Implementation

### Backend Dependencies
```python
python-docx>=0.8.11    # Word document processing
docxtpl>=0.16.7        # Template rendering
reportlab>=4.0.0       # PDF generation
```

### Frontend Dependencies
```javascript
@ckeditor/ckeditor5-react    # Rich text editing (optional)
@mui/material               # UI components
```

### API Integration
The frontend communicates with the backend through new API functions:
- `fetchTemplateContent()`: Extract template structure
- `generateLivePreview()`: Generate PDF previews
- `fetchTemplatePlaceholders()`: Get placeholder list

## Usage Workflow

1. **Import Data**: Upload Excel file or import from Google Sheets
2. **Select Template**: Choose from available Word templates
3. **Review & Edit**: 
   - Fill in template data fields
   - Generate live preview
   - Analyze template structure
4. **Generate Report**: Download the final filled template

## Benefits

### For Users
- **Visual feedback**: See exactly how their report will look
- **Error prevention**: Catch issues before generating final report
- **Efficiency**: Streamlined workflow from data to finished report
- **Flexibility**: Edit both data and template content

### For Developers
- **Modular design**: Easy to extend and customize
- **Error handling**: Robust error handling and fallbacks
- **Performance**: Efficient PDF generation and caching
- **Maintainability**: Clean separation of concerns

## Future Enhancements

### Planned Features
1. **Template Versioning**: Track changes to templates over time
2. **Collaborative Editing**: Multiple users editing the same template
3. **Advanced Styling**: More sophisticated PDF styling options
4. **Template Library**: Browse and search available templates
5. **Custom Placeholders**: User-defined placeholder types

### Technical Improvements
1. **Caching**: Cache generated previews for better performance
2. **Async Processing**: Background preview generation
3. **Compression**: Optimize PDF file sizes
4. **Security**: Enhanced input validation and sanitization

## Testing

Run the test script to verify backend functionality:
```bash
cd backend
python test_template_endpoints.py
```

This will test:
- Template listing
- Placeholder extraction
- Content analysis
- Live preview generation

## Troubleshooting

### Common Issues

1. **Preview not generating**: Check if template has valid placeholders
2. **PDF display issues**: Ensure browser supports PDF iframes
3. **Template loading errors**: Verify template file format (.docx)
4. **Performance issues**: Consider caching for large templates

### Debug Steps

1. Check browser console for JavaScript errors
2. Verify backend server is running
3. Test API endpoints directly with curl/Postman
4. Check template file format and structure 