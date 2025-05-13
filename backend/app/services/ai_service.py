import openai
import os
import json
from typing import Dict, Any

class AIService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._analyze_with_openai(data)

    def _analyze_with_openai(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

    def generate_report_suggestions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestions for report content based on the data"""
        prompt = f"""
        Given this data: {json.dumps(data)}
        Generate suggestions for:
        1. Key metrics to highlight
        2. Recommended visualizations
        3. Important trends to note
        4. Potential areas of concern
        """
        
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

ai_service = AIService()
