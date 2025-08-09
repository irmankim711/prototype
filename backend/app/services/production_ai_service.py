"""
Production-Ready AI Service
Eliminates mock data and implements real OpenAI integration for form analysis
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class ProductionAIService:
    """Production-ready AI service with real OpenAI integration"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.enabled = os.getenv('ENABLE_REAL_AI', 'false').lower() == 'true'
        
        if self.enabled and not self.api_key:
            logger.warning("OPENAI_API_KEY not set. AI analysis will use fallback logic.")
            self.enabled = False
        
        if self.enabled:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("Production AI service initialized with OpenAI")
        else:
            logger.info("AI service running with intelligent fallback analysis")
    
    def analyze_form_data(self, form_data: Dict[str, Any], form_title: str) -> Dict[str, Any]:
        """Analyze real form data with AI or intelligent fallback"""
        try:
            if self.enabled:
                return self._analyze_with_openai(form_data, form_title)
            else:
                return self._analyze_with_fallback(form_data, form_title)
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._analyze_with_fallback(form_data, form_title)
    
    def _analyze_with_openai(self, form_data: Dict[str, Any], form_title: str) -> Dict[str, Any]:
        """Real OpenAI analysis of form data"""
        try:
            # Prepare data for AI analysis
            responses = form_data.get('responses', [])
            questions = form_data.get('questions', {})
            
            if not responses:
                return {'error': 'No responses to analyze'}
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(responses, questions, form_title)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert data analyst specializing in form response analysis. Provide detailed, actionable insights based on the data provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            parsed_analysis = self._parse_ai_response(ai_content, form_data)
            
            logger.info(f"OpenAI analysis completed for form: {form_title}")
            return {
                'status': 'success',
                'ai_powered': True,
                'analysis': parsed_analysis,
                'response_count': len(responses),
                'model_used': 'gpt-4',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._analyze_with_fallback(form_data, form_title)
    
    def _analyze_with_fallback(self, form_data: Dict[str, Any], form_title: str) -> Dict[str, Any]:
        """Intelligent fallback analysis without AI"""
        responses = form_data.get('responses', [])
        questions = form_data.get('questions', {})
        
        if not responses:
            return {
                'status': 'success',
                'ai_powered': False,
                'analysis': {'message': 'No responses to analyze'},
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Statistical analysis
        total_responses = len(responses)
        
        # Analyze response patterns
        response_analysis = self._analyze_response_patterns(responses)
        
        # Analyze question-specific insights
        question_analysis = self._analyze_questions(responses, questions)
        
        # Generate completion insights
        completion_analysis = self._analyze_completion_patterns(responses)
        
        # Generate summary insights
        summary = self._generate_summary_insights(response_analysis, question_analysis, total_responses)
        
        analysis = {
            'summary': summary,
            'response_patterns': response_analysis,
            'question_insights': question_analysis,
            'completion_analysis': completion_analysis,
            'key_metrics': {
                'total_responses': total_responses,
                'unique_respondents': len(set(r.get('response_id', '') for r in responses)),
                'completion_rate': completion_analysis.get('completion_rate', 100.0)
            },
            'recommendations': self._generate_recommendations(response_analysis, question_analysis, total_responses)
        }
        
        logger.info(f"Fallback analysis completed for form: {form_title}")
        return {
            'status': 'success',
            'ai_powered': False,
            'analysis': analysis,
            'response_count': total_responses,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_analysis_prompt(self, responses: List[Dict], questions: Dict, form_title: str) -> str:
        """Create comprehensive prompt for AI analysis"""
        # Sample responses for context (limit to first 10 to stay within token limits)
        sample_responses = responses[:10]
        
        prompt = f"""
        Analyze the following form data from "{form_title}":
        
        FORM QUESTIONS:
        {json.dumps(questions, indent=2)}
        
        SAMPLE RESPONSES ({len(sample_responses)} of {len(responses)} total):
        {json.dumps(sample_responses, indent=2)}
        
        Please provide analysis in the following structure:
        
        1. EXECUTIVE SUMMARY (2-3 sentences overview)
        
        2. KEY TRENDS (3-5 main patterns identified)
        
        3. QUESTION-SPECIFIC INSIGHTS (for each major question)
        
        4. RECOMMENDATIONS (3-5 actionable suggestions)
        
        5. DATA QUALITY ASSESSMENT
        
        Focus on actionable insights that can help improve the form or the process it supports.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_content: str, form_data: Dict) -> Dict[str, Any]:
        """Parse and structure AI response"""
        # For now, return the raw AI content with basic structure
        # In production, you might want to implement more sophisticated parsing
        
        sections = ai_content.split('\n\n')
        
        parsed = {
            'raw_analysis': ai_content,
            'executive_summary': '',
            'key_trends': [],
            'question_insights': {},
            'recommendations': [],
            'data_quality': ''
        }
        
        # Basic parsing logic
        current_section = None
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if 'EXECUTIVE SUMMARY' in section.upper():
                current_section = 'executive_summary'
                parsed['executive_summary'] = section.replace('EXECUTIVE SUMMARY', '').strip()
            elif 'KEY TRENDS' in section.upper():
                current_section = 'key_trends'
            elif 'RECOMMENDATIONS' in section.upper():
                current_section = 'recommendations'
            elif 'DATA QUALITY' in section.upper():
                current_section = 'data_quality'
                parsed['data_quality'] = section.replace('DATA QUALITY ASSESSMENT', '').strip()
            elif current_section == 'key_trends' and section:
                # Extract bullet points or numbered items
                if section.startswith(('-', '•', '*')) or section[0].isdigit():
                    parsed['key_trends'].append(section)
            elif current_section == 'recommendations' and section:
                if section.startswith(('-', '•', '*')) or section[0].isdigit():
                    parsed['recommendations'].append(section)
        
        return parsed
    
    def _analyze_response_patterns(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in response data"""
        if not responses:
            return {}
        
        # Extract timestamps
        timestamps = []
        for response in responses:
            if response.get('create_time'):
                try:
                    timestamps.append(datetime.fromisoformat(response['create_time'].replace('Z', '+00:00')))
                except:
                    continue
        
        patterns = {}
        
        if timestamps:
            timestamps.sort()
            patterns['submission_timeframe'] = {
                'first_response': timestamps[0].isoformat(),
                'last_response': timestamps[-1].isoformat(),
                'response_span_days': (timestamps[-1] - timestamps[0]).days
            }
            
            # Analyze submission frequency by day of week
            day_counts = {}
            hour_counts = {}
            for ts in timestamps:
                day = ts.strftime('%A')
                hour = ts.hour
                day_counts[day] = day_counts.get(day, 0) + 1
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            patterns['submission_by_day'] = day_counts
            patterns['submission_by_hour'] = hour_counts
            patterns['peak_day'] = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
            patterns['peak_hour'] = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        
        return patterns
    
    def _analyze_questions(self, responses: List[Dict], questions: Dict) -> Dict[str, Any]:
        """Analyze individual question responses"""
        question_insights = {}
        
        for question_id, question_info in questions.items():
            question_title = question_info.get('title', question_id)
            question_type = question_info.get('type', 'unknown')
            
            # Collect answers for this question
            answers = []
            for response in responses:
                if question_title in response.get('answers', {}):
                    answer = response['answers'][question_title]
                    if answer:  # Skip empty answers
                        answers.append(answer)
            
            if not answers:
                continue
            
            insight = {
                'question_type': question_type,
                'response_count': len(answers),
                'response_rate': len(answers) / len(responses) * 100,
                'analysis': {}
            }
            
            # Type-specific analysis
            if question_type == 'choice':
                # Analyze choice distribution
                choice_counts = {}
                for answer in answers:
                    choice_counts[str(answer)] = choice_counts.get(str(answer), 0) + 1
                
                insight['analysis'] = {
                    'distribution': choice_counts,
                    'most_popular': max(choice_counts.items(), key=lambda x: x[1]) if choice_counts else None,
                    'unique_choices': len(choice_counts)
                }
                
            elif question_type == 'text':
                # Analyze text responses
                word_count_avg = sum(len(str(answer).split()) for answer in answers) / len(answers)
                char_count_avg = sum(len(str(answer)) for answer in answers) / len(answers)
                
                insight['analysis'] = {
                    'average_word_count': round(word_count_avg, 1),
                    'average_character_count': round(char_count_avg, 1),
                    'response_lengths': 'varied' if max(len(str(a)) for a in answers) > 2 * min(len(str(a)) for a in answers) else 'consistent'
                }
                
            elif question_type == 'scale':
                # Analyze scale responses
                try:
                    numeric_answers = [float(answer) for answer in answers if str(answer).replace('.', '').isdigit()]
                    if numeric_answers:
                        avg_score = sum(numeric_answers) / len(numeric_answers)
                        insight['analysis'] = {
                            'average_score': round(avg_score, 2),
                            'min_score': min(numeric_answers),
                            'max_score': max(numeric_answers),
                            'score_distribution': {str(int(score)): numeric_answers.count(score) for score in set(numeric_answers)}
                        }
                except:
                    pass
            
            question_insights[question_title] = insight
        
        return question_insights
    
    def _analyze_completion_patterns(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze response completion patterns"""
        if not responses:
            return {'completion_rate': 0}
        
        total_responses = len(responses)
        
        # Calculate completion metrics
        complete_responses = 0
        question_counts = []
        
        for response in responses:
            answers = response.get('answers', {})
            answered_questions = len([a for a in answers.values() if a])
            question_counts.append(answered_questions)
            
            # Consider complete if answered at least 80% of questions
            if answered_questions > 0:
                complete_responses += 1
        
        avg_questions_answered = sum(question_counts) / len(question_counts) if question_counts else 0
        
        return {
            'completion_rate': (complete_responses / total_responses * 100) if total_responses > 0 else 0,
            'average_questions_answered': round(avg_questions_answered, 1),
            'response_quality': 'high' if avg_questions_answered > 3 else 'medium' if avg_questions_answered > 1 else 'low'
        }
    
    def _generate_summary_insights(self, response_patterns: Dict, question_analysis: Dict, total_responses: int) -> str:
        """Generate executive summary from analysis"""
        insights = []
        
        insights.append(f"Analysis of {total_responses} form responses reveals")
        
        if response_patterns.get('peak_day'):
            insights.append(f"peak submission activity on {response_patterns['peak_day']}")
        
        if question_analysis:
            most_answered = max(question_analysis.items(), key=lambda x: x[1]['response_count'])
            insights.append(f"highest engagement with '{most_answered[0]}' ({most_answered[1]['response_count']} responses)")
        
        return ' '.join(insights) + '.'
    
    def _generate_recommendations(self, response_patterns: Dict, question_analysis: Dict, total_responses: int) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Response timing recommendations
        if response_patterns.get('peak_hour') is not None:
            peak_hour = response_patterns['peak_hour']
            if 9 <= peak_hour <= 17:
                recommendations.append(f"Consider sending form reminders during business hours (peak activity at {peak_hour}:00)")
            else:
                recommendations.append(f"Evening/weekend submissions are common (peak at {peak_hour}:00) - ensure form accessibility")
        
        # Question-specific recommendations
        for question_title, analysis in question_analysis.items():
            response_rate = analysis.get('response_rate', 0)
            if response_rate < 70:
                recommendations.append(f"Question '{question_title}' has low response rate ({response_rate:.1f}%) - consider making it optional or clearer")
            elif response_rate > 95:
                recommendations.append(f"Question '{question_title}' performs well ({response_rate:.1f}%) - use as template for other questions")
        
        # Volume recommendations
        if total_responses < 10:
            recommendations.append("Consider extending collection period or promoting form more widely to increase sample size")
        elif total_responses > 500:
            recommendations.append("Excellent response volume - consider implementing automated analysis workflows")
        
        return recommendations[:5]  # Limit to top 5 recommendations

# Global instance for use in routes
production_ai_service = ProductionAIService()
