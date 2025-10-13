"""
Program-related models for production deployment
NO MOCK DATA - All data comes from real forms and user input
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app import db

class Program(db.Model):
    """Real program data - NO MOCK DATA"""
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    organizer = Column(String(255), nullable=False)
    speaker = Column(String(255))
    trainer = Column(String(255))
    facilitator = Column(String(255))
    background = Column(Text)
    objectives = Column(Text)
    requirements = Column(Text)
    capacity = Column(Integer, default=50)
    status = Column(String(20), default='draft')  # draft, active, completed, cancelled
    form_source = Column(String(50))  # google_forms, microsoft_forms
    form_id = Column(String(255))  # External form ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = relationship("Participant", back_populates="program", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="program", cascade="all, delete-orphan")
    form_integrations = relationship("FormIntegration", back_populates="program", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'location': self.location,
            'organizer': self.organizer,
            'speaker': self.speaker,
            'trainer': self.trainer,
            'facilitator': self.facilitator,
            'background': self.background,
            'objectives': self.objectives,
            'capacity': self.capacity,
            'status': self.status,
            'form_source': self.form_source,
            'form_id': self.form_id,
            'participant_count': len(self.participants) if self.participants else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Participant(db.Model):
    """Real participant data - NO MOCK DATA"""
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    full_name = Column(String(255), nullable=False)
    identification_number = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    gender = Column(String(10))
    age = Column(Integer)
    organization = Column(String(255))
    position = Column(String(255))
    department = Column(String(255))
    registration_date = Column(DateTime, default=datetime.utcnow)
    registration_source = Column(String(50))  # google_forms, microsoft_forms, manual
    form_response_id = Column(String(255))  # External response ID
    status = Column(String(20), default='registered')  # registered, confirmed, attended, cancelled
    
    # Additional fields for comprehensive tracking
    address = Column(Text)
    emergency_contact = Column(String(255))
    dietary_requirements = Column(Text)
    special_needs = Column(Text)
    
    # Relationships
    program = relationship("Program", back_populates="participants")
    attendance_records = relationship("AttendanceRecord", back_populates="participant", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'program_id': self.program_id,
            'full_name': self.full_name,
            'identification_number': self.identification_number,
            'email': self.email,
            'phone': self.phone,
            'gender': self.gender,
            'age': self.age,
            'organization': self.organization,
            'position': self.position,
            'department': self.department,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'registration_source': self.registration_source,
            'status': self.status,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'dietary_requirements': self.dietary_requirements,
            'special_needs': self.special_needs
        }

class AttendanceRecord(db.Model):
    """Real attendance tracking - NO MOCK DATA"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participants.id'), nullable=False)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    
    # Multi-day attendance tracking
    day_1_status = Column(String(20), default='absent')  # present, absent, late, excused
    day_2_status = Column(String(20), default='absent')
    day_3_status = Column(String(20), default='absent')
    day_4_status = Column(String(20), default='absent')
    day_5_status = Column(String(20), default='absent')
    
    # Time tracking
    total_hours_attended = Column(Numeric(5, 2), default=0)
    attendance_percentage = Column(Numeric(5, 2), default=0)
    
    # Check-in/out times
    check_in_time_day1 = Column(DateTime)
    check_out_time_day1 = Column(DateTime)
    check_in_time_day2 = Column(DateTime)
    check_out_time_day2 = Column(DateTime)
    check_in_time_day3 = Column(DateTime)
    check_out_time_day3 = Column(DateTime)
    
    # Additional tracking
    notes = Column(Text)
    recorded_by = Column(String(255))  # Who recorded the attendance
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    participant = relationship("Participant", back_populates="attendance_records")
    program = relationship("Program", back_populates="attendance_records")

    def calculate_attendance_percentage(self):
        """Calculate attendance percentage based on program duration"""
        total_days = 0
        attended_days = 0
        
        for day in [self.day_1_status, self.day_2_status, self.day_3_status, 
                   self.day_4_status, self.day_5_status]:
            if day != 'absent':
                total_days += 1
                if day in ['present', 'late']:
                    attended_days += 1
        
        return (attended_days / total_days * 100) if total_days > 0 else 0

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'participant_id': self.participant_id,
            'program_id': self.program_id,
            'day_1_status': self.day_1_status,
            'day_2_status': self.day_2_status,
            'day_3_status': self.day_3_status,
            'day_4_status': self.day_4_status,
            'day_5_status': self.day_5_status,
            'total_hours_attended': float(self.total_hours_attended) if self.total_hours_attended else 0,
            'attendance_percentage': float(self.attendance_percentage) if self.attendance_percentage else 0,
            'notes': self.notes,
            'recorded_by': self.recorded_by,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
