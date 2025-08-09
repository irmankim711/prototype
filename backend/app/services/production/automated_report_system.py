"""
Production Automated Report System - ZERO MOCK DATA
Complete integration of all production services
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

from app import db

# Import all production services
from .google_forms_service import GoogleFormsService
from .microsoft_graph_service import MicrosoftGraphService
from .ai_analysis_service import AIAnalysisService, AnalysisRequest, AnalysisResult
from .template_converter_service import TemplateConverterService

logger = logging.getLogger(__name__)

class ProductionAutomatedReportSystem:
    """Production Automated Report System - ZERO MOCK DATA"""
    
    def __init__(self):
        # Initialize all production services
        self.google_service = GoogleFormsService()
        self.microsoft_service = MicrosoftGraphService()
        self.ai_service = AIAnalysisService()
        self.template_service = TemplateConverterService()
        
        # NO MOCK MODE - This is production only
        self.mock_mode = False  # ALWAYS FALSE for production
        
        # Report generation settings
        self.default_template = os.getenv('DEFAULT_TEMPLATE_PATH', './templates/Temp1.docx')
        self.max_concurrent_reports = int(os.getenv('MAX_CONCURRENT_REPORTS', '5'))
        
        logger.info("Production Automated Report System initialized with ZERO mock data")

    async def generate_complete_report(self, program_id: int, user_id: str, report_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate complete production report with real data - NO MOCK DATA"""
        try:
            start_time = datetime.utcnow()
            
            # Import models
            from app.models.production import Program, Participant, FormIntegration, Report
            
            # Get program data
            program = Program.query.get(program_id)
            if not program:
                raise ValueError(f"Program with ID {program_id} not found")
            
            # Get all participants
            participants = Participant.query.filter_by(program_id=program_id).all()
            
            logger.info(f"Starting complete report generation for program '{program.title}' with {len(participants)} participants")
            
            # Step 1: Sync all external form data
            sync_results = await self._sync_all_external_data(program_id, user_id)
            
            # Step 2: Refresh participant data after sync
            participants = Participant.query.filter_by(program_id=program_id).all()
            
            # Step 3: Prepare data for analysis and reporting
            report_data = await self._prepare_report_data(program, participants)
            
            # Step 4: Generate AI analysis
            ai_analysis = await self._generate_ai_analysis(program, participants, report_data)
            
            # Step 5: Generate final report document
            template_path = report_config.get('template_path', self.default_template) if report_config else self.default_template
            document_result = await self._generate_report_document(
                template_path, 
                report_data, 
                ai_analysis,
                report_config
            )
            
            # Step 6: Store report metadata
            report_record = await self._store_report_metadata(
                program_id, 
                user_id, 
                document_result, 
                ai_analysis,
                sync_results
            )
            
            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Successfully generated complete report for program {program_id} in {generation_time:.2f} seconds")
            
            return {
                'status': 'success',
                'report_id': report_record.id,
                'program_id': program_id,
                'program_title': program.title,
                'document_path': document_result['output_path'],
                'document_filename': document_result['output_filename'],
                'participants_analyzed': len(participants),
                'sync_results': sync_results,
                'ai_analysis': {
                    'summary': ai_analysis.summary,
                    'insights_count': len(ai_analysis.insights),
                    'recommendations_count': len(ai_analysis.recommendations),
                    'quality_score': ai_analysis.quality_score
                },
                'generation_time_seconds': generation_time,
                'generated_at': end_time.isoformat(),
                'generated_by': user_id
            }
            
        except Exception as e:
            logger.error(f"Error generating complete report: {str(e)}")
            raise Exception(f"Report generation failed: {str(e)}")

    async def _sync_all_external_data(self, program_id: int, user_id: str) -> Dict[str, Any]:
        """Sync all external form data for the program - NO MOCK DATA"""
        try:
            from app.models.production import FormIntegration
            
            # Get all form integrations for this program
            integrations = FormIntegration.query.filter_by(program_id=program_id).all()
            
            sync_results = {
                'google_forms': [],
                'microsoft_forms': [],
                'total_synced': 0,
                'errors': []
            }
            
            # Sync Google Forms
            google_integrations = [i for i in integrations if i.platform == 'google_forms']
            for integration in google_integrations:
                try:
                    result = await self.google_service.sync_form_to_database(
                        user_id, 
                        integration.form_id, 
                        program_id
                    )
                    sync_results['google_forms'].append(result)
                    sync_results['total_synced'] += result.get('responses_processed', 0)
                except Exception as e:
                    error_msg = f"Google Forms sync error for form {integration.form_id}: {str(e)}"
                    sync_results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Sync Microsoft Forms
            microsoft_integrations = [i for i in integrations if i.platform == 'microsoft_forms']
            for integration in microsoft_integrations:
                try:
                    result = await self.microsoft_service.sync_form_to_database(
                        user_id,
                        integration.form_id,
                        program_id
                    )
                    sync_results['microsoft_forms'].append(result)
                    sync_results['total_synced'] += result.get('responses_processed', 0)
                except Exception as e:
                    error_msg = f"Microsoft Forms sync error for form {integration.form_id}: {str(e)}"
                    sync_results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Completed external data sync: {sync_results['total_synced']} total responses synced")
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Error syncing external data: {str(e)}")
            raise Exception(f"Data sync failed: {str(e)}")

    async def _prepare_report_data(self, program, participants: List) -> Dict[str, Any]:
        """Prepare comprehensive report data - NO MOCK DATA"""
        try:
            from app.models.production import AttendanceRecord, FormResponse
            
            # Get attendance records
            all_attendance = []
            for participant in participants:
                attendance_records = AttendanceRecord.query.filter_by(
                    participant_id=participant.id
                ).all()
                
                for record in attendance_records:
                    all_attendance.append({
                        'participant_id': participant.id,
                        'participant_name': participant.full_name,
                        'session_date': record.session_date.isoformat() if record.session_date else None,
                        'status': record.status,
                        'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                        'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None
                    })
            
            # Get form responses
            form_responses = FormResponse.query.join(
                'integration'
            ).filter_by(program_id=program.id).all()
            
            # Calculate attendance statistics
            attendance_stats = self._calculate_attendance_statistics(all_attendance, participants)
            
            # Prepare participant data
            participant_data = []
            for participant in participants:
                # Get participant's attendance records
                participant_attendance = [a for a in all_attendance if a['participant_id'] == participant.id]
                
                participant_data.append({
                    'id': participant.id,
                    'full_name': participant.full_name,
                    'email': participant.email,
                    'phone': participant.phone,
                    'organization': participant.organization,
                    'department': participant.department,
                    'position': participant.position,
                    'gender': participant.gender,
                    'identification_number': participant.identification_number,
                    'registration_date': participant.registration_date.isoformat() if participant.registration_date else None,
                    'registration_source': participant.registration_source,
                    'attendance_count': len([a for a in participant_attendance if a['status'] in ['present', 'attended']]),
                    'total_sessions': len(set(a['session_date'] for a in participant_attendance if a['session_date'])),
                    'attendance_rate': self._calculate_participant_attendance_rate(participant_attendance)
                })
            
            # Prepare program data
            program_data = {
                'id': program.id,
                'title': program.title,
                'description': program.description,
                'start_date': program.start_date.isoformat() if program.start_date else None,
                'end_date': program.end_date.isoformat() if program.end_date else None,
                'location': program.location,
                'department': program.department,
                'organizer': program.organizer,
                'status': program.status,
                'created_at': program.created_at.isoformat() if program.created_at else None
            }
            
            # Compile final report data
            report_data = {
                'program': program_data,
                'participants': participant_data,
                'attendance_records': all_attendance,
                'attendance_statistics': attendance_stats,
                'form_responses': [
                    {
                        'id': fr.id,
                        'platform': fr.integration.platform,
                        'form_title': fr.integration.form_title,
                        'submitted_at': fr.submitted_at.isoformat() if fr.submitted_at else None,
                        'quality_score': fr.quality_score,
                        'response_data': fr.response_data
                    } for fr in form_responses
                ],
                'report_metadata': {
                    'generated_date': datetime.utcnow().isoformat(),
                    'total_participants': len(participants),
                    'total_form_responses': len(form_responses),
                    'total_attendance_records': len(all_attendance),
                    'data_completeness_score': self._calculate_data_completeness(participant_data, all_attendance)
                }
            }
            
            logger.info(f"Prepared comprehensive report data for {len(participants)} participants")
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error preparing report data: {str(e)}")
            raise Exception(f"Data preparation failed: {str(e)}")

    async def _generate_ai_analysis(self, program, participants: List, report_data: Dict[str, Any]) -> AnalysisResult:
        """Generate comprehensive AI analysis - NO MOCK DATA"""
        try:
            program_context = {
                'title': program.title,
                'description': program.description,
                'duration': (program.end_date - program.start_date).days if program.end_date and program.start_date else None,
                'type': 'training_program',
                'participant_count': len(participants)
            }
            
            # Convert participants to analysis format
            participant_analysis_data = []
            for participant in participants:
                participant_analysis_data.append({
                    'full_name': participant.full_name,
                    'organization': participant.organization,
                    'department': participant.department,
                    'position': participant.position,
                    'gender': participant.gender,
                    'registration_source': participant.registration_source
                })
            
            # Generate participant demographics analysis
            demographics_analysis = await self.ai_service.analyze_participant_data(
                participant_analysis_data,
                program_context
            )
            
            # Generate attendance analysis if we have attendance data
            attendance_analysis = None
            if report_data.get('attendance_records'):
                attendance_analysis = await self.ai_service.analyze_attendance_patterns(
                    report_data['attendance_records'],
                    program_context
                )
            
            # Generate feedback analysis if we have form responses
            feedback_analysis = None
            if report_data.get('form_responses'):
                # Extract feedback text from form responses
                feedback_data = []
                for response in report_data['form_responses']:
                    response_data = response.get('response_data', {})
                    if isinstance(response_data, dict):
                        # Look for feedback fields
                        for key, value in response_data.items():
                            if any(word in key.lower() for word in ['feedback', 'comment', 'suggestion', 'opinion']):
                                feedback_data.append({
                                    'feedback_text': str(value),
                                    'source': response.get('platform'),
                                    'submitted_at': response.get('submitted_at')
                                })
                
                if feedback_data:
                    feedback_analysis = await self.ai_service.analyze_feedback_sentiment(
                        feedback_data,
                        program_context
                    )
            
            # Combine all analyses
            combined_insights = demographics_analysis.insights.copy()
            combined_recommendations = demographics_analysis.recommendations.copy()
            
            if attendance_analysis:
                combined_insights.extend(attendance_analysis.insights)
                combined_recommendations.extend(attendance_analysis.recommendations)
            
            if feedback_analysis:
                combined_insights.extend(feedback_analysis.insights)
                combined_recommendations.extend(feedback_analysis.recommendations)
            
            # Create comprehensive summary
            summary_parts = [demographics_analysis.summary]
            if attendance_analysis:
                summary_parts.append(attendance_analysis.summary)
            if feedback_analysis:
                summary_parts.append(feedback_analysis.summary)
            
            combined_summary = " ".join(summary_parts)
            
            # Calculate overall quality score
            scores = [demographics_analysis.quality_score]
            if attendance_analysis:
                scores.append(attendance_analysis.quality_score)
            if feedback_analysis:
                scores.append(feedback_analysis.quality_score)
            
            overall_quality_score = sum(scores) / len(scores)
            
            # Create combined analysis result
            combined_analysis = AnalysisResult(
                summary=combined_summary,
                insights=combined_insights,
                recommendations=list(set(combined_recommendations)),  # Remove duplicates
                quality_score=overall_quality_score,
                confidence_level='high' if overall_quality_score > 0.8 else 'medium',
                analysis_metadata={
                    'demographics_analysis': demographics_analysis.analysis_metadata,
                    'attendance_analysis': attendance_analysis.analysis_metadata if attendance_analysis else None,
                    'feedback_analysis': feedback_analysis.analysis_metadata if feedback_analysis else None,
                    'combined_analysis_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Generated comprehensive AI analysis with {len(combined_insights)} insights and {len(combined_recommendations)} recommendations")
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")

    async def _generate_report_document(self, template_path: str, report_data: Dict[str, Any], ai_analysis: AnalysisResult, report_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate final report document - NO MOCK DATA"""
        try:
            # Prepare template data
            template_data = {
                # Program information
                'program.title': report_data['program']['title'],
                'program.description': report_data['program']['description'],
                'program.start_date': report_data['program']['start_date'],
                'program.end_date': report_data['program']['end_date'],
                'program.location': report_data['program']['location'],
                'program.organizer': report_data['program']['organizer'],
                'program.department': report_data['program']['department'],
                
                # Report metadata
                'report.generated_date': datetime.utcnow().strftime('%d/%m/%Y'),
                'report.generated_time': datetime.utcnow().strftime('%H:%M:%S'),
                'report.total_participants': len(report_data['participants']),
                'report.total_responses': len(report_data.get('form_responses', [])),
                
                # Statistics
                'attendance.total_sessions': report_data['attendance_statistics'].get('total_sessions', 0),
                'attendance.average_rate': f"{report_data['attendance_statistics'].get('average_attendance_rate', 0) * 100:.1f}%",
                
                # AI Analysis
                'analysis.summary': ai_analysis.summary,
                'analysis.quality_score': f"{ai_analysis.quality_score * 100:.1f}%",
                'analysis.insights_count': len(ai_analysis.insights),
                'analysis.recommendations_count': len(ai_analysis.recommendations),
                
                # Key insights (first 3)
                'insight.1': ai_analysis.insights[0]['description'] if len(ai_analysis.insights) > 0 else '',
                'insight.2': ai_analysis.insights[1]['description'] if len(ai_analysis.insights) > 1 else '',
                'insight.3': ai_analysis.insights[2]['description'] if len(ai_analysis.insights) > 2 else '',
                
                # Key recommendations (first 3)
                'recommendation.1': ai_analysis.recommendations[0] if len(ai_analysis.recommendations) > 0 else '',
                'recommendation.2': ai_analysis.recommendations[1] if len(ai_analysis.recommendations) > 1 else '',
                'recommendation.3': ai_analysis.recommendations[2] if len(ai_analysis.recommendations) > 2 else '',
            }
            
            # Add participant list (first 10 for template)
            for i, participant in enumerate(report_data['participants'][:10]):
                template_data[f'participant.{i+1}.name'] = participant['full_name']
                template_data[f'participant.{i+1}.organization'] = participant['organization']
                template_data[f'participant.{i+1}.attendance_rate'] = f"{participant['attendance_rate'] * 100:.1f}%"
            
            # Generate output filename
            output_filename = None
            if report_config and report_config.get('output_filename'):
                output_filename = report_config['output_filename']
            else:
                safe_title = "".join(c for c in report_data['program']['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                output_filename = f"{safe_title}_Report_{timestamp}.docx"
            
            # Convert template
            document_result = await self.template_service.convert_template(
                template_path,
                template_data,
                output_filename
            )
            
            logger.info(f"Successfully generated report document: {document_result['output_filename']}")
            
            return document_result
            
        except Exception as e:
            logger.error(f"Error generating report document: {str(e)}")
            raise Exception(f"Document generation failed: {str(e)}")

    async def _store_report_metadata(self, program_id: int, user_id: str, document_result: Dict[str, Any], ai_analysis: AnalysisResult, sync_results: Dict[str, Any]):
        """Store report metadata in database - NO MOCK DATA"""
        try:
            from app.models.production import Report
            
            report = Report(
                program_id=program_id,
                report_type='comprehensive',
                file_path=document_result['output_path'],
                file_name=document_result['output_filename'],
                file_size=document_result.get('file_size', 0),
                summary=ai_analysis.summary,
                insights=ai_analysis.insights,
                recommendations=ai_analysis.recommendations,
                quality_score=ai_analysis.quality_score,
                generation_metadata={
                    'sync_results': sync_results,
                    'ai_analysis_metadata': ai_analysis.analysis_metadata,
                    'template_conversion': document_result,
                    'generation_timestamp': datetime.utcnow().isoformat()
                },
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(report)
            db.session.commit()
            
            logger.info(f"Stored report metadata with ID: {report.id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error storing report metadata: {str(e)}")
            raise Exception(f"Report storage failed: {str(e)}")

    def _calculate_attendance_statistics(self, attendance_records: List[Dict], participants: List) -> Dict[str, Any]:
        """Calculate attendance statistics from real data - NO MOCK DATA"""
        if not attendance_records:
            return {
                'total_sessions': 0,
                'total_participants': len(participants),
                'average_attendance_rate': 0.0,
                'attendance_by_session': {},
                'attendance_by_participant': {}
            }
        
        # Group by session
        sessions = {}
        for record in attendance_records:
            session_date = record.get('session_date')
            if session_date:
                if session_date not in sessions:
                    sessions[session_date] = {'present': 0, 'total': 0}
                
                sessions[session_date]['total'] += 1
                if record.get('status') in ['present', 'attended']:
                    sessions[session_date]['present'] += 1
        
        # Calculate session attendance rates
        for session_date, stats in sessions.items():
            stats['rate'] = stats['present'] / stats['total'] if stats['total'] > 0 else 0
        
        # Calculate overall average
        total_present = sum(record.get('status') in ['present', 'attended'] for record in attendance_records)
        average_rate = total_present / len(attendance_records) if attendance_records else 0
        
        return {
            'total_sessions': len(sessions),
            'total_participants': len(participants),
            'average_attendance_rate': average_rate,
            'attendance_by_session': sessions,
            'total_attendance_records': len(attendance_records)
        }

    def _calculate_participant_attendance_rate(self, participant_attendance: List[Dict]) -> float:
        """Calculate attendance rate for individual participant - NO MOCK DATA"""
        if not participant_attendance:
            return 0.0
        
        present_count = sum(1 for record in participant_attendance if record.get('status') in ['present', 'attended'])
        return present_count / len(participant_attendance)

    def _calculate_data_completeness(self, participants: List[Dict], attendance_records: List[Dict]) -> float:
        """Calculate data completeness score - NO MOCK DATA"""
        if not participants:
            return 0.0
        
        # Check participant data completeness
        required_fields = ['full_name', 'email', 'organization']
        completeness_scores = []
        
        for participant in participants:
            filled_fields = sum(1 for field in required_fields if participant.get(field))
            score = filled_fields / len(required_fields)
            completeness_scores.append(score)
        
        participant_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # Factor in attendance data availability
        attendance_completeness = 1.0 if attendance_records else 0.5
        
        # Overall score (weighted)
        overall_score = (participant_completeness * 0.7) + (attendance_completeness * 0.3)
        
        return overall_score

    async def get_report_status(self, report_id: int) -> Dict[str, Any]:
        """Get status of a generated report - NO MOCK DATA"""
        try:
            from app.models.production import Report
            
            report = Report.query.get(report_id)
            if not report:
                raise ValueError(f"Report with ID {report_id} not found")
            
            # Check if file still exists
            file_exists = os.path.exists(report.file_path) if report.file_path else False
            
            return {
                'report_id': report.id,
                'program_id': report.program_id,
                'report_type': report.report_type,
                'file_name': report.file_name,
                'file_path': report.file_path,
                'file_exists': file_exists,
                'file_size': report.file_size,
                'quality_score': report.quality_score,
                'insights_count': len(report.insights) if report.insights else 0,
                'recommendations_count': len(report.recommendations) if report.recommendations else 0,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'created_by': report.created_by,
                'status': 'completed',
                'generation_metadata': report.generation_metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting report status: {str(e)}")
            raise Exception(f"Failed to get report status: {str(e)}")

    async def list_program_reports(self, program_id: int) -> List[Dict[str, Any]]:
        """List all reports for a program - NO MOCK DATA"""
        try:
            from app.models.production import Report
            
            reports = Report.query.filter_by(program_id=program_id).order_by(Report.created_at.desc()).all()
            
            report_list = []
            for report in reports:
                file_exists = os.path.exists(report.file_path) if report.file_path else False
                
                report_list.append({
                    'report_id': report.id,
                    'report_type': report.report_type,
                    'file_name': report.file_name,
                    'file_exists': file_exists,
                    'file_size': report.file_size,
                    'quality_score': report.quality_score,
                    'created_at': report.created_at.isoformat() if report.created_at else None,
                    'created_by': report.created_by,
                    'summary': report.summary[:200] + "..." if report.summary and len(report.summary) > 200 else report.summary
                })
            
            return report_list
            
        except Exception as e:
            logger.error(f"Error listing program reports: {str(e)}")
            raise Exception(f"Failed to list reports: {str(e)}")
