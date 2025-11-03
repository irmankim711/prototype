"""
AI-Powered Report Generation Service using Claude AI
Provides intelligent report generation with:
- Data analysis and insights extraction
- Structured report content generation
- Executive summaries and recommendations
- Chart and visualization suggestions
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd
import anthropic

logger = logging.getLogger(__name__)


class AIReportService:
    """AI-powered report generation service using Claude API"""

    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.ai_enabled = True
            logger.info("Claude AI Report Service initialized successfully")
        else:
            self.client = None
            self.ai_enabled = False
            logger.warning("ANTHROPIC_API_KEY not set - AI report features will be disabled")

    def generate_report_content(
        self,
        data: List[Dict[str, Any]],
        report_title: str,
        report_type: str = "analysis",
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent report content using Claude AI

        Args:
            data: List of dictionaries containing the data to analyze
            report_title: Title for the report
            report_type: Type of report (analysis, summary, detailed, executive)
            additional_context: Additional context or instructions for the AI

        Returns:
            Dictionary containing generated report sections
        """
        if not self.ai_enabled:
            return self._generate_fallback_report(data, report_title)

        try:
            logger.info(f"Generating AI report for: {report_title}")

            # Convert data to DataFrame for analysis
            df = pd.DataFrame(data)
            data_summary = self._get_data_summary(df)

            # Create the prompt for Claude
            prompt = self._create_report_prompt(
                df,
                data_summary,
                report_title,
                report_type,
                additional_context
            )

            # Call Claude API
            logger.info("Calling Claude API for report generation...")
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse the response
            response_text = message.content[0].text
            report_content = self._parse_report_response(response_text)

            logger.info("AI report generation completed successfully")
            return {
                'success': True,
                'content': report_content,
                'ai_generated': True,
                'model': 'claude-sonnet-4',
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating AI report: {str(e)}")
            return self._generate_fallback_report(data, report_title)

    def generate_executive_summary(
        self,
        data: List[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an executive summary using Claude AI

        Args:
            data: List of dictionaries containing the data
            analysis: Optional pre-computed analysis results

        Returns:
            Executive summary text
        """
        if not self.ai_enabled:
            return self._generate_basic_summary(data)

        try:
            df = pd.DataFrame(data)
            data_summary = self._get_data_summary(df)

            prompt = f"""Generate a concise executive summary for the following data analysis:

Data Overview:
- Total Records: {len(df)}
- Columns: {', '.join(df.columns.tolist())}
- Date Range: {data_summary.get('date_range', 'N/A')}

Key Statistics:
{json.dumps(data_summary, indent=2)}

Please provide a 3-4 paragraph executive summary that:
1. Highlights the most important findings
2. Identifies key trends or patterns
3. Provides actionable recommendations
4. Uses clear, professional language suitable for stakeholders

Format the response as a single cohesive summary without section headers."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return self._generate_basic_summary(data)

    def analyze_data_insights(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract insights from data using Claude AI

        Args:
            data: List of dictionaries containing the data

        Returns:
            Dictionary containing insights, trends, and recommendations
        """
        if not self.ai_enabled:
            return self._generate_basic_insights(data)

        try:
            df = pd.DataFrame(data)
            data_summary = self._get_data_summary(df)

            prompt = f"""Analyze the following dataset and provide key insights:

Dataset Overview:
- Total Records: {len(df)}
- Columns: {', '.join(df.columns.tolist())}

Statistical Summary:
{json.dumps(data_summary, indent=2)}

Sample Data (first 5 rows):
{df.head().to_dict('records')}

Please provide:
1. Key trends or patterns
2. Notable anomalies or outliers
3. Data quality observations
4. Actionable recommendations

Return the analysis in JSON format with these exact keys:
{{
    "key_trends": ["trend1", "trend2", ...],
    "anomalies": ["anomaly1", "anomaly2", ...],
    "data_quality": ["observation1", "observation2", ...],
    "recommendations": ["recommendation1", "recommendation2", ...]
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            response_text = message.content[0].text
            # Extract JSON from potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            insights = json.loads(response_text.strip())
            return insights

        except Exception as e:
            logger.error(f"Error analyzing data insights: {str(e)}")
            return self._generate_basic_insights(data)

    def suggest_visualizations(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Suggest appropriate visualizations for the data using Claude AI

        Args:
            data: List of dictionaries containing the data

        Returns:
            List of visualization suggestions with types and configurations
        """
        if not self.ai_enabled:
            return self._generate_basic_viz_suggestions(data)

        try:
            df = pd.DataFrame(data)
            data_summary = self._get_data_summary(df)

            prompt = f"""Analyze this dataset and suggest the most appropriate visualizations:

Dataset:
- Total Records: {len(df)}
- Columns: {', '.join(df.columns.tolist())}
- Column Types: {df.dtypes.to_dict()}

Data Summary:
{json.dumps(data_summary, indent=2)}

Please suggest 3-5 visualizations that would best represent this data.
Return suggestions in JSON format:
{{
    "visualizations": [
        {{
            "type": "bar|line|pie|scatter|heatmap",
            "title": "Chart Title",
            "x_axis": "column_name",
            "y_axis": "column_name",
            "description": "Why this visualization is useful",
            "priority": 1-5
        }}
    ]
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1536,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            result = json.loads(response_text.strip())
            return result.get('visualizations', [])

        except Exception as e:
            logger.error(f"Error suggesting visualizations: {str(e)}")
            return self._generate_basic_viz_suggestions(data)

    def _get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate basic statistical summary of the data"""
        summary = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }

        # Add numeric column statistics
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            summary['numeric_stats'] = df[numeric_cols].describe().to_dict()

        # Add date range if date columns exist
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            for col in date_cols:
                summary['date_range'] = f"{df[col].min()} to {df[col].max()}"
                break

        # Add categorical column info
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            summary['categorical_info'] = {}
            for col in categorical_cols[:5]:  # Limit to first 5
                summary['categorical_info'][col] = {
                    'unique_count': df[col].nunique(),
                    'top_values': df[col].value_counts().head(3).to_dict()
                }

        return summary

    def _create_report_prompt(
        self,
        df: pd.DataFrame,
        data_summary: Dict[str, Any],
        report_title: str,
        report_type: str,
        additional_context: Optional[str]
    ) -> str:
        """Create the prompt for Claude to generate the report"""

        report_type_instructions = {
            'analysis': 'Provide detailed analysis with insights, trends, and patterns',
            'summary': 'Provide a concise summary of key findings',
            'detailed': 'Provide comprehensive detailed analysis with all relevant metrics',
            'executive': 'Provide executive-level summary focused on strategic insights'
        }

        instruction = report_type_instructions.get(report_type, report_type_instructions['analysis'])

        prompt = f"""Generate a professional {report_type} report for: {report_title}

Dataset Overview:
- Total Records: {len(df)}
- Columns: {', '.join(df.columns.tolist())}

Statistical Summary:
{json.dumps(data_summary, indent=2)}

Sample Data (first 10 rows):
{df.head(10).to_dict('records')}

Instructions:
{instruction}

{f'Additional Context: {additional_context}' if additional_context else ''}

Please structure the report with the following sections:
1. Executive Summary
2. Data Overview
3. Key Findings
4. Detailed Analysis
5. Trends and Patterns
6. Recommendations
7. Conclusion

Format the response as structured markdown with clear section headers."""

        return prompt

    def _parse_report_response(self, response_text: str) -> Dict[str, str]:
        """Parse Claude's response into structured sections"""
        sections = {
            'executive_summary': '',
            'data_overview': '',
            'key_findings': '',
            'detailed_analysis': '',
            'trends_patterns': '',
            'recommendations': '',
            'conclusion': ''
        }

        # Split by markdown headers
        current_section = None
        lines = response_text.split('\n')

        section_map = {
            'executive summary': 'executive_summary',
            'data overview': 'data_overview',
            'key findings': 'key_findings',
            'detailed analysis': 'detailed_analysis',
            'trends and patterns': 'trends_patterns',
            'recommendations': 'recommendations',
            'conclusion': 'conclusion'
        }

        for line in lines:
            # Check if line is a header
            if line.startswith('##'):
                header = line.replace('#', '').strip().lower()
                current_section = section_map.get(header)
            elif current_section:
                sections[current_section] += line + '\n'

        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()

        return sections

    def _generate_fallback_report(
        self,
        data: List[Dict[str, Any]],
        report_title: str
    ) -> Dict[str, Any]:
        """Generate basic report without AI"""
        df = pd.DataFrame(data)

        content = {
            'executive_summary': f'Basic analysis of {report_title} with {len(df)} records.',
            'data_overview': f'Dataset contains {len(df.columns)} columns: {", ".join(df.columns.tolist())}',
            'key_findings': 'AI analysis unavailable. Manual review recommended.',
            'detailed_analysis': df.describe().to_string() if len(df) > 0 else 'No data available',
            'trends_patterns': 'Trend analysis requires AI service.',
            'recommendations': 'Enable Claude AI for automated recommendations.',
            'conclusion': 'Report generated without AI assistance.'
        }

        return {
            'success': True,
            'content': content,
            'ai_generated': False,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _generate_basic_summary(self, data: List[Dict[str, Any]]) -> str:
        """Generate basic summary without AI"""
        df = pd.DataFrame(data)
        return f"Dataset contains {len(df)} records with {len(df.columns)} columns. AI analysis unavailable."

    def _generate_basic_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic insights without AI"""
        return {
            'key_trends': ['AI analysis unavailable'],
            'anomalies': [],
            'data_quality': ['Manual review recommended'],
            'recommendations': ['Enable Claude AI for detailed insights']
        }

    def _generate_basic_viz_suggestions(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate basic visualization suggestions without AI"""
        df = pd.DataFrame(data)
        suggestions = []

        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(numeric_cols) > 0:
            suggestions.append({
                'type': 'bar',
                'title': f'Distribution of {numeric_cols[0]}',
                'x_axis': df.columns[0],
                'y_axis': numeric_cols[0],
                'description': 'Basic bar chart visualization',
                'priority': 3
            })

        return suggestions
