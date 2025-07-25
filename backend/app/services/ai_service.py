import openai
import os
import json
from typing import Dict, Any

class AIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.openai_client = None
            self.enabled = False

    def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            # Return mock data when OpenAI is not available
            return {
                'summary': 'Data analysis completed successfully. (Mock mode - OpenAI not configured)',
                'insights': ['This is a mock analysis result since OpenAI API key is not configured'],
                'suggestions': 'Consider configuring OpenAI API key for real AI analysis.'
            }
        return self._analyze_with_openai(data)

    def _analyze_with_openai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return self.analyze_data(data)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data analysis assistant. Analyze the provided data and generate insights."
                    },
                    {
                        "role": "user",
                        "content": json.dumps(data)
                    }
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Fallback to mock response on error
            return {
                'summary': f'Analysis completed with fallback mode. Error: {str(e)}',
                'insights': ['Mock analysis due to API error'],
                'suggestions': 'Please check API configuration.'
            }

    def generate_report_suggestions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestions for report content based on the data"""
        if not self.enabled:
            return {
                'key_metrics': ['Sample metric 1', 'Sample metric 2'],
                'visualizations': ['Chart suggestion', 'Graph recommendation'],
                'trends': ['Upward trend noted', 'Stable performance'],
                'concerns': ['Mock concern for testing']
            }
        
        prompt = f"""
        Given this data: {json.dumps(data)}
        Generate suggestions for:
        1. Key metrics to highlight
        2. Recommended visualizations
        3. Important trends to note
        4. Potential areas of concern
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a report generation assistant. Provide structured suggestions for report content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                'key_metrics': [f'Error occurred: {str(e)}'],
                'visualizations': ['Fallback visualization'],
                'trends': ['Unable to analyze trends'],
                'concerns': ['API configuration needed']
            }

ai_service = AIService()
