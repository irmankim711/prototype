# How to Generate Reports with Your Template

## ✅ What's Fixed:

1. **Template uses YOUR original design** - blue headers, tables, all your formatting
2. **No extra colors or styling added** by the system
3. **Data can be inserted** using placeholders

## 📝 Template with Placeholders Created:

File: `backend/templates/04- LAPORAN FU _ PUNCAK ALAM_with_placeholders.docx`

**Placeholders added:**
- `{{tarikh}}` - replaces "12 & 13 OKTOBER 2024"
- `{{lokasi}}` - replaces "MASJID TAMAN ALAM JAYA, BANDAR PUNCAK ALAM"
- `{{perunding}}` - replaces "PERUNDING MUBARAK RESOURCES"
- `{{anjuran}}` - replaces "LEMBAGA ZAKAT SELANGOR (MAIS)"

## 🔧 How to Use:

### Example API Request:

```json
POST /api/reports/generate
{
  "title": "Laporan Fiqh Usrah",
  "description": "Report for program",
  "data": {
    "tarikh": "15 & 16 NOVEMBER 2024",
    "lokasi": "MASJID AL-HIDAYAH, SHAH ALAM",
    "perunding": "PERUNDING ISLAM SDN BHD",
    "anjuran": "JABATAN AGAMA ISLAM SELANGOR"
  },
  "config": {
    "template_used": "Temp1"
  }
}
```

### The system will:
1. Find your template: `04- LAPORAN FU _ PUNCAK ALAM_with_placeholders.docx`
2. Replace placeholders with your data:
   - `{{tarikh}}` → "15 & 16 NOVEMBER 2024"
   - `{{lokasi}}` → "MASJID AL-HIDAYAH, SHAH ALAM"
   - etc.
3. Keep ALL your original formatting (blue headers, tables, etc.)
4. Generate the report with your data

## 📌 Important:

- **Blue headers are FROM YOUR TEMPLATE** - that's your design!
- System does NOT add any colors
- System does NOT add any content
- System ONLY fills in the `{{placeholders}}` with your data

## 🎯 To Add More Placeholders:

Tell me which fields in your template should be dynamic (replaceable with data), and I'll add more placeholders!

Current static fields you might want to make dynamic:
- Dates in tables
- Instructor names
- Participant counts
- Session times
- Any other data that changes per report
