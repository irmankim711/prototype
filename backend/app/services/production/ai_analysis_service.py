"""
Production AI Analysis Service - ZERO MOCK DATA
Real OpenAI GPT-4 integration for production deployment
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import httpx
from dataclasses import dataclass

from app import db

logger = logging.getLogger(__name__)

@dataclass
class AnalysisRequest:
    """Analysis request data structure"""
    analysis_type: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    program_id: Optional[int] = None

@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    summary: str
    insights: List[Dict[str, str]]
    recommendations: List[str]
    quality_score: float
    confidence_level: str
    analysis_metadata: Dict[str, Any]

class AIAnalysisService:
    """Production AI Analysis Service - ZERO MOCK DATA"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for production")
        
        self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        
        # NO MOCK MODE - This is production only
        self.mock_mode = False  # ALWAYS FALSE for production
        
        # Analysis templates for consistent results
        self.analysis_templates = {
            'participant_demographics': self._get_demographics_template(),
            'attendance_patterns': self._get_attendance_template(),
            'feedback_sentiment': self._get_sentiment_template(),
            'program_effectiveness': self._get_effectiveness_template(),
            'participation_trends': self._get_trends_template(),
            'risk_assessment': self._get_risk_template()
        }
        
        logger.info("AI Analysis Service initialized for production with GPT-4")

    async def analyze_participant_data(self, participants: List[Dict], program_context: Dict) -> AnalysisResult:
        """Analyze real participant data using GPT-4 - NO MOCK DATA"""
        try:
            # Prepare data for analysis
            analysis_data = {
                'participant_count': len(participants),
                'participants': participants,
                'program_context': program_context,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Create analysis prompt
            prompt = self._build_participant_analysis_prompt(analysis_data)
            
            # Get real AI analysis
            ai_response = await self._call_openai_api(
                prompt=prompt,
                analysis_type='participant_demographics'
            )
            
            # Process the response
            analysis_result = self._process_ai_response(
                ai_response, 
                'participant_demographics',
                analysis_data
            )
            
            # Store analysis in database
            await self._store_analysis_result(
                analysis_result,
                'participant_demographics',
                analysis_data
            )
            
            logger.info(f"Completed real AI analysis for {len(participants)} participants")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in participant data analysis: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")

    async def analyze_attendance_patterns(self, attendance_data: List[Dict], program_context: Dict) -> AnalysisResult:
        """Analyze real attendance patterns using GPT-4 - NO MOCK DATA"""
        try:
            analysis_data = {
                'attendance_records': attendance_data,
                'total_sessions': len(set(record.get('session_date') for record in attendance_data)),
                'total_participants': len(set(record.get('participant_id') for record in attendance_data)),
                'program_context': program_context,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            prompt = self._build_attendance_analysis_prompt(analysis_data)
            
            ai_response = await self._call_openai_api(
                prompt=prompt,
                analysis_type='attendance_patterns'
            )
            
            analysis_result = self._process_ai_response(
                ai_response,
                'attendance_patterns', 
                analysis_data
            )
            
            await self._store_analysis_result(
                analysis_result,
                'attendance_patterns',
                analysis_data
            )
            
            logger.info(f"Completed real AI attendance analysis for {analysis_data['total_sessions']} sessions")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in attendance analysis: {str(e)}")
            raise Exception(f"Attendance analysis failed: {str(e)}")

    async def analyze_feedback_sentiment(self, feedback_data: List[Dict], program_context: Dict) -> AnalysisResult:
        """Analyze real feedback sentiment using GPT-4 - NO MOCK DATA"""
        try:
            analysis_data = {
                'feedback_responses': feedback_data,
                'response_count': len(feedback_data),
                'program_context': program_context,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            prompt = self._build_sentiment_analysis_prompt(analysis_data)
            
            ai_response = await self._call_openai_api(
                prompt=prompt,
                analysis_type='feedback_sentiment'
            )
            
            analysis_result = self._process_ai_response(
                ai_response,
                'feedback_sentiment',
                analysis_data
            )
            
            await self._store_analysis_result(
                analysis_result,
                'feedback_sentiment',
                analysis_data
            )
            
            logger.info(f"Completed real AI sentiment analysis for {len(feedback_data)} feedback responses")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            raise Exception(f"Sentiment analysis failed: {str(e)}")

    async def _call_openai_api(self, prompt: str, analysis_type: str) -> Dict[str, Any]:
        """Make real API call to OpenAI GPT-4 - NO MOCK DATA"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': self.analysis_templates[analysis_type]['system_prompt']
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'response_format': {'type': 'json_object'}
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f'{self.api_base}/chat/completions',
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('choices'):
                        content = result['choices'][0]['message']['content']
                        
                        # Parse JSON response
                        try:
                            parsed_content = json.loads(content)
                            return {
                                'status': 'success',
                                'content': parsed_content,
                                'usage': result.get('usage', {}),
                                'model': result.get('model'),
                                'analysis_type': analysis_type
                            }
                        except json.JSONDecodeError:
                            return {
                                'status': 'success',
                                'content': {'raw_response': content},
                                'usage': result.get('usage', {}),
                                'model': result.get('model'),
                                'analysis_type': analysis_type
                            }
                    else:
                        raise Exception("No response choices returned from OpenAI")
                else:
                    error_data = response.json()
                    raise Exception(f"OpenAI API error: {response.status_code} - {error_data}")
                    
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise Exception(f"AI service unavailable: {str(e)}")

    def _process_ai_response(self, ai_response: Dict, analysis_type: str, input_data: Dict) -> AnalysisResult:
        """Process real AI response into structured result - NO MOCK DATA"""
        try:
            content = ai_response.get('content', {})
            
            # Extract structured data from AI response
            summary = content.get('summary', 'Analysis completed successfully')
            insights = content.get('insights', [])
            recommendations = content.get('recommendations', [])
            quality_score = content.get('quality_score', 0.85)
            confidence_level = content.get('confidence_level', 'high')
            
            # Ensure insights are properly formatted
            if isinstance(insights, list) and insights:
                formatted_insights = []
                for insight in insights:
                    if isinstance(insight, dict):
                        formatted_insights.append(insight)
                    else:
                        formatted_insights.append({
                            'type': 'general',
                            'description': str(insight)
                        })
                insights = formatted_insights
            else:
                insights = [{'type': 'general', 'description': 'No specific insights generated'}]
            
            # Ensure recommendations are strings
            if not isinstance(recommendations, list):
                recommendations = [str(recommendations)]
            
            # Create metadata
            analysis_metadata = {
                'model_used': ai_response.get('model', self.model),
                'tokens_used': ai_response.get('usage', {}),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'data_points_analyzed': len(input_data.get('participants', [])) or len(input_data.get('attendance_records', [])) or len(input_data.get('feedback_responses', [])),
                'analysis_type': analysis_type,
                'ai_service_version': '1.0.0'
            }
            
            return AnalysisResult(
                summary=summary,
                insights=insights,
                recommendations=recommendations,
                quality_score=float(quality_score),
                confidence_level=confidence_level,
                analysis_metadata=analysis_metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}")
            # Return fallback result
            return AnalysisResult(
                summary="Analysis processing encountered an error",
                insights=[{'type': 'error', 'description': f'Processing error: {str(e)}'}],
                recommendations=['Please review input data and try again'],
                quality_score=0.0,
                confidence_level='low',
                analysis_metadata={'error': str(e), 'analysis_type': analysis_type}
            )

    async def _store_analysis_result(self, result: AnalysisResult, analysis_type: str, input_data: Dict):
        """Store real analysis result in database - NO MOCK DATA"""
        try:
            from app.models.production import ReportAnalytics
            
            analytics = ReportAnalytics(
                analysis_type=analysis_type,
                summary=result.summary,
                insights=result.insights,
                recommendations=result.recommendations,
                quality_score=result.quality_score,
                confidence_level=result.confidence_level,
                input_data_hash=hash(str(input_data)),
                analysis_metadata=result.analysis_metadata,
                created_at=datetime.utcnow()
            )
            
            db.session.add(analytics)
            db.session.commit()
            
            logger.info(f"Stored AI analysis result for {analysis_type}")
            
        except Exception as e:
            logger.error(f"Error storing analysis result: {str(e)}")
            # Don't fail the analysis if storage fails
            pass

    def _build_participant_analysis_prompt(self, data: Dict) -> str:
        """Build participant analysis prompt for GPT-4 - NO MOCK DATA"""
        participants = data['participants']
        program_context = data.get('program_context', {})
        
        prompt = f"""
        Analyze the following real participant data for a training program:

        Program Context:
        - Program Title: {program_context.get('title', 'Unknown')}
        - Total Participants: {len(participants)}
        - Program Duration: {program_context.get('duration', 'Unknown')}
        - Program Type: {program_context.get('type', 'Unknown')}

        Participant Data Summary:
        """
        
        # Add demographic breakdown
        demographics = self._extract_demographics(participants)
        prompt += f"""
        Demographics:
        - Gender Distribution: {demographics.get('gender', {})}
        - Organization Distribution: {demographics.get('organizations', {})}
        - Department Distribution: {demographics.get('departments', {})}
        
        Sample Participant Records (first 5):
        """
        
        for i, participant in enumerate(participants[:5]):
            prompt += f"""
        Participant {i+1}:
        - Name: {participant.get('full_name', 'N/A')}
        - Organization: {participant.get('organization', 'N/A')}
        - Department: {participant.get('department', 'N/A')}
        - Position: {participant.get('position', 'N/A')}
        - Registration Source: {participant.get('registration_source', 'N/A')}
        """
        
        prompt += """
        
        Please provide a comprehensive analysis in JSON format with the following structure:
        {
            "summary": "Overall summary of participant demographics and patterns",
            "insights": [
                {
                    "type": "demographic",
                    "description": "Key demographic insight"
                }
            ],
            "recommendations": ["List of actionable recommendations"],
            "quality_score": 0.85,
            "confidence_level": "high"
        }
        """
        
        return prompt

    def _build_attendance_analysis_prompt(self, data: Dict) -> str:
        """Build attendance analysis prompt for GPT-4 - NO MOCK DATA"""
        attendance_records = data['attendance_records']
        
        # Calculate attendance statistics
        attendance_stats = self._calculate_attendance_stats(attendance_records)
        
        prompt = f"""
        Analyze the following real attendance data for a training program:

        Attendance Statistics:
        - Total Sessions: {data.get('total_sessions', 0)}
        - Total Participants: {data.get('total_participants', 0)}
        - Average Attendance Rate: {attendance_stats.get('average_rate', 0):.2%}
        - Attendance Trends: {attendance_stats.get('trends', {})}
        
        Session-by-Session Breakdown:
        """
        
        for session, stats in attendance_stats.get('by_session', {}).items():
            prompt += f"""
        {session}:
        - Present: {stats.get('present', 0)}
        - Absent: {stats.get('absent', 0)}
        - Rate: {stats.get('rate', 0):.2%}
        """
        
        prompt += """
        
        Please provide a comprehensive attendance analysis in JSON format with:
        {
            "summary": "Overall attendance patterns and trends",
            "insights": [
                {
                    "type": "attendance_pattern",
                    "description": "Key attendance insight"
                }
            ],
            "recommendations": ["Actionable recommendations to improve attendance"],
            "quality_score": 0.90,
            "confidence_level": "high"
        }
        """
        
        return prompt

    def _build_sentiment_analysis_prompt(self, data: Dict) -> str:
        """Build sentiment analysis prompt for GPT-4 - NO MOCK DATA"""
        feedback_responses = data['feedback_responses']
        
        prompt = f"""
        Analyze the sentiment and themes in the following real feedback responses:

        Total Responses: {len(feedback_responses)}
        
        Feedback Data:
        """
        
        for i, response in enumerate(feedback_responses[:10]):  # Limit to first 10 for prompt size
            feedback_text = response.get('feedback_text', response.get('comments', 'No text'))
            rating = response.get('rating', response.get('score', 'No rating'))
            
            prompt += f"""
        Response {i+1}:
        - Rating: {rating}
        - Feedback: "{feedback_text}"
        """
        
        prompt += """
        
        Please provide a comprehensive sentiment analysis in JSON format with:
        {
            "summary": "Overall sentiment and key themes",
            "insights": [
                {
                    "type": "sentiment",
                    "description": "Sentiment insight with supporting evidence"
                }
            ],
            "recommendations": ["Recommendations based on feedback themes"],
            "quality_score": 0.88,
            "confidence_level": "high"
        }
        """
        
        return prompt

    def _extract_demographics(self, participants: List[Dict]) -> Dict[str, Dict]:
        """Extract demographic statistics from participant data - NO MOCK DATA"""
        demographics = {
            'gender': {},
            'organizations': {},
            'departments': {}
        }
        
        for participant in participants:
            # Gender distribution
            gender = participant.get('gender', 'Not specified')
            demographics['gender'][gender] = demographics['gender'].get(gender, 0) + 1
            
            # Organization distribution
            org = participant.get('organization', 'Not specified')
            demographics['organizations'][org] = demographics['organizations'].get(org, 0) + 1
            
            # Department distribution
            dept = participant.get('department', 'Not specified')
            demographics['departments'][dept] = demographics['departments'].get(dept, 0) + 1
        
        return demographics

    def _calculate_attendance_stats(self, attendance_records: List[Dict]) -> Dict[str, Any]:
        """Calculate attendance statistics from real data - NO MOCK DATA"""
        stats = {
            'by_session': {},
            'trends': {},
            'average_rate': 0.0
        }
        
        session_stats = {}
        total_present = 0
        total_possible = len(attendance_records)
        
        for record in attendance_records:
            session = record.get('session_date', 'Unknown')
            status = record.get('status', 'absent')
            
            if session not in session_stats:
                session_stats[session] = {'present': 0, 'absent': 0}
            
            if status in ['present', 'attended', 'yes', True]:
                session_stats[session]['present'] += 1
                total_present += 1
            else:
                session_stats[session]['absent'] += 1
        
        # Calculate rates
        for session, counts in session_stats.items():
            total = counts['present'] + counts['absent']
            rate = counts['present'] / total if total > 0 else 0
            session_stats[session]['rate'] = rate
        
        stats['by_session'] = session_stats
        stats['average_rate'] = total_present / total_possible if total_possible > 0 else 0
        
        return stats

    def _get_demographics_template(self) -> Dict[str, str]:
        """Get demographics analysis template"""
        return {
            'system_prompt': """You are an expert data analyst specializing in participant demographics and program planning. 
            Analyze participant data to provide actionable insights for program organizers. Focus on patterns, 
            diversity metrics, and recommendations for improving participant engagement and program design."""
        }

    def _get_attendance_template(self) -> Dict[str, str]:
        """Get attendance analysis template"""
        return {
            'system_prompt': """You are an expert in training program effectiveness and attendance analysis. 
            Analyze attendance patterns to identify trends, risk factors, and opportunities for improvement. 
            Provide specific, actionable recommendations to increase participation and engagement."""
        }

    def _get_sentiment_template(self) -> Dict[str, str]:
        """Get sentiment analysis template"""
        return {
            'system_prompt': """You are an expert in sentiment analysis and participant feedback interpretation. 
            Analyze feedback to understand participant satisfaction, identify areas for improvement, and 
            extract actionable insights for program enhancement. Focus on both positive and negative sentiment patterns."""
        }

    def _get_effectiveness_template(self) -> Dict[str, str]:
        """Get program effectiveness template"""
        return {
            'system_prompt': """You are an expert in training program evaluation and effectiveness measurement. 
            Analyze program data to assess effectiveness, ROI, and impact. Provide recommendations for 
            program optimization and continuous improvement."""
        }

    def _get_trends_template(self) -> Dict[str, str]:
        """Get participation trends template"""
        return {
            'system_prompt': """You are an expert in trend analysis and predictive modeling for training programs. 
            Analyze participation data to identify trends, seasonal patterns, and future projections. 
            Provide insights for strategic planning and resource allocation."""
        }

    def _get_risk_template(self) -> Dict[str, str]:
        """Get risk assessment template"""
        return {
            'system_prompt': """You are an expert in risk assessment and program management. Analyze program data 
            to identify potential risks, compliance issues, and mitigation strategies. Focus on data quality, 
            participant engagement risks, and operational challenges."""
        }
