"""
Excel Data Extraction Service
Extracts structured data from uploaded Excel files for report generation
"""

import os
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ExcelDataExtractor:
    """Extract and structure data from Excel files for report generation"""

    def __init__(self):
        self.uploads_dir = Path("static/uploads/excel")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '../config/excel_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading excel_config.json: {e}")
            # Fallback to empty config or default values could be implemented here
            self.config = {}

    def extract_data_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from Excel file

        Args:
            file_path: Path to Excel file (relative or absolute)

        Returns:
            Dict containing extracted and structured data
        """
        try:
            # Resolve file path
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.uploads_dir, file_path)

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Excel file not found: {file_path}")

            logger.info(f"📊 Extracting data from Excel file: {file_path}")

            # Read all sheets from Excel file
            excel_file = pd.ExcelFile(file_path)
            all_sheets = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                all_sheets[sheet_name] = df
                logger.info(f"   📄 Sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")

            # Try to identify the main data sheet
            main_sheet = self._identify_main_sheet(all_sheets)
            main_df = all_sheets.get(main_sheet, list(all_sheets.values())[0])

            logger.info(f"   🎯 Using main sheet: {main_sheet}")

            # Extract structured data
            extracted_data = {
                'program_info': self._extract_program_info(main_df),
                'participants': self._extract_participants(main_df),
                'attendance': self._extract_attendance(main_df),
                'statistics': self._calculate_statistics(main_df),
                'metadata': {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'extraction_date': datetime.utcnow().isoformat(),
                    'total_rows': len(main_df),
                    'total_columns': len(main_df.columns),
                    'sheets': list(all_sheets.keys()),
                    'main_sheet': main_sheet
                }
            }

            logger.info(f"✅ Data extraction complete:")
            logger.info(f"   - Program info fields: {len(extracted_data['program_info'])}")
            logger.info(f"   - Participants: {len(extracted_data['participants'])}")
            logger.info(f"   - Attendance records: {len(extracted_data['attendance'])}")

            return extracted_data

        except Exception as e:
            logger.exception("Error extracting data from Excel")
            raise

    def _identify_main_sheet(self, sheets: Dict[str, pd.DataFrame]) -> str:
        """Identify the main data sheet from multiple sheets"""
        # Prefer sheets with common names
        # Prefer sheets with common names
        priority_names = self.config.get('sheet_detection', {}).get('priority_names', ['data', 'participants', 'sheet1', 'main', 'peserta'])

        for name in priority_names:
            for sheet_name in sheets.keys():
                if name in sheet_name.lower():
                    return sheet_name

        # Otherwise return the first sheet
        return list(sheets.keys())[0]

    def _extract_program_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract program information from DataFrame"""
        program_info = {}

        # Common field mappings (case-insensitive)
        # Common field mappings (case-insensitive)
        field_mappings = self.config.get('program_info_mappings', {
            'title': ['title', 'program_title', 'tajuk', 'nama_program', 'program'],
            'date': ['date', 'tarikh', 'program_date', 'start_date'],
            'time': ['time', 'masa', 'program_time', 'hour'],
            'location': ['location', 'lokasi', 'tempat', 'venue', 'place'],
            'organizer': ['organizer', 'anjuran', 'penganjur', 'organized_by'],
            'facilitator': ['facilitator', 'fasilitator', 'trainer', 'jurulatih'],
            'objectives': ['objectives', 'objektif', 'matlamat', 'goals']
        })

        # Convert column names to lowercase for matching
        columns_lower = {col.lower(): col for col in df.columns}

        # Try to extract program info from first few rows or column headers
        for field, possible_names in field_mappings.items():
            value = None

            # Method 1: Look for column with matching name
            for name in possible_names:
                if name in columns_lower:
                    col_name = columns_lower[name]
                    # Get first non-null value from this column
                    value = df[col_name].dropna().iloc[0] if not df[col_name].dropna().empty else None
                    if value:
                        program_info[field] = str(value)
                        break

            # Method 2: Look in first column for key-value pairs
            if not value and len(df.columns) >= 2:
                first_col = df.iloc[:, 0].astype(str).str.lower()
                for name in possible_names:
                    mask = first_col.str.contains(name, case=False, na=False)
                    if mask.any():
                        idx = mask.idxmax()
                        value = df.iloc[idx, 1]
                        if pd.notna(value):
                            program_info[field] = str(value)
                            break

        # Set defaults for missing fields
        if 'title' not in program_info:
            program_info['title'] = 'Program Report'
        if 'date' not in program_info:
            program_info['date'] = datetime.now().strftime('%Y-%m-%d')
        if 'location' not in program_info:
            program_info['location'] = 'To Be Confirmed'

        return program_info

    def _extract_participants(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract participant data from DataFrame"""
        participants = []

        # Common column name mappings
        # Common column name mappings
        mappings = self.config.get('participant_mappings', {})
        name_cols = mappings.get('name', ['name', 'nama', 'participant_name', 'student_name', 'full_name'])
        id_cols = mappings.get('id', ['id', 'no', 'participant_id', 'student_id', 'no_peserta', 'bil'])
        gender_cols = mappings.get('gender', ['gender', 'jantina', 'sex'])
        email_cols = mappings.get('email', ['email', 'emel', 'e-mail'])
        phone_cols = mappings.get('phone', ['phone', 'telefon', 'no_telefon', 'contact'])

        # Convert columns to lowercase for matching
        columns_lower = {col.lower(): col for col in df.columns}

        # Find the actual column names
        name_col = self._find_column(columns_lower, name_cols)
        id_col = self._find_column(columns_lower, id_cols)
        gender_col = self._find_column(columns_lower, gender_cols)
        email_col = self._find_column(columns_lower, email_cols)
        phone_col = self._find_column(columns_lower, phone_cols)

        if not name_col:
            logger.warning("⚠️ No participant name column found")
            return participants

        logger.info(f"📋 Found participant columns: name={name_col}, id={id_col}, gender={gender_col}")

        # Extract participant rows
        for idx, row in df.iterrows():
            name = row.get(name_col)

            # Skip empty rows or header rows
            if pd.isna(name) or str(name).lower() in ['name', 'nama', 'participant']:
                continue

            participant = {
                'name': str(name).strip(),
                'id': str(row.get(id_col, idx + 1)) if id_col else str(idx + 1),
                'gender': str(row.get(gender_col, '')).strip() if gender_col else '',
                'email': str(row.get(email_col, '')).strip() if email_col else '',
                'phone': str(row.get(phone_col, '')).strip() if phone_col else ''
            }

            participants.append(participant)

        logger.info(f"✅ Extracted {len(participants)} participants")
        return participants

    def _extract_attendance(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract attendance records from DataFrame"""
        attendance_records = []

        # Look for attendance columns (day 1, day 2, etc.)
        attendance_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
        attendance_config = self.config.get('attendance_mappings', {})
        keywords = attendance_config.get('keywords', ['attendance', 'kehadiran', 'hadir', 'day', 'hari'])
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in keywords):
                attendance_cols.append(col)

        if not attendance_cols:
            logger.info("ℹ️ No attendance columns found")
            return attendance_records

        logger.info(f"📊 Found attendance columns: {attendance_cols}")

        # Get participant ID/name column
        columns_lower = {col.lower(): col for col in df.columns}
        id_col = self._find_column(columns_lower, ['id', 'no', 'participant_id', 'bil'])
        name_col = self._find_column(columns_lower, ['name', 'nama', 'participant_name'])

        # Extract attendance data
        for idx, row in df.iterrows():
            participant_id = row.get(id_col, idx + 1) if id_col else idx + 1
            participant_name = row.get(name_col, '') if name_col else ''

            if pd.isna(participant_name):
                continue

            record = {
                'participant_id': str(participant_id),
                'participant_name': str(participant_name)
            }

            # Add attendance status for each day
            for day_idx, att_col in enumerate(attendance_cols, start=1):
                status = row.get(att_col, '')
                # Normalize status
                if pd.notna(status):
                    status_str = str(status).lower().strip()
                    present_keywords = attendance_config.get('status_present', ['hadir', 'present', 'yes', 'y', '✓', '✔'])
                    is_present = any(keyword in status_str for keyword in present_keywords)
                    record[f'day_{day_idx}_status'] = 'present' if is_present else 'absent'
                else:
                    record[f'day_{day_idx}_status'] = 'absent'

            attendance_records.append(record)

        logger.info(f"✅ Extracted {len(attendance_records)} attendance records")
        return attendance_records

    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics from DataFrame"""
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns)
        }

        # Gender statistics
        columns_lower = {col.lower(): col for col in df.columns}
        gender_col = self._find_column(columns_lower, ['gender', 'jantina', 'sex'])

        if gender_col:
            gender_counts = df[gender_col].value_counts().to_dict()
            gender_stats = self.config.get('gender_statistics', {})
            male_keywords = gender_stats.get('male', ['male', 'lelaki'])
            female_keywords = gender_stats.get('female', ['female', 'perempuan'])
            
            stats['male_count'] = sum(v for k, v in gender_counts.items() if any(m in str(k).lower() for m in male_keywords))
            stats['female_count'] = sum(v for k, v in gender_counts.items() if any(f in str(k).lower() for f in female_keywords))
            stats['total_participants'] = stats['male_count'] + stats['female_count']
        else:
            # Count non-null names
            name_col = self._find_column(columns_lower, ['name', 'nama', 'participant_name'])
            if name_col:
                stats['total_participants'] = df[name_col].notna().sum()

        return stats

    def _find_column(self, columns_lower: Dict[str, str], possible_names: List[str]) -> Optional[str]:
        """Find a column by possible names (case-insensitive)"""
        for name in possible_names:
            if name in columns_lower:
                return columns_lower[name]
        return None


# Create singleton instance
excel_data_extractor = ExcelDataExtractor()
