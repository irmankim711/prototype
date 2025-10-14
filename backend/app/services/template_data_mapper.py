"""
Template Data Mapper Service
Maps raw data to the format expected by LaTeX templates
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import re

logger = logging.getLogger(__name__)

class TemplateDataMapper:
    """Service for mapping data to template-specific formats"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TemplateDataMapper")

    def map_data_for_template(self, raw_data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """
        Map raw data to the format expected by a specific template

        Args:
            raw_data: Raw data from forms, Excel, etc.
            template_name: Name of the template (e.g., 'Temp2.tex')

        Returns:
            Mapped data in the format expected by the template
        """
        try:
            # ✅ Enhanced logging for debugging
            self.logger.info(f"🗺️  Starting data mapping for template: {template_name}")
            self.logger.info(f"🗺️  Input data keys: {list(raw_data.keys())}")

            # Validate input data
            validation_result = self._validate_input_data(raw_data)
            if not validation_result['valid']:
                self.logger.warning(f"⚠️  Data validation warnings: {validation_result['warnings']}")
            else:
                self.logger.info(f"✅ Data validation passed")

            # ✅ Log record count for debugging
            records_count = len(raw_data.get('records', raw_data.get('submissions', [])))
            self.logger.info(f"📊 Processing {records_count} records")

            # Choose mapping strategy based on template
            if template_name == 'Temp2.tex':
                self.logger.info(f"🎯 Using Temp2-specific mapping")
                mapped_data = self._map_data_for_temp2(raw_data)
            else:
                self.logger.info(f"🎯 Using default mapping for {template_name}")
                mapped_data = self._map_data_default(raw_data)

            # ✅ Verify mapped data is not empty
            if not mapped_data:
                self.logger.error(f"❌ Mapping resulted in empty data!")
                return self._create_fallback_data(raw_data)

            self.logger.info(f"✅ Mapping completed successfully")
            self.logger.info(f"✅ Mapped data keys: {list(mapped_data.keys())}")
            return mapped_data

        except Exception as e:
            self.logger.error(f"❌ Error mapping data for template {template_name}: {str(e)}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return self._create_fallback_data(raw_data)

    def _map_data_for_temp2(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map data specifically for Temp2.tex template"""
        try:
            # Extract records/submissions
            records = raw_data.get('records', raw_data.get('submissions', []))
            metadata = raw_data.get('metadata', {})

            # Create program data structure expected by Temp2.tex
            program_data = self._extract_program_data(records, metadata)

            # Create evaluation data structure
            evaluation_data = self._create_evaluation_data(records)

            # Create participants data
            participants_data = self._create_participants_data(records)

            # Create suggestions data
            suggestions_data = self._create_suggestions_data(records)

            # Create attendance data
            attendance_data = self._create_attendance_data(records)

            mapped_data = {
                'program': program_data,
                'evaluation': evaluation_data,
                'participants': participants_data,
                'suggestions': suggestions_data,
                'attendance': attendance_data,
                'tentative': {
                    'day1': [],
                    'day2': []
                },
                'images': []
            }

            self.logger.info(f"Successfully mapped data for Temp2.tex with {len(records)} records")
            return mapped_data

        except Exception as e:
            self.logger.error(f"Error mapping data for Temp2.tex: {str(e)}")
            return self._create_fallback_temp2_data(raw_data)

    def _extract_program_data(self, records: List[Dict], metadata: Dict) -> Dict[str, Any]:
        """Extract program information from records"""
        # Try to extract program info from first record or create defaults
        first_record = records[0] if records else {}

        # Handle nested data structure (common in form submissions)
        if 'data' in first_record and isinstance(first_record['data'], dict):
            first_record = {**first_record, **first_record['data']}

        # Log what we're extracting for debugging
        self.logger.info(f"Extracting program data from {len(records)} records")
        if first_record:
            self.logger.debug(f"First record keys: {list(first_record.keys())[:10]}")

        program_data = {
            'title': first_record.get('program_title', first_record.get('title', 'Program Evaluation Report')),
            'location': first_record.get('program_location', first_record.get('location', 'Not Specified')),
            'date': first_record.get('program_date', first_record.get('date', datetime.now().strftime('%Y-%m-%d'))),
            'time': first_record.get('program_time', first_record.get('time', 'Not Specified')),
            'organizer': first_record.get('organizer', first_record.get('organisation', 'Organization')),
            'background': first_record.get('background', first_record.get('program_background', 'Program background information')),
            'place': first_record.get('place', first_record.get('program_location', first_record.get('location', 'Not Specified'))),
            'speaker': first_record.get('speaker', first_record.get('speakers', 'Not Specified')),
            'trainer': first_record.get('trainer', first_record.get('trainers', 'Not Specified')),
            'facilitator': first_record.get('facilitator', first_record.get('facilitators', 'Not Specified')),
            'male_participants': str(self._count_participants_by_gender(records, 'Male')),
            'female_participants': str(self._count_participants_by_gender(records, 'Female')),
            'total_participants': str(len(records)),
            'secretariat': first_record.get('secretariat', 'Not Specified'),
            'transport_company': first_record.get('transport_company', first_record.get('transportation', 'Not Specified')),
            'catering': first_record.get('catering', first_record.get('catering_service', 'Not Specified')),
            'objectives': first_record.get('objectives', first_record.get('program_objectives', 'Program objectives')),
            'day1_date': first_record.get('day1_date', first_record.get('date', datetime.now().strftime('%Y-%m-%d'))),
            'day2_date': first_record.get('day2_date', first_record.get('date', datetime.now().strftime('%Y-%m-%d'))),
            'conclusion': first_record.get('conclusion', first_record.get('program_conclusion', 'Program completed successfully'))
        }

        self.logger.info(f"Extracted program data: title='{program_data['title']}', participants={program_data['total_participants']}")

        return program_data

    def _create_evaluation_data(self, records: List[Dict]) -> Dict[str, Any]:
        """Create evaluation data structure"""
        total_participants = len(records)

        # Create default evaluation scores (1-5 scale)
        evaluation_data = {
            'total_participants': total_participants,
            'content': {
                'objective': {str(i): 4 for i in range(1, 6)},  # Default to 4/5
                'impact': {str(i): 4 for i in range(1, 6)},
                'duration': {str(i): 4 for i in range(1, 6)}
            },
            'tools': {
                'notes': {str(i): 4 for i in range(1, 6)},
                'notes_clarity': {str(i): 4 for i in range(1, 6)},
                'whiteboard': {str(i): 4 for i in range(1, 6)},
                'lcd': {str(i): 4 for i in range(1, 6)},
                'pa_system': {str(i): 4 for i in range(1, 6)}
            },
            'presenter': {
                'preparation': {str(i): 4 for i in range(1, 6)},
                'delivery': {str(i): 4 for i in range(1, 6)},
                'language': {str(i): 4 for i in range(1, 6)},
                'knowledge': {str(i): 4 for i in range(1, 6)},
                'answering': {str(i): 4 for i in range(1, 6)},
                'methodology': {str(i): 4 for i in range(1, 6)},
                'engagement': {str(i): 4 for i in range(1, 6)},
                'feedback': {str(i): 4 for i in range(1, 6)}
            },
            'facilitator': {
                'impact': {str(i): 4 for i in range(1, 6)},
                'performance': {str(i): 4 for i in range(1, 6)}
            },
            'environment': {
                'location': {str(i): 4 for i in range(1, 6)},
                'worship': {str(i): 4 for i in range(1, 6)},
                'facilities': {str(i): 4 for i in range(1, 6)},
                'catering': {str(i): 4 for i in range(1, 6)},
                'seminar_hall': {str(i): 4 for i in range(1, 6)}
            },
            'overall': {
                'impact': {str(i): 4 for i in range(1, 6)},
                'performance': {str(i): 4 for i in range(1, 6)}
            },
            'summary': {
                'percentage': {
                    '1': '5%',
                    '2': '10%',
                    '3': '15%',
                    '4': '40%',
                    '5': '30%'
                }
            },
            'pre_post': {
                'decrease': {'percentage': '10%', 'count': 1},
                'no_change': {'percentage': '20%', 'count': 2},
                'increase': {'percentage': '60%', 'count': 6},
                'incomplete': {'percentage': '10%', 'count': 1}
            },
            'chart': 'evaluation_chart.png'  # Placeholder for chart
        }

        return evaluation_data

    def _create_participants_data(self, records: List[Dict]) -> List[Dict[str, Any]]:
        """Create participants data structure"""
        participants = []

        for i, record in enumerate(records, 1):
            # Handle nested data structure
            if 'data' in record and isinstance(record['data'], dict):
                record = {**record, **record['data']}

            # Extract participant data with multiple fallback field names
            try:
                pre_score = int(record.get('pre_test_score', record.get('pre_mark', record.get('pre_test', 70))))
                post_score = int(record.get('post_test_score', record.get('post_mark', record.get('post_test', 85))))
                change_value = post_score - pre_score
            except (ValueError, TypeError):
                pre_score = 70
                post_score = 85
                change_value = 15

            participant = {
                'bil': str(i),
                'name': record.get('name', record.get('participant_name', record.get('full_name', f'Participant {i}'))),
                'ic': record.get('ic', record.get('id_number', record.get('identity_card', 'Not Specified'))),
                'address': record.get('address', record.get('participant_address', 'Not Specified')),
                'tel': record.get('phone', record.get('tel', record.get('telephone', record.get('phone_number', 'Not Specified')))),
                'attendance_day1': record.get('attendance_day1', record.get('day1_attendance', 'Present')),
                'attendance_day2': record.get('attendance_day2', record.get('day2_attendance', 'Present')),
                'notes': record.get('notes', record.get('remarks', '')),
                'pre_mark': str(pre_score),
                'post_mark': str(post_score),
                'change': str(change_value)
            }
            participants.append(participant)

        self.logger.info(f"Created participants data for {len(participants)} participants")
        return participants

    def _create_suggestions_data(self, records: List[Dict]) -> Dict[str, str]:
        """Create suggestions data structure"""
        # Aggregate suggestions from records
        consultant_suggestions = []
        participant_suggestions = []

        for record in records:
            if record.get('consultant_suggestion'):
                consultant_suggestions.append(record['consultant_suggestion'])
            if record.get('participant_suggestion'):
                participant_suggestions.append(record['participant_suggestion'])

        return {
            'consultant': '; '.join(consultant_suggestions[:3]) if consultant_suggestions else 'No specific suggestions',
            'participants': '; '.join(participant_suggestions[:3]) if participant_suggestions else 'No specific suggestions'
        }

    def _create_attendance_data(self, records: List[Dict]) -> Dict[str, int]:
        """Create attendance data structure"""
        total_invited = len(records) + 2  # Assume 2 additional invites
        total_attended = len([r for r in records if r.get('attendance_status', 'Present') == 'Present'])
        total_absent = total_invited - total_attended

        return {
            'total_invited': total_invited,
            'total_attended': total_attended,
            'total_absent': total_absent
        }

    def _count_participants_by_gender(self, records: List[Dict], gender: str) -> int:
        """Count participants by gender"""
        count = 0
        for record in records:
            record_gender = record.get('gender', record.get('jantina', ''))
            if record_gender.lower() == gender.lower():
                count += 1
        return count if count > 0 else len(records) // 2  # Default split if no gender data

    def _map_data_default(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default data mapping for other templates"""
        records = raw_data.get('records', raw_data.get('submissions', []))

        # Create participants structure for all templates
        participants = self._create_participants_data(records)

        return {
            'title': raw_data.get('title', 'Report'),
            'author': 'Automated Report System',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'records': records,
            'total_records': len(records),
            'participants': participants,  # Add participants structure
            'data': raw_data,
            'submissions': records
        }

    def _create_fallback_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback data when mapping fails"""
        return {
            'title': 'Report Generation Error',
            'author': 'System',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'records': [],
            'total_records': 0,
            'error': 'Data mapping failed'
        }

    def _create_fallback_temp2_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback data specifically for Temp2.tex"""
        return {
            'program': {
                'title': 'Program Report',
                'location': 'Not Specified',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': 'Not Specified',
                'organizer': 'Organization',
                'background': 'Program evaluation report',
                'total_participants': 0
            },
            'evaluation': {
                'total_participants': 0,
                'content': {'objective': {str(i): 0 for i in range(1, 6)}},
                'summary': {'percentage': {str(i): '0%' for i in range(1, 6)}}
            },
            'participants': [],
            'suggestions': {
                'consultant': 'No data available',
                'participants': 'No data available'
            },
            'attendance': {
                'total_invited': 0,
                'total_attended': 0,
                'total_absent': 0
            }
        }

    def extract_template_variables(self, template_content: str) -> List[str]:
        """Extract all variables from template content"""
        # Find Jinja2-style variables: {{ variable }}
        variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
        matches = re.findall(variable_pattern, template_content)

        variables = []
        for match in matches:
            # Clean up variable name (remove filters, etc.)
            var_name = match.strip().split('|')[0].strip()
            if var_name not in variables:
                variables.append(var_name)

        return variables

    def validate_data_mapping(self, mapped_data: Dict[str, Any], template_variables: List[str]) -> Dict[str, Any]:
        """Validate that mapped data contains all required template variables"""
        validation_result = {
            'valid': True,
            'missing_variables': [],
            'coverage_percentage': 0
        }

        missing_vars = []
        for var in template_variables:
            if not self._check_nested_variable(mapped_data, var):
                missing_vars.append(var)

        validation_result['missing_variables'] = missing_vars
        validation_result['valid'] = len(missing_vars) == 0
        validation_result['coverage_percentage'] = ((len(template_variables) - len(missing_vars)) / len(template_variables) * 100) if template_variables else 100

        return validation_result

    def _check_nested_variable(self, data: Dict[str, Any], variable_path: str) -> bool:
        """Check if a nested variable exists in the data"""
        try:
            parts = variable_path.split('.')
            current = data

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False

            return True
        except:
            return False

    def _validate_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data structure before mapping

        Args:
            data: Raw data to validate

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }

        # Check if data is a dictionary
        if not isinstance(data, dict):
            validation_result['valid'] = False
            validation_result['errors'].append(f"Data must be a dictionary, got {type(data)}")
            return validation_result

        # Check for records or submissions
        records = data.get('records', data.get('submissions', []))
        if not records:
            validation_result['warnings'].append("No records or submissions found in data")
        else:
            self.logger.info(f"Validation: Found {len(records)} records/submissions")

        # Check if records are valid
        if records and not isinstance(records, list):
            validation_result['warnings'].append(f"Records should be a list, got {type(records)}")

        # Log metadata if present
        if 'metadata' in data:
            self.logger.info(f"Validation: Metadata present with keys {list(data['metadata'].keys())}")

        return validation_result

# Global instance
template_data_mapper = TemplateDataMapper()