"""
Template Report Service
Generates reports by copying the original template and replacing specific text fields
Preserves 100% of the original template formatting
"""
import os
import logging
import shutil
from datetime import datetime
from typing import Dict, Optional
from docx import Document
from flask import current_app

logger = logging.getLogger(__name__)


class TemplateReportService:
    """Service for generating reports that preserve exact template formatting"""

    def generate_report(
        self,
        template_id: str,
        data: Dict,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate a report by copying the template and optionally replacing text

        Args:
            template_id: ID or name of template
            data: Dictionary of data to populate (optional)
            output_filename: Name for output file (optional)

        Returns:
            Path to generated report file
        """
        try:
            # Find template file
            template_path = self._find_template(template_id)
            if not template_path:
                raise ValueError(f"Template not found: {template_id}")

            # Create output directory
            output_dir = self._get_output_dir()

            # Generate output filename
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"report_{template_id}_{timestamp}.docx"

            output_path = os.path.join(output_dir, output_filename)

            # If no data provided, just copy the template as-is
            if not data or not data.items():
                logger.info("No data provided - copying template as-is")
                shutil.copy2(template_path, output_path)
                logger.info(f"Report generated (template copy): {output_path}")
                return output_path

            # Load template and replace specified fields only
            doc = Document(template_path)

            # Replace text in paragraphs
            replacements_made = 0
            for paragraph in doc.paragraphs:
                for key, value in data.items():
                    if str(key) in paragraph.text:
                        paragraph.text = paragraph.text.replace(str(key), str(value))
                        replacements_made += 1

            # Replace text in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in data.items():
                            if str(key) in cell.text:
                                cell.text = cell.text.replace(str(key), str(value))
                                replacements_made += 1

            # Save the document
            doc.save(output_path)

            logger.info(f"Report generated with {replacements_made} replacements: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _find_template(self, template_id: str) -> Optional[str]:
        """Find template file by ID or name"""
        templates_dir = os.path.join(current_app.root_path, '..', 'templates')

        # Try different paths
        candidates = [
            os.path.join(templates_dir, f"{template_id}.docx"),
            os.path.join(templates_dir, "04- LAPORAN FU _ PUNCAK ALAM_final.docx"),
            os.path.join(templates_dir, "report_templates", f"{template_id}.docx"),
        ]

        # Also search recursively
        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file.endswith('.docx') and not file.startswith('~'):
                    candidates.append(os.path.join(root, file))

        # Return first existing file
        for path in candidates:
            if os.path.exists(path):
                logger.info(f"Found template: {path}")
                return path

        return None

    def _get_output_dir(self) -> str:
        """Get output directory for generated reports"""
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        output_dir = os.path.join(current_app.root_path, '..', upload_folder, 'reports')
        os.makedirs(output_dir, exist_ok=True)
        return os.path.abspath(output_dir)


# Singleton instance
template_report_service = TemplateReportService()
