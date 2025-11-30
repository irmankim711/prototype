"""
AI-Enhanced Excel Generation Service
Uses Claude API to create structured, professional Excel spreadsheets with:
- Intelligent data analysis and formatting
- Dynamic formulas and calculations
- Professional charts and visualizations
- Conditional formatting based on data patterns
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Color
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, IconSetRule
from openpyxl.chart import BarChart, LineChart, PieChart, ScatterChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
import anthropic

logger = logging.getLogger(__name__)


class AIEnhancedExcelService:
    """AI-powered Excel generation service using Claude API"""

    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
            logger.warning("ANTHROPIC_API_KEY not set - AI features will be limited")

        self.reports_dir = Path('reports/excel')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '../config/excel_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading excel_config.json: {e}")
            self.config = {}

    def generate_enhanced_excel(
        self,
        data: List[Dict[str, Any]],
        title: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Generate an AI-enhanced Excel file from data

        Args:
            data: List of dictionaries containing the data
            title: Title for the spreadsheet
            options: Optional configuration (include_charts, include_formulas, etc.)

        Returns:
            Tuple of (file_path, file_size)
        """
        try:
            options = options or {}

            # Analyze data structure using Claude
            logger.info(f"Analyzing data structure for: {title}")
            analysis = self._analyze_data_structure(data, title)

            # Create workbook
            wb = Workbook()
            wb.remove(wb.active)  # Remove default sheet

            # Create main data sheet with AI-enhanced formatting
            self._create_data_sheet(wb, data, title, analysis)

            # Create summary sheet with AI-generated insights
            if options.get('include_summary', True):
                self._create_summary_sheet(wb, data, analysis)

            # Create charts sheet if requested
            if options.get('include_charts', True):
                self._create_charts_sheet(wb, data, analysis)

            # Create pivot analysis if requested
            if options.get('include_pivot', False):
                self._create_pivot_sheet(wb, data, analysis)

            # Generate filename and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self._sanitize_filename(title)}_{timestamp}.xlsx"
            file_path = self.reports_dir / filename

            wb.save(str(file_path))
            file_size = file_path.stat().st_size

            logger.info(f"Excel file generated: {file_path} ({file_size} bytes)")
            return str(file_path), file_size

        except Exception as e:
            logger.error(f"Error generating enhanced Excel: {str(e)}")
            raise

    def _analyze_data_structure(self, data: List[Dict], title: str) -> Dict[str, Any]:
        """Use Claude to analyze data structure and recommend optimal formatting"""
        try:
            # Check if client is available
            if not self.client:
                logger.warning("Claude API client not available - using default analysis")
                return self._get_default_analysis(data)

            # Prepare data sample for analysis
            sample_size = min(10, len(data))
            data_sample = data[:sample_size]

            prompt = f"""Analyze this dataset and provide recommendations for Excel formatting:

Title: {title}
Total Records: {len(data)}
Sample Data: {json.dumps(data_sample, indent=2, default=str)}

Provide a JSON response with:
1. "column_types": Map each column to its type (text, number, date, currency, percentage, etc.)
2. "friendly_headers": Map each original column name to a professional, human-readable header name (e.g., "created_at" -> "Submission Date").
3. "recommended_charts": List of chart types that would best visualize this data (bar, line, pie, scatter, column, area).
4. "key_metrics": List of important metrics to highlight (sum, average, count, min, max).
5. "conditional_formatting": Suggestions for conditional formatting rules.
6. "formulas": Recommended calculated columns or summary formulas.
7. "insights": 3-5 key insights about the data.

Return ONLY valid JSON, no additional text."""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse Claude's response
            response_text = response.content[0].text

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            analysis = json.loads(response_text)
            logger.info(f"Data analysis completed: {len(analysis.get('insights', []))} insights generated")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing data structure: {str(e)}")
            # Return default analysis
            return self._get_default_analysis(data)

    def _get_default_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Return default analysis when AI is not available"""
        if not data:
            return {
                "column_types": {},
                "recommended_charts": [],
                "key_metrics": [],
                "conditional_formatting": [],
                "formulas": [],
                "insights": ["No data available for analysis"]
            }

        # Infer column types from first row
        first_row = data[0]
        column_types = {}

        for key, value in first_row.items():
            if isinstance(value, (int, float)):
                column_types[key] = "number"
            elif isinstance(value, str):
                # Try to detect dates
                type_config = self.config.get('type_detection', {})
                date_indicators = type_config.get('date_indicators', ['date', 'time', 'created', 'updated'])
                currency_indicators = type_config.get('currency_indicators', ['price', 'cost', 'amount', 'revenue', 'salary'])
                
                if any(date_indicator in key.lower() for date_indicator in date_indicators):
                    column_types[key] = "date"
                elif any(curr_indicator in key.lower() for curr_indicator in currency_indicators):
                    column_types[key] = "currency"
                else:
                    column_types[key] = "text"
            else:
                column_types[key] = "text"

        return {
            "column_types": column_types,
            "recommended_charts": ["bar", "line"],
            "key_metrics": ["count", "sum", "average"],
            "conditional_formatting": ["color_scale"],
            "formulas": ["SUM", "AVERAGE", "COUNT"],
            "insights": [
                f"Dataset contains {len(data)} records",
                f"Total of {len(first_row)} columns detected",
                "Using default formatting - set ANTHROPIC_API_KEY for AI-powered insights"
            ]
        }

    def _create_data_sheet(self, wb: Workbook, data: List[Dict], title: str, analysis: Dict):
        """Create main data sheet with AI-enhanced formatting"""
        ws = wb.create_sheet("Data")

        if not data:
            ws.cell(1, 1, "No data available")
            return

        # Add title and metadata
        ws.merge_cells('A1:E1')
        title_cell = ws['A1']
        title_cell.value = title
        title_cell.font = Font(size=16, bold=True, color="1F4E78")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # Add generation info
        ws.cell(2, 1, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ws.cell(2, 1).font = Font(size=10, italic=True, color="7F7F7F")
        ws.cell(3, 1, f"Total Records: {len(data)}")
        ws.cell(3, 1).font = Font(size=10, italic=True, color="7F7F7F")

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)

        # Headers (row 5)
        header_row = 5
        column_types = analysis.get('column_types', {})
        friendly_headers = analysis.get('friendly_headers', {})

        for col_idx, column in enumerate(df.columns, 1):
            # Use friendly header if available, otherwise capitalize original
            header_text = friendly_headers.get(column, str(column).replace('_', ' ').title())
            
            cell = ws.cell(header_row, col_idx, header_text)
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = Border(
                bottom=Side(style='medium', color='000000')
            )

        # Data rows
        for row_idx, (_, row) in enumerate(df.iterrows(), header_row + 1):
            for col_idx, (col_name, value) in enumerate(zip(df.columns, row), 1):
                cell = ws.cell(row_idx, col_idx, value)

                # Apply formatting based on column type
                col_type = column_types.get(col_name, 'text')
                self._apply_cell_formatting(cell, value, col_type)

                # Alternate row colors
                if row_idx % 2 == 0:
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

        # Apply conditional formatting based on AI recommendations
        self._apply_conditional_formatting(ws, df, analysis, header_row)

        # Auto-adjust column widths
        self._auto_adjust_columns(ws, df)

        # Add table formatting
        table_ref = f"A{header_row}:{get_column_letter(len(df.columns))}{header_row + len(df)}"
        table = Table(displayName="DataTable", ref=table_ref)
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )
        table.tableStyleInfo = style
        ws.add_table(table)

        # Freeze header row
        ws.freeze_panes = ws.cell(header_row + 1, 1)

    def _create_summary_sheet(self, wb: Workbook, data: List[Dict], analysis: Dict):
        """Create summary sheet with AI-generated insights and statistics"""
        ws = wb.create_sheet("Summary & Insights")

        # Title
        ws.merge_cells('A1:D1')
        title_cell = ws['A1']
        title_cell.value = "Data Summary & AI Insights"
        title_cell.font = Font(size=14, bold=True, color="1F4E78")
        title_cell.alignment = Alignment(horizontal='center')

        df = pd.DataFrame(data)

        # Key Metrics Section
        row = 3
        ws.cell(row, 1, "KEY METRICS").font = Font(size=12, bold=True, color="2E75B6")
        row += 1

        key_metrics = analysis.get('key_metrics', [])
        for metric in key_metrics:
            ws.cell(row, 1, metric.upper()).font = Font(bold=True)
            # Add formula for metric calculation
            if metric == 'count':
                ws.cell(row, 2, f"=COUNTA(Data!A6:A{len(df)+5})")
            elif metric == 'sum' and len(df.select_dtypes(include=['number']).columns) > 0:
                num_col = df.select_dtypes(include=['number']).columns[0]
                col_idx = df.columns.get_loc(num_col) + 1
                ws.cell(row, 2, f"=SUM(Data!{get_column_letter(col_idx)}6:{get_column_letter(col_idx)}{len(df)+5})")
            elif metric == 'average' and len(df.select_dtypes(include=['number']).columns) > 0:
                num_col = df.select_dtypes(include=['number']).columns[0]
                col_idx = df.columns.get_loc(num_col) + 1
                ws.cell(row, 2, f"=AVERAGE(Data!{get_column_letter(col_idx)}6:{get_column_letter(col_idx)}{len(df)+5})")
            row += 1

        # AI Insights Section
        row += 2
        ws.cell(row, 1, "AI-GENERATED INSIGHTS").font = Font(size=12, bold=True, color="2E75B6")
        row += 1

        insights = analysis.get('insights', [])
        for idx, insight in enumerate(insights, 1):
            ws.cell(row, 1, f"{idx}.")
            ws.cell(row, 2, insight)
            ws.cell(row, 2).alignment = Alignment(wrap_text=True, vertical='top')
            row += 1

        # Column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15

    def _create_charts_sheet(self, wb: Workbook, data: List[Dict], analysis: Dict):
        """Create charts sheet with AI-recommended visualizations"""
        ws = wb.create_sheet("Charts & Visualizations")

        # Title
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = "Data Visualizations"
        title_cell.font = Font(size=14, bold=True, color="1F4E78")
        title_cell.alignment = Alignment(horizontal='center')

        df = pd.DataFrame(data)
        recommended_charts = analysis.get('recommended_charts', [])

        chart_row = 3

        for chart_type in recommended_charts[:self.config.get('generation', {}).get('max_charts', 5)]:
            try:
                if chart_type == 'bar' and len(df.select_dtypes(include=['number']).columns) > 0:
                    self._add_bar_chart(ws, df, chart_row)
                    chart_row += 20
                elif chart_type == 'column' and len(df.select_dtypes(include=['number']).columns) > 0:
                    self._add_column_chart(ws, df, chart_row)
                    chart_row += 20
                elif chart_type == 'line' and len(df.select_dtypes(include=['number']).columns) > 0:
                    self._add_line_chart(ws, df, chart_row)
                    chart_row += 20
                elif chart_type == 'pie':
                    self._add_pie_chart(ws, df, chart_row)
                    chart_row += 20
                elif chart_type == 'scatter' and len(df.select_dtypes(include=['number']).columns) >= 2:
                    self._add_scatter_chart(ws, df, chart_row)
                    chart_row += 20
                elif chart_type == 'area' and len(df.select_dtypes(include=['number']).columns) > 0:
                    self._add_area_chart(ws, df, chart_row)
                    chart_row += 20
            except Exception as e:
                logger.warning(f"Could not create {chart_type} chart: {str(e)}")

    def _add_column_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add a column chart"""
        try:
            chart = BarChart()
            chart.type = "col"
            chart.title = "Data Distribution (Column Chart)"
            chart.style = 10
            chart.height = 10
            chart.width = 20

            num_col = df.select_dtypes(include=['number']).columns[0]
            col_idx = df.columns.get_loc(num_col) + 1

            data = Reference(ws, min_col=col_idx, min_row=5, max_row=min(15, len(df)+5))
            chart.add_data(data, titles_from_data=False)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add column chart: {str(e)}")

    def _add_area_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add an area chart"""
        try:
            from openpyxl.chart import AreaChart
            chart = AreaChart()
            chart.title = "Trend Analysis (Area Chart)"
            chart.style = 13
            chart.height = 10
            chart.width = 20

            num_col = df.select_dtypes(include=['number']).columns[0]
            col_idx = df.columns.get_loc(num_col) + 1

            data = Reference(ws, min_col=col_idx, min_row=5, max_row=min(15, len(df)+5))
            chart.add_data(data, titles_from_data=False)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add area chart: {str(e)}")

    def _add_scatter_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add a scatter chart"""
        try:
            chart = ScatterChart()
            chart.title = "Correlation Analysis (Scatter Chart)"
            chart.style = 13
            chart.height = 10
            chart.width = 20

            num_cols = df.select_dtypes(include=['number']).columns
            if len(num_cols) < 2:
                return

            x_col_idx = df.columns.get_loc(num_cols[0]) + 1
            y_col_idx = df.columns.get_loc(num_cols[1]) + 1

            x_values = Reference(ws, min_col=x_col_idx, min_row=6, max_row=min(15, len(df)+5))
            y_values = Reference(ws, min_col=y_col_idx, min_row=6, max_row=min(15, len(df)+5))
            
            series = openpyxl.chart.Series(y_values, x_values, title_from_data=False)
            chart.series.append(series)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add scatter chart: {str(e)}")

    def _create_pivot_sheet(self, wb: Workbook, data: List[Dict], analysis: Dict):
        """Create pivot analysis sheet"""
        ws = wb.create_sheet("Pivot Analysis")

        ws.cell(1, 1, "Pivot Analysis")
        ws.cell(1, 1).font = Font(size=14, bold=True)

        df = pd.DataFrame(data)

        # Add pivot table data
        # This is a simplified version - full pivot table functionality would require more complex logic
        ws.cell(3, 1, "Note: For interactive pivot tables, use Excel's PivotTable feature on the Data sheet")
        ws.cell(3, 1).alignment = Alignment(wrap_text=True)

    def _apply_cell_formatting(self, cell, value, col_type: str):
        """Apply formatting based on column type"""
        cell.alignment = Alignment(vertical='center', wrap_text=False)

        if col_type == 'number':
            cell.number_format = '#,##0.00'
            cell.alignment = Alignment(horizontal='right', vertical='center')
        elif col_type == 'currency':
            cell.number_format = '$#,##0.00'
            cell.alignment = Alignment(horizontal='right', vertical='center')
        elif col_type == 'percentage':
            cell.number_format = '0.00%'
            cell.alignment = Alignment(horizontal='right', vertical='center')
        elif col_type == 'date':
            cell.number_format = 'yyyy-mm-dd'
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center')

    def _apply_conditional_formatting(self, ws, df: pd.DataFrame, analysis: Dict, header_row: int):
        """Apply AI-recommended conditional formatting"""
        try:
            formatting_rules = analysis.get('conditional_formatting', [])

            # Apply color scales to numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col_name in numeric_cols:
                col_idx = df.columns.get_loc(col_name) + 1
                col_letter = get_column_letter(col_idx)
                range_str = f"{col_letter}{header_row+1}:{col_letter}{header_row+len(df)}"

                # Add color scale rule
                rule = ColorScaleRule(
                    start_type='min', start_color='F8696B',
                    mid_type='percentile', mid_value=50, mid_color='FFEB84',
                    end_type='max', end_color='63BE7B'
                )
                ws.conditional_formatting.add(range_str, rule)
                break  # Only apply to first numeric column for now

        except Exception as e:
            logger.warning(f"Could not apply conditional formatting: {str(e)}")

    def _add_bar_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add a bar chart"""
        try:
            chart = BarChart()
            chart.title = "Data Distribution (Bar Chart)"
            chart.style = 10
            chart.height = 10
            chart.width = 20

            # Use first 10 rows for chart
            num_col = df.select_dtypes(include=['number']).columns[0]
            col_idx = df.columns.get_loc(num_col) + 1

            data = Reference(ws, min_col=col_idx, min_row=5, max_row=min(15, len(df)+5))
            chart.add_data(data, titles_from_data=False)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add bar chart: {str(e)}")

    def _add_line_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add a line chart"""
        try:
            chart = LineChart()
            chart.title = "Trend Analysis (Line Chart)"
            chart.style = 12
            chart.height = 10
            chart.width = 20

            num_col = df.select_dtypes(include=['number']).columns[0]
            col_idx = df.columns.get_loc(num_col) + 1

            data = Reference(ws, min_col=col_idx, min_row=5, max_row=min(15, len(df)+5))
            chart.add_data(data, titles_from_data=False)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add line chart: {str(e)}")

    def _add_pie_chart(self, ws, df: pd.DataFrame, start_row: int):
        """Add a pie chart"""
        try:
            chart = PieChart()
            chart.title = "Distribution (Pie Chart)"
            chart.height = 10
            chart.width = 20

            # Create simple data for pie chart
            ws.cell(start_row, 10, "Category")
            ws.cell(start_row, 11, "Count")

            # Add sample data
            for i, val in enumerate(range(3), start_row + 1):
                ws.cell(i, 10, f"Category {i-start_row}")
                ws.cell(i, 11, val + 1)

            labels = Reference(ws, min_col=10, min_row=start_row+1, max_row=start_row+3)
            data = Reference(ws, min_col=11, min_row=start_row, max_row=start_row+3)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(labels)

            ws.add_chart(chart, f"A{start_row}")
        except Exception as e:
            logger.warning(f"Could not add pie chart: {str(e)}")

    def _auto_adjust_columns(self, ws, df: pd.DataFrame):
        """Auto-adjust column widths based on content"""
        for column in ws.columns:
            max_length = 0
            column_letter = None

            for cell in column:
                try:
                    # Skip merged cells
                    if hasattr(cell, 'column_letter'):
                        if column_letter is None:
                            column_letter = cell.column_letter

                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            # Only adjust if we found a valid column letter
            if column_letter:
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]


# Global instance
ai_excel_service = AIEnhancedExcelService()
