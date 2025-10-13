"""
Live Preview Report Generator
Generates HTML reports for live preview with AI content variations
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Template, Environment, BaseLoader
import base64
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import io
import pandas as pd
import numpy as np

# Use non-interactive backend for matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

class LivePreviewGenerator:
    def __init__(self):
        """Initialize Live Preview Generator"""
        self.template_dir = os.path.join(os.path.dirname(__file__), '../../templates/report_templates')
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Default templates
        self.default_templates = {
            "professional": self._get_professional_template(),
            "training": self._get_training_template(),
            "analytics": self._get_analytics_template(),
            "executive": self._get_executive_template()
        }
        
        # Chart color schemes
        self.color_schemes = {
            "professional": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"],
            "modern": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
            "corporate": ["#34495E", "#2C3E50", "#8E44AD", "#3498DB"],
            "vibrant": ["#E74C3C", "#F39C12", "#27AE60", "#9B59B6"]
        }
    
    def generate_live_preview(self, excel_data: Dict[str, Any], template_type: str = "professional", 
                            ai_content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate live preview HTML for report
        
        Args:
            excel_data: Parsed Excel data
            template_type: Type of template to use
            ai_content: AI-generated content variations
            
        Returns:
            Dict containing preview HTML and metadata
        """
        try:
            # Get template
            template = self.default_templates.get(template_type, self.default_templates["professional"])
            
            # Prepare data for template
            template_data = self._prepare_template_data(excel_data, ai_content)
            
            # Generate charts if needed
            charts = self._generate_charts(excel_data, template_type)
            template_data['charts'] = charts
            
            # Render template
            jinja_env = Environment(loader=BaseLoader())
            template_obj = jinja_env.from_string(template)
            html_content = template_obj.render(**template_data)
            
            return {
                "success": True,
                "html_content": html_content,
                "template_type": template_type,
                "generated_at": datetime.now().isoformat(),
                "charts_count": len(charts),
                "template_data": template_data
            }
            
        except Exception as e:
            logger.error(f"Error generating live preview: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "html_content": self._get_error_template(str(e))
            }
    
    def generate_content_variations_preview(self, excel_data: Dict[str, Any], 
                                          content_variations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate preview with multiple content variations
        
        Args:
            excel_data: Parsed Excel data
            content_variations: AI-generated content variations
            
        Returns:
            Dict containing multiple preview versions
        """
        try:
            previews = {}
            
            if 'variations' in content_variations:
                for variation in content_variations['variations']:
                    style = variation.get('style', 'professional')
                    preview = self.generate_live_preview(
                        excel_data=excel_data,
                        template_type=style,
                        ai_content=variation
                    )
                    previews[style] = preview
            else:
                # Fallback to single preview
                previews['default'] = self.generate_live_preview(excel_data)
            
            return {
                "success": True,
                "variations": previews,
                "variation_count": len(previews)
            }
            
        except Exception as e:
            logger.error(f"Error generating content variations preview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _prepare_template_data(self, excel_data: Dict[str, Any], ai_content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        try:
            primary_sheet = excel_data.get('primary_sheet', {})
            
            # Basic data
            template_data = {
                "report_title": ai_content.get('title', 'Data Analysis Report') if ai_content else 'Data Analysis Report',
                "report_date": datetime.now().strftime('%B %d, %Y'),
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_records": primary_sheet.get('clean_rows', 0),
                "data_source": os.path.basename(excel_data.get('file_path', 'Unknown')),
                "sheet_name": primary_sheet.get('sheet_name', 'Sheet1')
            }
            
            # AI Content
            if ai_content:
                template_data.update({
                    "executive_summary": ai_content.get('content', ''),
                    "content_style": ai_content.get('style', 'professional'),
                    "content_tone": ai_content.get('tone', 'formal')
                })
            else:
                template_data.update({
                    "executive_summary": "This report provides a comprehensive analysis of the uploaded data.",
                    "content_style": "professional",
                    "content_tone": "formal"
                })
            
            # Data overview
            headers = primary_sheet.get('headers', [])
            sample_data = primary_sheet.get('sample_data', [])
            
            template_data.update({
                "headers": headers,
                "sample_data": sample_data[:10],  # Limit to 10 rows for preview
                "total_columns": len(headers),
                "data_types": primary_sheet.get('data_types', {}),
                "field_categories": primary_sheet.get('field_categories', {})
            })
            
            # Statistics
            statistics = primary_sheet.get('statistics', {})
            template_data['statistics'] = statistics
            
            # Quality assessment
            quality = primary_sheet.get('quality_assessment', {})
            if quality:
                completeness = quality.get('completeness', {})
                template_data.update({
                    "data_completeness": completeness.get('completeness_percentage', 100),
                    "missing_data_count": completeness.get('missing_cells', 0),
                    "duplicate_rows": quality.get('uniqueness', {}).get('duplicate_rows', 0)
                })
            
            # Key insights
            template_data['key_insights'] = self._generate_key_insights(primary_sheet)
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error preparing template data: {str(e)}")
            return {"error": str(e)}
    
    def _generate_key_insights(self, sheet_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from data"""
        insights = []
        
        try:
            total_rows = sheet_data.get('clean_rows', 0)
            headers = sheet_data.get('headers', [])
            statistics = sheet_data.get('statistics', {})
            field_categories = sheet_data.get('field_categories', {})
            
            # Basic insights
            insights.append(f"Dataset contains {total_rows:,} records across {len(headers)} fields")
            
            # Performance metrics insights
            performance_fields = [k for k, v in field_categories.items() if v == 'performance_metric']
            if performance_fields:
                insights.append(f"Performance data available for {len(performance_fields)} metrics: {', '.join(performance_fields[:3])}")
            
            # Numeric statistics insights
            numeric_stats = statistics.get('numeric', {})
            if numeric_stats:
                for field, stats in list(numeric_stats.items())[:2]:  # First 2 numeric fields
                    mean_val = stats.get('mean', 0)
                    insights.append(f"Average {field}: {mean_val:.2f}")
            
            # Data quality insights
            quality = sheet_data.get('quality_assessment', {})
            if quality:
                completeness = quality.get('completeness', {}).get('completeness_percentage', 100)
                if completeness >= 95:
                    insights.append("Excellent data quality with minimal missing values")
                elif completeness >= 80:
                    insights.append("Good data quality with some missing values")
                else:
                    insights.append("Data quality needs attention due to missing values")
            
            # Unique insights based on field types
            personal_info = [k for k, v in field_categories.items() if v == 'personal_info']
            if personal_info:
                insights.append(f"Personal information captured for participant tracking")
            
            contact_info = [k for k, v in field_categories.items() if v == 'contact_info']
            if contact_info:
                insights.append(f"Contact information available for follow-up communications")
            
        except Exception as e:
            logger.warning(f"Error generating insights: {str(e)}")
            insights.append("Data analysis completed successfully")
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_charts(self, excel_data: Dict[str, Any], template_type: str = "professional") -> List[Dict[str, Any]]:
        """Generate charts for the report"""
        charts = []
        
        try:
            primary_sheet = excel_data.get('primary_sheet', {})
            sample_data = primary_sheet.get('sample_data', [])
            
            if not sample_data:
                return charts
            
            # Convert sample data to DataFrame
            df = pd.DataFrame(sample_data)
            
            # Color scheme
            colors = self.color_schemes.get(template_type, self.color_schemes["professional"])
            
            # Generate different types of charts
            
            # 1. Numeric data overview (bar chart)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                chart_data = self._create_bar_chart(df, numeric_cols[:4], colors, "Numeric Data Overview")
                if chart_data:
                    charts.append(chart_data)
            
            # 2. Distribution chart for first numeric column
            if numeric_cols:
                first_numeric = numeric_cols[0]
                chart_data = self._create_histogram(df, first_numeric, colors[0], f"Distribution of {first_numeric}")
                if chart_data:
                    charts.append(chart_data)
            
            # 3. Category distribution (pie chart)
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                first_text = text_cols[0]
                value_counts = df[first_text].value_counts().head(5)
                if len(value_counts) > 1:
                    chart_data = self._create_pie_chart(value_counts, colors, f"Distribution of {first_text}")
                    if chart_data:
                        charts.append(chart_data)
            
            # 4. Trend analysis if there are enough numeric columns
            if len(numeric_cols) >= 2:
                chart_data = self._create_line_chart(df, numeric_cols[:2], colors, "Trend Analysis")
                if chart_data:
                    charts.append(chart_data)
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
        
        return charts
    
    def _create_bar_chart(self, df: pd.DataFrame, columns: List[str], colors: List[str], title: str) -> Optional[Dict[str, Any]]:
        """Create bar chart"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Calculate means for each column
            means = [df[col].mean() for col in columns if df[col].notna().any()]
            column_names = [col for col in columns if df[col].notna().any()]
            
            if not means:
                return None
            
            bars = plt.bar(column_names, means, color=colors[:len(means)])
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel('Metrics', fontsize=12)
            plt.ylabel('Average Values', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, mean in zip(bars, means):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(means)*0.01,
                        f'{mean:.1f}', ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()
            
            return {
                "type": "bar",
                "title": title,
                "image": f"data:image/png;base64,{img_base64}",
                "description": f"Bar chart showing average values for {', '.join(column_names)}"
            }
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {str(e)}")
            plt.close()
            return None
    
    def _create_histogram(self, df: pd.DataFrame, column: str, color: str, title: str) -> Optional[Dict[str, Any]]:
        """Create histogram"""
        try:
            plt.figure(figsize=(8, 5))
            
            data = df[column].dropna()
            if len(data) == 0:
                return None
            
            plt.hist(data, bins=20, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel(column, fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            
            # Add statistics text
            mean_val = data.mean()
            std_val = data.std()
            plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
            plt.legend()
            
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()
            
            return {
                "type": "histogram",
                "title": title,
                "image": f"data:image/png;base64,{img_base64}",
                "description": f"Distribution histogram for {column} (Mean: {mean_val:.2f}, Std: {std_val:.2f})"
            }
            
        except Exception as e:
            logger.error(f"Error creating histogram: {str(e)}")
            plt.close()
            return None
    
    def _create_pie_chart(self, value_counts: pd.Series, colors: List[str], title: str) -> Optional[Dict[str, Any]]:
        """Create pie chart"""
        try:
            plt.figure(figsize=(8, 6))
            
            # Create pie chart
            wedges, texts, autotexts = plt.pie(value_counts.values, labels=value_counts.index, 
                                             autopct='%1.1f%%', colors=colors[:len(value_counts)],
                                             startangle=90)
            
            plt.title(title, fontsize=14, fontweight='bold')
            
            # Improve text readability
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            plt.axis('equal')
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()
            
            return {
                "type": "pie",
                "title": title,
                "image": f"data:image/png;base64,{img_base64}",
                "description": f"Pie chart showing distribution of categories"
            }
            
        except Exception as e:
            logger.error(f"Error creating pie chart: {str(e)}")
            plt.close()
            return None
    
    def _create_line_chart(self, df: pd.DataFrame, columns: List[str], colors: List[str], title: str) -> Optional[Dict[str, Any]]:
        """Create line chart"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Use index as x-axis
            x_values = range(len(df))
            
            for i, col in enumerate(columns):
                data = df[col].dropna()
                if len(data) > 1:
                    plt.plot(data.index, data.values, marker='o', color=colors[i % len(colors)], 
                            label=col, linewidth=2, markersize=4)
            
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel('Record Index', fontsize=12)
            plt.ylabel('Values', fontsize=12)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()
            
            return {
                "type": "line",
                "title": title,
                "image": f"data:image/png;base64,{img_base64}",
                "description": f"Line chart showing trends for {', '.join(columns)}"
            }
            
        except Exception as e:
            logger.error(f"Error creating line chart: {str(e)}")
            plt.close()
            return None
    
    def _get_professional_template(self) -> str:
        """Get professional template HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #2E86AB, #A23B72); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 2.5rem; font-weight: 300; }
        .header p { margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9; }
        .content { padding: 30px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #2E86AB; border-bottom: 2px solid #2E86AB; padding-bottom: 5px; margin-bottom: 15px; }
        .data-overview { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #2E86AB; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #2E86AB; }
        .stat-label { font-size: 0.9rem; color: #666; margin-top: 5px; }
        .table-container { overflow-x: auto; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .data-table th, .data-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        .data-table th { background: #f8f9fa; font-weight: 600; color: #2E86AB; }
        .data-table tr:hover { background: #f8f9fa; }
        .insight-list { list-style: none; padding: 0; }
        .insight-list li { padding: 10px 0; border-left: 3px solid #2E86AB; padding-left: 15px; margin-bottom: 10px; background: #f8f9fa; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .executive-summary { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #A23B72; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <p>Generated on {{ report_date }} | Data Source: {{ data_source }}</p>
        </div>
        
        <div class="content">
            <!-- Executive Summary -->
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="executive-summary">
                    {{ executive_summary }}
                </div>
            </div>
            
            <!-- Data Overview -->
            <div class="section">
                <h2>Data Overview</h2>
                <div class="data-overview">
                    <div class="stat-card">
                        <div class="stat-number">{{ total_records }}</div>
                        <div class="stat-label">Total Records</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ total_columns }}</div>
                        <div class="stat-label">Data Fields</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ data_completeness|round(1) }}%</div>
                        <div class="stat-label">Data Completeness</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ duplicate_rows }}</div>
                        <div class="stat-label">Duplicate Records</div>
                    </div>
                </div>
            </div>
            
            <!-- Key Insights -->
            <div class="section">
                <h2>Key Insights</h2>
                <ul class="insight-list">
                    {% for insight in key_insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <!-- Charts -->
            {% if charts %}
            <div class="section">
                <h2>Data Visualizations</h2>
                {% for chart in charts %}
                <div class="chart-container">
                    <h3>{{ chart.title }}</h3>
                    <img src="{{ chart.image }}" alt="{{ chart.description }}">
                    <p style="color: #666; font-size: 0.9rem; margin-top: 10px;">{{ chart.description }}</p>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Sample Data -->
            <div class="section">
                <h2>Sample Data (First 10 Records)</h2>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                {% for header in headers %}
                                <th>{{ header }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in sample_data %}
                            <tr>
                                {% for header in headers %}
                                <td>{{ row[header] if row[header] is not none else '-' }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_training_template(self) -> str:
        """Get training-focused template"""
        return self._get_professional_template().replace(
            "linear-gradient(135deg, #2E86AB, #A23B72)",
            "linear-gradient(135deg, #27AE60, #2980B9)"
        ).replace("#2E86AB", "#27AE60").replace("#A23B72", "#2980B9")
    
    def _get_analytics_template(self) -> str:
        """Get analytics-focused template"""
        return self._get_professional_template().replace(
            "linear-gradient(135deg, #2E86AB, #A23B72)",
            "linear-gradient(135deg, #8E44AD, #3498DB)"
        ).replace("#2E86AB", "#8E44AD").replace("#A23B72", "#3498DB")
    
    def _get_executive_template(self) -> str:
        """Get executive summary template"""
        return self._get_professional_template().replace(
            "linear-gradient(135deg, #2E86AB, #A23B72)",
            "linear-gradient(135deg, #34495E, #2C3E50)"
        ).replace("#2E86AB", "#34495E").replace("#A23B72", "#2C3E50")
    
    def _get_error_template(self, error_message: str) -> str:
        """Get error template"""
        return f"""
        <div style="padding: 20px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; color: #721c24;">
            <h3>Preview Generation Error</h3>
            <p>Unable to generate preview: {error_message}</p>
            <p>Please check your data and try again.</p>
        </div>
        """

# Global instance
live_preview_generator = LivePreviewGenerator()
