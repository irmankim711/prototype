# Template System Fix Guide

## Problem Summary

The report generation system was creating plain black & white reports with minimal styling instead of using the actual formatted DOCX templates. Additionally, templates were not appearing properly in the frontend.

## Root Causes Identified

1. **Aggressive Template Filtering**: The backend API was filtering templates to only show "PUNCAK ALAM" templates
2. **Minimal Report Generation**: The export service was creating simple reports with basic tables instead of using actual template files
3. **Missing Template Registration**: Templates in the filesystem were not registered in the database

## Solutions Implemented

### 1. Fixed Template API Filtering
**File**: `backend/app/routes/templates_api.py`

**What Changed**: Removed the aggressive filtering that only showed Puncak Alam templates

**Before**:
```python
# ONLY show the Puncak Alam template
templates = [t for t in all_templates if 'PUNCAK ALAM' in t.get('name', '').upper() or 'LAPORAN FU' in t.get('name', '').upper()]
```

**After**:
```python
# Get all templates
templates = template_service.get_templates(user_id=user_id, filters=filters)
```

### 2. Enhanced Export Service to Use Real Templates
**File**: `backend/app/services/export_service.py`

**What Changed**:
- Export service now searches for and loads actual DOCX template files
- Templates are loaded from database first, then falls back to file system search
- All original template formatting, styling, and design is preserved

**Key Changes**:
```python
def _export_docx(self, template_id: str, context: Dict, reports_dir: str) -> str:
    # 1. Try to find template from database
    template_record = Template.query.filter_by(id=int(template_id), is_active=True).first()

    # 2. Use actual template file with all formatting
    tpl = DocxTemplate(template_path)
    tpl.render(context)
    tpl.save(output_path)
```

**New Helper Method**:
```python
def _find_template_file(self, templates_dir: str, template_id: str) -> Optional[str]:
    # Searches for template files in multiple locations
    # Returns the first matching template found
```

### 3. Created Template Registration Script
**File**: `backend/register_templates.py`

A new script that:
- Scans the `backend/templates/` directory for DOCX files
- Registers each template in the database
- Updates existing templates if paths changed
- Makes templates visible in the frontend

## How to Use

### Step 1: Register Templates in Database

Run the registration script to make templates available:

```bash
cd backend
python register_templates.py
```

Expected output:
```
Registering templates from backend/templates directory...
------------------------------------------------------------
Registered template 'Laporan Follow-up Puncak Alam' (ID: 1)
------------------------------------------------------------

All templates registered successfully!

Registered Templates:
  - ID: 1 | Name: Laporan Follow-up Puncak Alam
    File: C:\...\backend\templates\04- LAPORAN FU _ PUNCAK ALAM_final.docx
    Exists: True
```

### Step 2: Verify Templates in Frontend

1. Start your backend server:
   ```bash
   cd backend
   python run.py
   ```

2. Start your frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to the Report Templates page in your app
4. You should now see all registered templates

### Step 3: Generate Reports with Original Formatting

When generating a report:

1. Select a template from the dropdown
2. Provide the data source (Excel file, form data, etc.)
3. Choose export format (PDF, DOCX, HTML)
4. The generated report will maintain **all original template formatting**:
   - Professional styling
   - Headers and footers
   - Tables and formatting
   - Colors and fonts
   - Page layout

## Technical Details

### Template Loading Priority

1. **Database lookup**: First tries to find template by ID in database
2. **Direct path**: Uses `file_path` from database if available
3. **File system search**: Falls back to searching in templates directory
4. **Recursive search**: Searches all subdirectories for matching DOCX files

### Supported Template Locations

- `backend/templates/{template_id}.docx`
- `backend/templates/report_templates/{template_id}.docx`
- `backend/templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx` (default)
- Any DOCX file in `backend/templates/` subdirectories

### Report Generation Flow

```
User selects template
    ↓
Frontend sends: { template_id, data_source, formats: ['pdf', 'docx'] }
    ↓
Backend export service
    ↓
Find template file (database → filesystem)
    ↓
Load template with docxtpl
    ↓
Render with user data
    ↓
Save with ALL original formatting preserved
    ↓
Return download URLs
```

## Benefits

1. ✅ **Original Formatting Preserved**: Reports maintain all professional styling from templates
2. ✅ **Multiple Templates Supported**: Not limited to just one template
3. ✅ **Easy Template Management**: Add new templates by placing DOCX files and running registration script
4. ✅ **Flexible Data Sources**: Works with Excel, forms, or any JSON data
5. ✅ **Multiple Output Formats**: Supports PDF, DOCX, and HTML

## Adding New Templates

To add a new template:

1. **Create your template**: Design in Microsoft Word with placeholders like `{{ variable_name }}`
2. **Save to templates directory**: Place in `backend/templates/` or `backend/templates/report_templates/`
3. **Register the template**: Run `python register_templates.py`
4. **Use in reports**: Template will now appear in frontend dropdown

### Template Placeholder Syntax

Use Jinja2 template syntax in your DOCX files:

```
{{ student_name }}           - Simple variable
{{ students|length }}        - Filter
{% for item in items %}      - Loop
  {{ item.name }}
{% endfor %}
{% if condition %}           - Conditional
  {{ text }}
{% endif %}
```

## Troubleshooting

### Templates not showing in frontend?
- Run `python register_templates.py` to register them
- Check that DOCX files exist in `backend/templates/`
- Verify database connection is working

### Reports still look plain?
- Ensure you're calling the correct endpoint: `/api/reports/export`
- Check that template file exists and path is correct
- Look at backend logs for template loading messages

### Template not rendering?
- Verify placeholder syntax in DOCX file
- Check that data_source contains the required variables
- Look for error messages in backend logs

## Files Modified

1. ✅ `backend/app/routes/templates_api.py` - Removed template filtering
2. ✅ `backend/app/services/export_service.py` - Enhanced to use real templates
3. ✅ `backend/register_templates.py` - New registration script

## Next Steps

1. Run the template registration script
2. Test report generation with different templates
3. Add more custom templates as needed
4. Configure template placeholders to match your data structure

---

**Summary**: The system now properly loads and uses actual DOCX template files with all their original formatting, styling, and design preserved in generated reports. Templates are manageable through a simple registration script and visible in the frontend.
