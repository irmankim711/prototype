"""
Advanced Template Optimization Service
Handles comprehensive data extraction and mapping for complex LaTeX templates.
"""

import re
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path
from .excel_parser import ExcelParserService

logger = logging.getLogger(__name__)


class LaTeXTemplateAnalyzer:
    """Analyzes LaTeX templates and extracts all placeholder patterns."""
    
    def __init__(self):
        self.placeholder_patterns = [
            r'\{\{([^}]+)\}\}',  # Mustache style {{variable}}
            r'\{\{#([^}]+)\}\}(.*?)\{\{/\1\}\}',  # Loop blocks {{#items}}...{{/items}}
            r'\{\{([^}]+\.[^}]+)\}\}',  # Nested properties {{object.property}}
        ]
        
    def extract_all_placeholders(self, template_content: str) -> Dict[str, Any]:
        """Extract all placeholders and their types from LaTeX template."""
        placeholders = {
            'simple': [],
            'nested': [],
            'loops': [],
            'tables': [],
            'conditionals': []
        }
        
        # Extract simple placeholders
        simple_pattern = r'\{\{([^#/][^}]*)\}\}'
        for match in re.finditer(simple_pattern, template_content):
            placeholder = match.group(1).strip()
            if '.' in placeholder:
                placeholders['nested'].append(placeholder)
            else:
                placeholders['simple'].append(placeholder)
        
        # Extract loop blocks
        loop_pattern = r'\{\{#([^}]+)\}\}(.*?)\{\{/\1\}\}'
        for match in re.finditer(loop_pattern, template_content, re.DOTALL):
            loop_var = match.group(1).strip()
            loop_content = match.group(2)
            
            # Extract placeholders within the loop
            loop_placeholders = []
            for inner_match in re.finditer(simple_pattern, loop_content):
                loop_placeholders.append(inner_match.group(1).strip())
            
            placeholders['loops'].append({
                'variable': loop_var,
                'content': loop_content,
                'inner_placeholders': loop_placeholders
            })
        
        # Detect table structures (longtable, tabular)
        table_patterns = [
            r'\\begin\{longtable\}(.*?)\\end\{longtable\}',
            r'\\begin\{tabular\}(.*?)\\end\{tabular\}'
        ]
        
        for pattern in table_patterns:
            for match in re.finditer(pattern, template_content, re.DOTALL):
                table_content = match.group(1)
                table_placeholders = []
                for placeholder_match in re.finditer(simple_pattern, table_content):
                    table_placeholders.append(placeholder_match.group(1).strip())
                
                placeholders['tables'].append({
                    'type': 'longtable' if 'longtable' in pattern else 'tabular',
                    'content': table_content,
                    'placeholders': table_placeholders
                })
        
        # Remove duplicates
        placeholders['simple'] = list(set(placeholders['simple']))
        placeholders['nested'] = list(set(placeholders['nested']))
        
        return placeholders


class ExcelDataMapper:
    """Maps Excel data to template structure based on intelligent pattern recognition."""
    
    def __init__(self):
        self.excel_service = ExcelParserService()
        
    def analyze_excel_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze Excel file and extract all data patterns."""
        try:
            # Parse Excel file with enhanced detection
            result = self.excel_service.parse_excel_file(file_path, "data_file.xlsx")
            
            if not result['success']:
                raise ValueError(f"Failed to parse Excel: {result.get('error', 'Unknown error')}")
            
            # Get tables data from the parser result
            tables_data = result.get('tables', [])
            
            analysis = {
                'program_info': {},
                'participants': [],
                'evaluation_data': {},
                'tentative': {},
                'suggestions': {},
                'attendance': {},
                'metadata': result.get('metadata', {})
            }
            
            # Group tables by sheet name for processing
            sheets_data = {}
            for table in tables_data:
                sheet_name = table.get('sheet_name', 'Sheet1')
                if sheet_name not in sheets_data:
                    sheets_data[sheet_name] = {'tables': []}
                sheets_data[sheet_name]['tables'].append(table)
            
            # Process each sheet
            for sheet_name, sheet_data in sheets_data.items():
                self._analyze_sheet_content(sheet_name, sheet_data, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Excel structure: {str(e)}")
            raise
    
    def _analyze_sheet_content(self, sheet_name: str, sheet_data: Dict, analysis: Dict[str, Any]):
        """Analyze individual sheet content and categorize data."""
        sheet_name_lower = sheet_name.lower()
        
        # Analyze based on sheet name patterns
        if any(keyword in sheet_name_lower for keyword in ['program', 'info', 'maklumat']):
            self._extract_program_info(sheet_data, analysis)
        elif any(keyword in sheet_name_lower for keyword in ['participant', 'peserta', 'attendance', 'kehadiran']):
            self._extract_participants_data(sheet_data, analysis)
        elif any(keyword in sheet_name_lower for keyword in ['evaluation', 'penilaian', 'assessment']):
            self._extract_evaluation_data(sheet_data, analysis)
        elif any(keyword in sheet_name_lower for keyword in ['tentative', 'schedule', 'jadual']):
            self._extract_tentative_data(sheet_data, analysis)
        elif any(keyword in sheet_name_lower for keyword in ['suggestion', 'cadangan', 'feedback']):
            self._extract_suggestions_data(sheet_data, analysis)
        else:
            # Try to auto-detect content type based on data patterns
            self._auto_detect_content_type(sheet_data, analysis)
    
    def _extract_program_info(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Extract program information from sheet data."""
        tables = sheet_data.get('tables', [])
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 2:
                continue
                
            # Look for key-value pairs
            for row in data[1:]:  # Skip header
                if len(row) >= 2 and row[0] and row[1]:
                    key = str(row[0]).lower().strip()
                    value = str(row[1]).strip()
                    
                    # Map common fields
                    field_mapping = {
                        'title': ['title', 'tajuk', 'nama program', 'program name'],
                        'date': ['date', 'tarikh', 'tariikh'],
                        'time': ['time', 'masa'],
                        'location': ['location', 'tempat', 'lokasi'],
                        'organizer': ['organizer', 'penganjur', 'anjuran'],
                        'speaker': ['speaker', 'penceramah'],
                        'trainer': ['trainer', 'jurulatih'],
                        'facilitator': ['facilitator', 'fasilitator'],
                        'male_participants': ['male', 'lelaki', 'peserta lelaki'],
                        'female_participants': ['female', 'perempuan', 'peserta perempuan'],
                        'total_participants': ['total', 'jumlah', 'keseluruhan'],
                        'background': ['background', 'latar belakang'],
                        'objectives': ['objectives', 'objektif', 'matlamat']
                    }
                    
                    for field, keywords in field_mapping.items():
                        if any(keyword in key for keyword in keywords):
                            analysis['program_info'][field] = value
                            break
    
    def _extract_participants_data(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Extract participants data from sheet."""
        tables = sheet_data.get('tables', [])
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 2:
                continue
            
            headers = [str(h).lower().strip() for h in data[0]] if data else []
            
            # Look for participant list structure
            if any(keyword in ' '.join(headers) for keyword in ['name', 'nama', 'participant']):
                participants = []
                
                for i, row in enumerate(data[1:], 1):
                    if len(row) < len(headers):
                        continue
                    
                    participant: Dict[str, Any] = {'bil': i}
                    
                    for j, header in enumerate(headers):
                        if j < len(row) and row[j]:
                            value = str(row[j]).strip()
                            
                            # Map common participant fields
                            if any(keyword in header for keyword in ['name', 'nama']):
                                participant['name'] = value
                            elif any(keyword in header for keyword in ['ic', 'k/p', 'kp', 'id']):
                                participant['ic'] = value
                            elif any(keyword in header for keyword in ['address', 'alamat']):
                                participant['address'] = value
                            elif any(keyword in header for keyword in ['tel', 'phone', 'telefon']):
                                participant['tel'] = value
                            elif any(keyword in header for keyword in ['pre', 'pra']):
                                try:
                                    participant['pre_mark'] = float(value)
                                except ValueError:
                                    participant['pre_mark'] = value
                            elif any(keyword in header for keyword in ['post']):
                                try:
                                    participant['post_mark'] = float(value)
                                except ValueError:
                                    participant['post_mark'] = value
                            elif any(keyword in header for keyword in ['attend', 'hadir', 'day1', 'h1']):
                                participant['attendance_day1'] = value
                            elif any(keyword in header for keyword in ['day2', 'h2']):
                                participant['attendance_day2'] = value
                    
                    # Calculate change if both pre and post marks exist
                    if 'pre_mark' in participant and 'post_mark' in participant:
                        try:
                            pre = float(participant['pre_mark'])
                            post = float(participant['post_mark'])
                            participant['change'] = post - pre
                        except (ValueError, TypeError):
                            participant['change'] = 0
                    
                    participants.append(participant)
                
                analysis['participants'] = participants
    
    def _extract_evaluation_data(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Extract evaluation data from sheet."""
        tables = sheet_data.get('tables', [])
        
        evaluation = {
            'content': {},
            'tools': {},
            'presenter': {},
            'facilitator': {},
            'environment': {},
            'overall': {},
            'summary': {'percentage': {}},
            'pre_post': {}
        }
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 2:
                continue
            
            headers = [str(h).lower().strip() for h in data[0]] if data else []
            
            # Look for evaluation matrix with ratings 1-5
            if any(str(i) in headers for i in range(1, 6)):
                for row in data[1:]:
                    if len(row) < 2:
                        continue
                    
                    criterion = str(row[0]).lower().strip()
                    
                    # Extract ratings for each scale
                    ratings = {}
                    for i in range(1, 6):
                        col_index = None
                        for j, header in enumerate(headers):
                            if str(i) in header:
                                col_index = j
                                break
                        
                        if col_index and col_index < len(row):
                            try:
                                ratings[str(i)] = int(row[col_index])
                            except (ValueError, TypeError):
                                ratings[str(i)] = 0
                    
                    # Categorize by evaluation type
                    if any(keyword in criterion for keyword in ['objektif', 'objective']):
                        evaluation['content']['objective'] = ratings
                    elif any(keyword in criterion for keyword in ['impak', 'impact']):
                        evaluation['content']['impact'] = ratings
                    elif any(keyword in criterion for keyword in ['masa', 'duration']):
                        evaluation['content']['duration'] = ratings
                    elif any(keyword in criterion for keyword in ['nota', 'notes']):
                        evaluation['tools']['notes'] = ratings
                    elif any(keyword in criterion for keyword in ['lcd']):
                        evaluation['tools']['lcd'] = ratings
                    elif any(keyword in criterion for keyword in ['persediaan', 'preparation']):
                        evaluation['presenter']['preparation'] = ratings
                    elif any(keyword in criterion for keyword in ['penyampaian', 'delivery']):
                        evaluation['presenter']['delivery'] = ratings
                    elif any(keyword in criterion for keyword in ['lokasi', 'location']):
                        evaluation['environment']['location'] = ratings
        
        analysis['evaluation_data'] = evaluation
    
    def _extract_tentative_data(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Extract program tentative/schedule data."""
        tables = sheet_data.get('tables', [])
        
        tentative = {'day1': [], 'day2': []}
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 2:
                continue
            
            headers = [str(h).lower().strip() for h in data[0]] if data else []
            
            # Look for schedule structure
            if any(keyword in ' '.join(headers) for keyword in ['time', 'masa', 'activity', 'aktiviti']):
                current_day = 'day1'  # Default
                
                for row in data[1:]:
                    if len(row) < 2:
                        continue
                    
                    # Check if this row indicates a new day
                    row_text = ' '.join(str(cell) for cell in row).lower()
                    if any(keyword in row_text for keyword in ['day 2', 'hari kedua', 'hari 2']):
                        current_day = 'day2'
                        continue
                    
                    time_val = str(row[0]).strip() if row[0] else ''
                    activity_val = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                    description_val = str(row[2]).strip() if len(row) > 2 and row[2] else ''
                    handler_val = str(row[3]).strip() if len(row) > 3 and row[3] else ''
                    
                    if time_val and activity_val:
                        tentative[current_day].append({
                            'time': time_val,
                            'activity': activity_val,
                            'description': description_val,
                            'handler': handler_val
                        })
        
        analysis['tentative'] = tentative
    
    def _extract_suggestions_data(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Extract suggestions and feedback data."""
        tables = sheet_data.get('tables', [])
        
        suggestions = {
            'consultant': [],
            'participants': []
        }
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 1:
                continue
            
            for row in data:
                if not row or not row[0]:
                    continue
                
                text = str(row[0]).strip()
                if len(text) > 10:  # Meaningful suggestion
                    # Try to categorize
                    if any(keyword in text.lower() for keyword in ['consultant', 'perunding']):
                        suggestions['consultant'].append(text)
                    else:
                        suggestions['participants'].append(text)
        
        analysis['suggestions'] = suggestions
    
    def _auto_detect_content_type(self, sheet_data: Dict, analysis: Dict[str, Any]):
        """Auto-detect content type based on data patterns."""
        tables = sheet_data.get('tables', [])
        
        for table in tables:
            data = table.get('data', [])
            if len(data) < 2:
                continue
            
            # Analyze first few rows to determine content type
            sample_text = ' '.join(str(cell) for row in data[:5] for cell in row if cell).lower()
            
            if any(keyword in sample_text for keyword in ['name', 'nama', 'participant']):
                self._extract_participants_data({'tables': [table]}, analysis)
            elif any(keyword in sample_text for keyword in ['evaluation', 'penilaian']):
                self._extract_evaluation_data({'tables': [table]}, analysis)
            elif any(keyword in sample_text for keyword in ['time', 'masa', 'schedule']):
                self._extract_tentative_data({'tables': [table]}, analysis)


class TemplateDataMerger:
    """Merges extracted Excel data with template placeholders."""
    
    def __init__(self):
        self.template_analyzer = LaTeXTemplateAnalyzer()
        self.data_mapper = ExcelDataMapper()
    
    def create_template_context(self, template_content: str, excel_file_path: str) -> Dict[str, Any]:
        """Create complete context for template rendering."""
        try:
            # Analyze template structure
            placeholders = self.template_analyzer.extract_all_placeholders(template_content)
            
            # Extract and map Excel data
            excel_analysis = self.data_mapper.analyze_excel_structure(excel_file_path)
            
            # Create comprehensive context
            context = self._build_complete_context(placeholders, excel_analysis)
            
            return {
                'success': True,
                'context': context,
                'placeholders': placeholders,
                'data_analysis': excel_analysis,
                'missing_fields': self._identify_missing_fields(placeholders, context)
            }
            
        except Exception as e:
            logger.error(f"Error creating template context: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'context': {},
                'placeholders': {},
                'data_analysis': {}
            }
    
    def _build_complete_context(self, placeholders: Dict, excel_data: Dict) -> Dict[str, Any]:
        """Build complete context from placeholders and Excel data."""
        context = {}
        
        # Map program information
        program_info = excel_data.get('program_info', {})
        context['program'] = {
            'title': program_info.get('title', 'PROGRAM TITLE'),
            'date': program_info.get('date', datetime.now().strftime('%d/%m/%Y')),
            'time': program_info.get('time', '9:00 AM - 5:00 PM'),
            'location': program_info.get('location', 'LOCATION'),
            'place': program_info.get('location', 'VENUE'),
            'organizer': program_info.get('organizer', 'ORGANIZER'),
            'speaker': program_info.get('speaker', 'SPEAKER'),
            'trainer': program_info.get('trainer', 'TRAINER'),
            'facilitator': program_info.get('facilitator', 'FACILITATOR'),
            'male_participants': program_info.get('male_participants', '0'),
            'female_participants': program_info.get('female_participants', '0'),
            'total_participants': program_info.get('total_participants', '0'),
            'background': program_info.get('background', 'PROGRAM BACKGROUND'),
            'objectives': program_info.get('objectives', 'PROGRAM OBJECTIVES'),
            'secretariat': program_info.get('secretariat', 'SECRETARIAT'),
            'transport_company': program_info.get('transport_company', 'TRANSPORT COMPANY'),
            'catering': program_info.get('catering', 'CATERING SERVICE'),
            'day1_date': program_info.get('day1_date', program_info.get('date', '')),
            'day2_date': program_info.get('day2_date', program_info.get('date', '')),
            'conclusion': program_info.get('conclusion', 'PROGRAM CONCLUSION')
        }
        
        # Map participants data
        participants = excel_data.get('participants', [])
        context['participants'] = participants
        
        # Map evaluation data
        evaluation_data = excel_data.get('evaluation_data', {})
        context['evaluation'] = {
            'content': evaluation_data.get('content', {}),
            'tools': evaluation_data.get('tools', {}),
            'presenter': evaluation_data.get('presenter', {}),
            'facilitator': evaluation_data.get('facilitator', {}),
            'environment': evaluation_data.get('environment', {}),
            'overall': evaluation_data.get('overall', {}),
            'summary': evaluation_data.get('summary', {'percentage': {}}),
            'pre_post': evaluation_data.get('pre_post', {}),
            'total_participants': len(participants)
        }
        
        # Map tentative data
        tentative_data = excel_data.get('tentative', {})
        context['tentative'] = tentative_data
        
        # Map suggestions
        suggestions_data = excel_data.get('suggestions', {})
        context['suggestions'] = suggestions_data
        
        # Calculate attendance data
        total_invited = len(participants)
        total_attended = sum(1 for p in participants if p.get('attendance_day1') or p.get('attendance_day2'))
        context['attendance'] = {
            'total_invited': total_invited,
            'total_attended': total_attended,
            'total_absent': total_invited - total_attended
        }
        
        # Add signature placeholders
        context['signature'] = {
            'consultant': {'name': 'CONSULTANT NAME'},
            'executive': {'name': 'EXECUTIVE NAME'},
            'head': {'name': 'HEAD OF DEPARTMENT'}
        }
        
        # Add image placeholders
        context['images'] = [
            {'path': 'images/program1.jpg', 'caption': 'Program Activity 1'},
            {'path': 'images/program2.jpg', 'caption': 'Program Activity 2'}
        ]
        
        return context
    
    def _identify_missing_fields(self, placeholders: Dict, context: Dict) -> List[str]:
        """Identify missing fields that couldn't be mapped from Excel data."""
        missing = []
        
        all_placeholders = (
            placeholders.get('simple', []) + 
            placeholders.get('nested', [])
        )
        
        for placeholder in all_placeholders:
            if '.' in placeholder:
                # Check nested field
                parts = placeholder.split('.')
                current = context
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        missing.append(placeholder)
                        break
            else:
                # Check simple field
                if placeholder not in context:
                    missing.append(placeholder)
        
        return missing


class TemplateOptimizerService:
    """Main service for template optimization and data mapping."""
    
    def __init__(self):
        self.template_analyzer = LaTeXTemplateAnalyzer()
        self.data_mapper = ExcelDataMapper()
        self.data_merger = TemplateDataMerger()
    
    def optimize_template_with_excel(self, template_content: str, excel_file_path: str) -> Dict[str, Any]:
        """Optimize template with Excel data for flawless rendering."""
        try:
            result = self.data_merger.create_template_context(template_content, excel_file_path)
            
            if result['success']:
                # Generate optimization suggestions
                optimizations = self._generate_optimizations(
                    template_content, 
                    result['context'], 
                    result['missing_fields']
                )
                
                result['optimizations'] = optimizations
                result['enhanced_context'] = self._enhance_context_for_rendering(result['context'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_optimizations(self, template_content: str, context: Dict, missing_fields: List[str]) -> Dict[str, Any]:
        """Generate optimization suggestions for template improvement."""
        optimizations = {
            'missing_data_suggestions': [],
            'template_improvements': [],
            'data_quality_issues': [],
            'formatting_suggestions': []
        }
        
        # Suggest solutions for missing fields
        for field in missing_fields:
            optimizations['missing_data_suggestions'].append({
                'field': field,
                'suggestion': f"Add data for '{field}' in Excel file",
                'severity': 'medium'
            })
        
        # Check for template improvements
        if '{{#participants}}' in template_content and not context.get('participants'):
            optimizations['template_improvements'].append({
                'issue': 'Participants loop defined but no participant data found',
                'suggestion': 'Ensure participant data is in Excel file with proper column headers',
                'severity': 'high'
            })
        
        # Check data quality
        participants = context.get('participants', [])
        if participants:
            incomplete_participants = [p for p in participants if not p.get('name')]
            if incomplete_participants:
                optimizations['data_quality_issues'].append({
                    'issue': f'{len(incomplete_participants)} participants missing names',
                    'suggestion': 'Review participant data in Excel file',
                    'severity': 'medium'
                })
        
        return optimizations
    
    def _enhance_context_for_rendering(self, context: Dict) -> Dict[str, Any]:
        """Enhance context with additional computed fields for better rendering."""
        enhanced = context.copy()
        
        # Calculate evaluation statistics
        if 'evaluation' in enhanced and 'participants' in enhanced:
            participants = enhanced['participants']
            
            # Calculate pre-post statistics
            pre_post_stats = self._calculate_pre_post_stats(participants)
            enhanced['evaluation']['pre_post'] = pre_post_stats
            
            # Calculate evaluation percentages
            evaluation_percentages = self._calculate_evaluation_percentages(enhanced['evaluation'])
            enhanced['evaluation']['summary']['percentage'] = evaluation_percentages
        
        # Format dates consistently
        if 'program' in enhanced:
            program = enhanced['program']
            for date_field in ['date', 'day1_date', 'day2_date']:
                if date_field in program and program[date_field]:
                    # Ensure consistent date format
                    try:
                        if isinstance(program[date_field], str):
                            # Try to parse and reformat
                            parsed_date = datetime.strptime(program[date_field], '%d/%m/%Y')
                            program[date_field] = parsed_date.strftime('%d/%m/%Y')
                    except ValueError:
                        pass  # Keep original format if parsing fails
        
        return enhanced
    
    def _calculate_pre_post_stats(self, participants: List[Dict]) -> Dict[str, Any]:
        """Calculate pre-post evaluation statistics."""
        stats = {
            'increase': {'count': 0, 'percentage': '0%'},
            'decrease': {'count': 0, 'percentage': '0%'},
            'no_change': {'count': 0, 'percentage': '0%'},
            'incomplete': {'count': 0, 'percentage': '0%'}
        }
        
        total = len(participants)
        if total == 0:
            return stats
        
        for participant in participants:
            pre_mark = participant.get('pre_mark')
            post_mark = participant.get('post_mark')
            
            if pre_mark is None or post_mark is None:
                stats['incomplete']['count'] += 1
            else:
                try:
                    pre = float(pre_mark)
                    post = float(post_mark)
                    if post > pre:
                        stats['increase']['count'] += 1
                    elif post < pre:
                        stats['decrease']['count'] += 1
                    else:
                        stats['no_change']['count'] += 1
                except (ValueError, TypeError):
                    stats['incomplete']['count'] += 1
        
        # Calculate percentages
        for category in stats:
            count = stats[category]['count']
            percentage = (count / total) * 100 if total > 0 else 0
            stats[category]['percentage'] = f"{percentage:.1f}%"
        
        return stats
    
    def _calculate_evaluation_percentages(self, evaluation: Dict) -> Dict[str, str]:
        """Calculate evaluation percentages for summary."""
        percentages = {}
        
        # Sample calculation - adjust based on your evaluation structure
        for i in range(1, 6):
            percentages[str(i)] = "20%"  # Default equal distribution
        
        return percentages
