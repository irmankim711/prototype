"""
Enhanced Gemini AI Service for Report Content Generation with Variations
Generates multiple content variations for reports based on Excel data
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import google.generativeai as genai
from flask import current_app

logger = logging.getLogger(__name__)

class GeminiContentService:
    def __init__(self):
        """Initialize Gemini Content Service"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model: Optional[Any] = None
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return
        
        try:
            genai.configure(api_key=self.api_key)  # type: ignore
            self.model = genai.GenerativeModel('gemini-2.0-flash')  # type: ignore
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            self.model = None

    def is_available(self) -> bool:
        """Check if Gemini AI service is available"""
        return self.model is not None and self.api_key is not None

    def generate_content_variations(self, data_summary: Dict[str, Any], section_type: str = "executive_summary") -> Dict[str, Any]:
        """
        Generate multiple content variations for a report section
        
        Args:
            data_summary: Summary of Excel data and analysis
            section_type: Type of content to generate (executive_summary, analysis, recommendations, etc.)
            
        Returns:
            Dict containing multiple content variations
        """
        if not self.is_available():
            return self._get_fallback_content(section_type)
        
        try:
            prompt = self._build_content_prompt(data_summary, section_type)
            response = self.model.generate_content(prompt)  # type: ignore
            
            if response and response.text:
                return self._parse_content_variations(response.text, section_type)
            else:
                return self._get_fallback_content(section_type)
                
        except Exception as e:
            logger.error(f"Error generating content variations: {str(e)}")
            return self._get_fallback_content(section_type)

    def generate_report_insights(self, excel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent insights from Excel data
        
        Args:
            excel_data: Parsed Excel data with headers and rows
            
        Returns:
            Dict containing AI-generated insights
        """
        if not self.is_available():
            return self._get_fallback_insights()
        
        try:
            prompt = self._build_insights_prompt(excel_data)
            response = self.model.generate_content(prompt)  # type: ignore
            
            if response and response.text:
                return self._parse_insights_response(response.text)
            else:
                return self._get_fallback_insights()
                
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return self._get_fallback_insights()

    def generate_chart_suggestions(self, excel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate chart suggestions based on Excel data
        
        Args:
            excel_data: Parsed Excel data
            
        Returns:
            List of chart suggestions with configurations
        """
        if not self.is_available():
            return self._get_fallback_charts()
        
        try:
            prompt = self._build_chart_prompt(excel_data)
            response = self.model.generate_content(prompt)  # type: ignore
            
            if response and response.text:
                return self._parse_chart_suggestions(response.text)
            else:
                return self._get_fallback_charts()
                
        except Exception as e:
            logger.error(f"Error generating chart suggestions: {str(e)}")
            return self._get_fallback_charts()

    def optimize_template_content(self, template_content: str, excel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize template content based on Excel data structure
        
        Args:
            template_content: Original template content
            excel_data: Excel data for optimization
            
        Returns:
            Optimized template with AI suggestions
        """
        if not self.is_available():
            return {"success": False, "error": "Gemini AI not available"}
        
        try:
            prompt = self._build_optimization_prompt(template_content, excel_data)
            response = self.model.generate_content(prompt)  # type: ignore
            
            if response and response.text:
                return self._parse_optimization_response(response.text)
            else:
                return {"success": False, "error": "No response from AI"}
                
        except Exception as e:
            logger.error(f"Error optimizing template: {str(e)}")
            return {"success": False, "error": str(e)}

    def _build_content_prompt(self, data_summary: Dict[str, Any], section_type: str) -> str:
        """Build prompt for content generation"""
        base_context = f"""
        You are an expert report writer. Generate professional content variations for a {section_type} section.
        
        Data Summary:
        - Total Records: {data_summary.get('total_records', 0)}
        - Key Metrics: {json.dumps(data_summary.get('key_metrics', {}), indent=2)}
        - Data Categories: {data_summary.get('categories', [])}
        - Time Period: {data_summary.get('time_period', 'Not specified')}
        
        Generate 4 different content variations for the {section_type} section:
        1. Professional/Formal style
        2. Casual/Team-friendly style  
        3. Technical/Analytical style
        4. Results-focused/Action-oriented style
        
        Format your response as JSON:
        {{
            "variations": [
                {{
                    "style": "professional",
                    "title": "Professional Title",
                    "content": "Professional content here...",
                    "tone": "formal"
                }},
                {{
                    "style": "casual", 
                    "title": "Casual Title",
                    "content": "Casual content here...",
                    "tone": "friendly"
                }},
                {{
                    "style": "technical",
                    "title": "Technical Title", 
                    "content": "Technical content here...",
                    "tone": "analytical"
                }},
                {{
                    "style": "results",
                    "title": "Results Title",
                    "content": "Results-focused content here...",
                    "tone": "action-oriented"
                }}
            ]
        }}
        """
        
        return base_context

    def _build_insights_prompt(self, excel_data: Dict[str, Any]) -> str:
        """Build prompt for insights generation"""
        headers = excel_data.get('headers', [])
        sample_data = excel_data.get('sample_rows', [])[:5]  # First 5 rows for context
        
        return f"""
        Analyze this Excel data and generate intelligent insights:
        
        Headers: {headers}
        Sample Data: {json.dumps(sample_data, indent=2)}
        Total Rows: {excel_data.get('total_rows', 0)}
        
        Generate insights in the following categories:
        1. Key Performance Indicators
        2. Trends and Patterns
        3. Notable Achievements
        4. Areas for Improvement
        5. Recommendations
        
        Format as JSON:
        {{
            "insights": {{
                "kpis": ["insight1", "insight2"],
                "trends": ["trend1", "trend2"],
                "achievements": ["achievement1", "achievement2"],
                "improvements": ["improvement1", "improvement2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "summary": "Overall summary of the data analysis"
        }}
        """

    def _build_chart_prompt(self, excel_data: Dict[str, Any]) -> str:
        """Build prompt for chart suggestions"""
        headers = excel_data.get('headers', [])
        data_types = excel_data.get('data_types', {})
        
        return f"""
        Suggest the most effective charts for this data:
        
        Headers: {headers}
        Data Types: {json.dumps(data_types, indent=2)}
        
        Suggest 3-5 different chart types that would best visualize this data.
        
        Format as JSON:
        {{
            "charts": [
                {{
                    "type": "bar",
                    "title": "Chart Title",
                    "x_axis": "header_name",
                    "y_axis": "header_name",
                    "description": "Why this chart is useful",
                    "priority": 1
                }}
            ]
        }}
        """

    def _build_optimization_prompt(self, template_content: str, excel_data: Dict[str, Any]) -> str:
        """Build prompt for template optimization"""
        return f"""
        Optimize this template based on the Excel data structure:
        
        Template Content: {template_content[:1000]}...
        Excel Headers: {excel_data.get('headers', [])}
        
        Provide optimization suggestions:
        1. Field mapping recommendations
        2. Template structure improvements
        3. Content organization suggestions
        
        Format as JSON:
        {{
            "optimized_template": "improved template content",
            "field_mappings": {{"template_field": "excel_header"}},
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """

    def _parse_content_variations(self, response_text: str, section_type: str) -> Dict[str, Any]:
        """Parse AI response for content variations"""
        try:
            # Try to extract JSON from response
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._get_fallback_content(section_type)

    def _parse_insights_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response for insights"""
        try:
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return self._get_fallback_insights()

    def _parse_chart_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse AI response for chart suggestions"""
        try:
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)
                return data.get('charts', [])
        except:
            pass
        
        return self._get_fallback_charts()

    def _parse_optimization_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response for template optimization"""
        try:
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                return {"success": True, "data": json.loads(json_str)}
        except:
            pass
        
        return {"success": False, "error": "Failed to parse AI response"}

    def _get_fallback_content(self, section_type: str) -> Dict[str, Any]:
        """Fallback content when AI is not available"""
        fallback_variations = {
            "executive_summary": [
                {
                    "style": "professional",
                    "title": "Executive Summary",
                    "content": "This report presents a comprehensive analysis of the data provided. Key metrics and performance indicators have been evaluated to provide actionable insights.",
                    "tone": "formal"
                },
                {
                    "style": "casual",
                    "title": "Summary Overview",
                    "content": "Here's what we found in the data! The numbers show some interesting patterns that the team should know about.",
                    "tone": "friendly"
                },
                {
                    "style": "technical",
                    "title": "Data Analysis Summary",
                    "content": "Statistical analysis of the dataset reveals significant patterns across multiple variables with measurable performance indicators.",
                    "tone": "analytical"
                },
                {
                    "style": "results",
                    "title": "Key Results",
                    "content": "Bottom line: The data shows clear opportunities for improvement and areas where we're already excelling.",
                    "tone": "action-oriented"
                }
            ]
        }
        
        return {"variations": fallback_variations.get(section_type, fallback_variations["executive_summary"])}

    def _get_fallback_insights(self) -> Dict[str, Any]:
        """Fallback insights when AI is not available"""
        return {
            "insights": {
                "kpis": ["Data analysis completed successfully", "Multiple data points evaluated"],
                "trends": ["Consistent data patterns observed", "Regular data collection maintained"],
                "achievements": ["Comprehensive dataset compiled", "All required fields captured"],
                "improvements": ["Consider additional data validation", "Explore automation opportunities"],
                "recommendations": ["Regular data review recommended", "Consider expanding data collection"]
            },
            "summary": "Data analysis shows consistent patterns with opportunities for optimization and improvement."
        }

    def _get_fallback_charts(self) -> List[Dict[str, Any]]:
        """Fallback chart suggestions when AI is not available"""
        return [
            {
                "type": "bar",
                "title": "Data Overview",
                "x_axis": "categories",
                "y_axis": "values", 
                "description": "Bar chart showing data distribution",
                "priority": 1
            },
            {
                "type": "line",
                "title": "Trends Over Time",
                "x_axis": "date",
                "y_axis": "values",
                "description": "Line chart showing trends",
                "priority": 2
            }
        ]

# Global instance
gemini_content_service = GeminiContentService()
