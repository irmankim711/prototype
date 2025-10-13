# REPORTS SCHEMA MISMATCH - COMPLETE FIX GUIDE

## Problem Summary
The backend Report models expect different field names than what exists in Supabase:

**Backend Models Expect:**
- `program_id` (INTEGER)  
- `generation_status` (VARCHAR)
- `template_id` (INTEGER)

**Supabase Database Has:**
- `organization_id` (UUID)
- `status` (VARCHAR) 
- `template_id` (UUID)

## Solution A: Update Backend Models (RECOMMENDED)

### Step 1: Create Supabase-Compatible Model

Create `backend/app/models/supabase_report.py`:

```python
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .. import db

class SupabaseReport(db.Model):
    __tablename__ = 'reports'
    __table_args__ = {'extend_existing': True}  # Key fix!
    
    # Match Supabase schema exactly
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(String, nullable=False)
    status = Column(String, default='pending')  # Use 'status' not 'generation_status'
    
    # UUIDs as in Supabase
    organization_id = Column(UUID(as_uuid=True))
    template_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    
    # File info
    file_url = Column(Text)
    file_size = Column(Integer)
    file_format = Column(String)
    
    # Other fields...
    generation_time = Column(Integer)
    error_message = Column(Text)
    parameters = Column(JSON, default=dict)
    data_snapshot = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
```

### Step 2: Update Route Imports

In your route files, replace:
```python
# OLD - causes schema mismatch
from app.models import Report

# NEW - matches Supabase schema  
from app.models.supabase_report import SupabaseReport as Report
```

### Step 3: Update Code Using `generation_status`

Find and replace in your codebase:
```python
# OLD
report.generation_status = "completed"

# NEW  
report.status = "completed"
```

### Step 4: Update Code Using `program_id`

```python
# OLD
report.program_id = some_id

# NEW
report.organization_id = some_uuid  # or use parameters field
```

## Solution B: Add Missing Columns (Alternative)

If you prefer to keep current backend code, add columns to Supabase:

```sql
-- Add missing columns
ALTER TABLE reports ADD COLUMN program_id INTEGER;
ALTER TABLE reports ADD COLUMN generation_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE reports ADD COLUMN generated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE reports ADD COLUMN generation_time_seconds INTEGER;
ALTER TABLE reports ADD COLUMN download_url VARCHAR(500);
ALTER TABLE reports ADD COLUMN last_downloaded TIMESTAMP WITH TIME ZONE;
ALTER TABLE reports ADD COLUMN data_source JSONB;
ALTER TABLE reports ADD COLUMN generation_config JSONB;
ALTER TABLE reports ADD COLUMN completeness_score INTEGER;
ALTER TABLE reports ADD COLUMN processing_notes TEXT;

-- Sync generation_status with status
UPDATE reports SET generation_status = status WHERE status IS NOT NULL;
```

## Quick Test Script

Create `test_report_fix.py`:
```python
from app import create_app, db
from app.models.supabase_report import SupabaseReport as Report

app = create_app()
with app.app_context():
    # Test creating a report
    report = Report(
        title="Test Report",
        report_type="test", 
        status="generated"  # Use 'status' not 'generation_status'
    )
    
    db.session.add(report)
    db.session.commit()
    print(f"✅ Report created: {report.id}")
    
    # Clean up
    db.session.delete(report)
    db.session.commit()
```

## Summary

**RECOMMENDED APPROACH: Solution A**
- ✅ Minimal database changes
- ✅ Follows Supabase conventions  
- ✅ Future-proof
- ✅ Cleaner code

The backend will work immediately after updating imports and field names.

**File Changes Needed:**
1. Create `app/models/supabase_report.py` 
2. Update route imports: `from app.models.supabase_report import SupabaseReport as Report`
3. Replace `generation_status` → `status` in code
4. Replace `program_id` → `organization_id` or use `parameters`

This will resolve the database schema mismatch completely! 🎉
