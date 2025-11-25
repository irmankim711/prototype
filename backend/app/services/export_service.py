"""
Unified export service for generating reports in PDF, DOCX, and HTML.
Uses ReportLab for PDF and docxtpl for DOCX template rendering.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from flask import current_app

logger = logging.getLogger(__name__)


try:
    from docxtpl import DocxTemplate  # docxtemplater
    from docx import Document  # used to create a default template if missing
    HAS_DOCXTPL = True
except Exception:
    HAS_DOCXTPL = False

try:
    # We will build a minimal PDF using reportlab directly if available;
    # alternatively, we can delegate to existing report_generator for richer PDFs.
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

try:
    # Optional: leverage existing generator for richer formatting when possible
    from .report_generator import create_pdf_report as legacy_create_pdf
except Exception:
    legacy_create_pdf = None


ALLOWED_FORMATS = {"pdf", "docx", "html"}


@dataclass
class ExportResult:
    status: str
    urls: Dict[str, Optional[str]]
    filenames: Dict[str, Optional[str]]


class ExportService:
    def __init__(self):
        # No cached state to avoid cross-request/test contamination
        self.upload_folder = None

    def _ensure_dirs(self):
        # Always resolve from current app config to honor per-test/per-request upload folders
        base = current_app.config.get("UPLOAD_FOLDER", "uploads")
        upload_folder = os.path.abspath(os.path.join(current_app.root_path, "..", base))
        reports_dir = os.path.join(upload_folder, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return reports_dir

    def _templates_dir(self) -> str:
        return os.path.abspath(os.path.join(current_app.root_path, "..", "templates"))

    def _timestamp_name(self, template_id: str, ext: str) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_tpl = "".join(c for c in (template_id or "template") if c.isalnum() or c in ("-", "_"))
        return f"report_{safe_tpl}_{ts}.{ext}"

    def _build_url(self, filename: str) -> str:
        # Served by /api/reports/download/<filename>
        return f"/api/reports/download/{filename}"

    # ---------------------- Public API ----------------------
    def export(self, template_id: str, data_source: Dict, formats: List[str]) -> ExportResult:
        if not template_id or not isinstance(template_id, str):
            raise ValueError("template_id is required and must be a string")
        if not isinstance(data_source, dict):
            raise ValueError("data_source must be an object")
        if not formats or any(fmt.lower() not in ALLOWED_FORMATS for fmt in formats):
            raise ValueError("formats must be a non-empty list with any of: pdf, docx, html")

        reports_dir = self._ensure_dirs()
        urls: Dict[str, Optional[str]] = {k: None for k in ALLOWED_FORMATS}
        filenames: Dict[str, Optional[str]] = {k: None for k in ALLOWED_FORMATS}

        # Normalize a basic context from data_source
        context = self._build_context(template_id, data_source)

        for fmt in sorted(set(f.lower() for f in formats)):
            try:
                if fmt == "pdf":
                    filenames["pdf"] = self._export_pdf(template_id, context, reports_dir)
                    urls["pdf"] = self._build_url(filenames["pdf"])
                elif fmt == "docx":
                    filenames["docx"] = self._export_docx(template_id, context, reports_dir)
                    urls["docx"] = self._build_url(filenames["docx"])
                elif fmt == "html":
                    filenames["html"] = self._export_html(template_id, context, reports_dir)
                    urls["html"] = self._build_url(filenames["html"])
            except Exception as e:
                logger.error(f"Failed to export {fmt}: {e}")
                raise

        return ExportResult(status="success", urls=urls, filenames=filenames)

    # ---------------------- Helpers ----------------------
    def _build_context(self, template_id: str, data_source: Dict) -> Dict:
        # Basic pass-through; ensure a few known keys for templates
        ctx = dict(data_source or {})
        ctx.setdefault("title", ctx.get("title") or f"Report for {template_id}")
        ctx.setdefault("generated_at", datetime.utcnow().isoformat())
        return ctx

    def _export_pdf(self, template_id: str, context: Dict, reports_dir: str) -> str:
        if HAS_REPORTLAB:
            # If the legacy PDF creator exists, try to use it for richer output
            if legacy_create_pdf is not None:
                filename = self._timestamp_name(template_id, "pdf")
                output_path = os.path.join(reports_dir, filename)
                # The legacy function expects a template id string and data; it will write to path
                try:
                    legacy_create_pdf(template_id, context, output_path)
                    return filename
                except Exception:
                    # Fallback to minimal PDF if legacy fails
                    logger.warning("Falling back to minimal ReportLab PDF")

            # Minimal ReportLab PDF
            filename = self._timestamp_name(template_id, "pdf")
            output_path = os.path.join(reports_dir, filename)
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph(str(context.get("title", "Report")), styles["Title"]))
            story.append(Spacer(1, 0.2 * inch))

            # Dump key-values into a simple table for visibility
            rows = [["Field", "Value"]]
            for k, v in list(context.items())[:20]:
                rows.append([str(k), str(v)])
            table = Table(rows, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            story.append(table)

            doc.build(story)
            return filename

        raise RuntimeError("ReportLab is not available; cannot generate PDF")

    def _export_docx(self, template_id: str, context: Dict, reports_dir: str) -> str:
        """
        Export DOCX by rendering the template with data.
        """
        templates_dir = self._templates_dir()

        # Find template file
        from ..models import TemplateModel as Template
        try:
            template_record = Template.query.filter_by(id=int(template_id), is_active=True).first()
            if template_record and template_record.file_path and os.path.exists(template_record.file_path):
                template_path = template_record.file_path
                logger.info(f"Using database template: {template_path}")
            else:
                template_path = self._find_template_file(templates_dir, template_id)
        except (ValueError, Exception) as e:
            logger.warning(f"Template lookup failed, using file search: {e}")
            template_path = self._find_template_file(templates_dir, template_id)

        if not template_path:
            raise RuntimeError(f"Template file not found for template_id: {template_id}")

        try:
            filename = self._timestamp_name(template_id, "docx")
            output_path = os.path.join(reports_dir, filename)

            if HAS_DOCXTPL:
                # Render template with data
                doc = DocxTemplate(template_path)
                doc.render(context)
                doc.save(output_path)
                logger.info(f"✅ Report generated and rendered: {output_path}")
            else:
                # Fallback if docxtpl is missing (though it should be there)
                import shutil
                shutil.copy2(template_path, output_path)
                logger.warning(f"⚠️ docxtpl not found, copied template without rendering: {output_path}")

            return filename

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise RuntimeError(f"Failed to generate DOCX report: {str(e)}")

    def _find_template_file(self, templates_dir: str, template_id: str) -> Optional[str]:
        """Find template file by searching in templates directory"""
        # Try multiple naming patterns
        candidates = [
            os.path.join(templates_dir, f"{template_id}.docx"),
            os.path.join(templates_dir, "report_templates", f"{template_id}.docx"),
            os.path.join(templates_dir, "04- LAPORAN FU _ PUNCAK ALAM_final.docx"),  # Default template
            os.path.join(templates_dir, "TestTemplate.docx"),
        ]

        # Also search recursively in templates directory
        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file.endswith('.docx') and not file.startswith('~'):
                    full_path = os.path.join(root, file)
                    candidates.append(full_path)

        # Return first existing file
        for candidate in candidates:
            if os.path.exists(candidate):
                logger.info(f"Found template file: {candidate}")
                return candidate

        return None

    def _export_html(self, template_id: str, context: Dict, reports_dir: str) -> str:
        filename = self._timestamp_name(template_id, "html")
        output_path = os.path.join(reports_dir, filename)
        html = f"""
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>{context.get('title','Report')}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; }}
      table {{ border-collapse: collapse; }}
      td, th {{ border: 1px solid #000; padding: 6px 8px; }}
      th {{ font-weight: bold; }}
    </style>
  </head>
  <body>
    <h1>{context.get('title','Report')}</h1>
    <p><strong>Generated at:</strong> {context.get('generated_at')}</p>
    <h2>Data</h2>
    <table>
      <tr><th>Field</th><th>Value</th></tr>
      {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in list(context.items())[:50])}
    </table>
  </body>
  </html>
        """.strip()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return filename


export_service = ExportService()
