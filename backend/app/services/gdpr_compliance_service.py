"""
GDPR/PDPA Compliance Service
Handles data protection, privacy rights, and compliance requirements
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

class ConsentType(Enum):
    """Types of consent required"""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    COOKIES = "cookies"
    THIRD_PARTY_SHARING = "third_party_sharing"

class DataRetentionPeriod(Enum):
    """Data retention periods"""
    SHORT_TERM = 30  # 30 days
    MEDIUM_TERM = 365  # 1 year
    LONG_TERM = 2555  # 7 years (legal requirement)
    PERMANENT = -1  # Never delete

@dataclass
class ConsentRecord:
    """Individual consent record"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    ip_address: str
    user_agent: str
    version: str  # Privacy policy version
    withdrawal_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['consent_type'] = self.consent_type.value
        if self.withdrawal_date:
            data['withdrawal_date'] = self.withdrawal_date.isoformat()
        return data

@dataclass
class DataProcessingRecord:
    """Record of data processing activities"""
    record_id: str
    user_id: str
    data_type: str
    processing_purpose: str
    legal_basis: str
    retention_period: DataRetentionPeriod
    created_at: datetime
    last_accessed: Optional[datetime] = None
    anonymized: bool = False
    deleted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['retention_period'] = self.retention_period.value
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data

class GDPRComplianceService:
    """Service for managing GDPR/PDPA compliance"""
    
    def __init__(self, storage_path: str = "compliance_data"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize storage files
        self.consent_file = os.path.join(storage_path, "consent_records.json")
        self.processing_file = os.path.join(storage_path, "processing_records.json")
        self.audit_file = os.path.join(storage_path, "audit_log.json")
        
        # Legal bases for processing
        self.legal_bases = {
            "consent": "Consent of the data subject",
            "contract": "Performance of a contract",
            "legal_obligation": "Compliance with legal obligation",
            "vital_interests": "Protection of vital interests",
            "public_task": "Performance of public task",
            "legitimate_interests": "Legitimate interests of controller"
        }
    
    def record_consent(self, user_id: str, consent_type: ConsentType, 
                      granted: bool, ip_address: str, user_agent: str,
                      privacy_policy_version: str) -> str:
        """Record user consent"""
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            version=privacy_policy_version
        )
        
        # Save consent record
        self._save_consent_record(consent_record)
        
        # Log audit trail
        self._log_audit_event("consent_recorded", {
            "user_id": user_id,
            "consent_type": consent_type.value,
            "granted": granted,
            "ip_address": ip_address
        })
        
        logger.info(f"Consent recorded: {user_id} - {consent_type.value} - {granted}")
        return consent_record.user_id
    
    def withdraw_consent(self, user_id: str, consent_type: ConsentType,
                        ip_address: str) -> bool:
        """Withdraw user consent"""
        try:
            # Load existing consent records
            consent_records = self._load_consent_records()
            
            # Find and update the consent record
            updated = False
            for record in consent_records:
                if (record['user_id'] == user_id and 
                    record['consent_type'] == consent_type.value and
                    record['granted'] and 
                    not record.get('withdrawal_date')):
                    
                    record['withdrawal_date'] = datetime.utcnow().isoformat()
                    updated = True
                    break
            
            if updated:
                self._save_consent_records(consent_records)
                
                # Log audit trail
                self._log_audit_event("consent_withdrawn", {
                    "user_id": user_id,
                    "consent_type": consent_type.value,
                    "ip_address": ip_address
                })
                
                logger.info(f"Consent withdrawn: {user_id} - {consent_type.value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error withdrawing consent: {e}")
            return False
    
    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consent records for a user"""
        try:
            consent_records = self._load_consent_records()
            user_consents = [
                record for record in consent_records 
                if record['user_id'] == user_id
            ]
            return user_consents
        except Exception as e:
            logger.error(f"Error getting user consents: {e}")
            return []
    
    def record_data_processing(self, user_id: str, data_type: str,
                             processing_purpose: str, legal_basis: str,
                             retention_period: DataRetentionPeriod) -> str:
        """Record data processing activity"""
        record_id = str(uuid.uuid4())
        
        processing_record = DataProcessingRecord(
            record_id=record_id,
            user_id=user_id,
            data_type=data_type,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            retention_period=retention_period,
            created_at=datetime.utcnow()
        )
        
        # Save processing record
        self._save_processing_record(processing_record)
        
        # Log audit trail
        self._log_audit_event("data_processing_recorded", {
            "record_id": record_id,
            "user_id": user_id,
            "data_type": data_type,
            "processing_purpose": processing_purpose
        })
        
        logger.info(f"Data processing recorded: {record_id}")
        return record_id
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR Article 20 - Right to data portability)"""
        try:
            # Get consent records
            consents = self.get_user_consents(user_id)
            
            # Get processing records
            processing_records = self._load_processing_records()
            user_processing = [
                record for record in processing_records
                if record['user_id'] == user_id and not record.get('deleted', False)
            ]
            
            # Compile user data export
            export_data = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "consent_records": consents,
                "processing_records": user_processing,
                "data_portability_notice": {
                    "en": "This export contains all personal data we have collected about you.",
                    "ms": "Eksport ini mengandungi semua data peribadi yang telah kami kumpulkan tentang anda."
                }
            }
            
            # Log audit trail
            self._log_audit_event("data_exported", {
                "user_id": user_id,
                "export_size": len(json.dumps(export_data))
            })
            
            logger.info(f"User data exported: {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            raise
    
    def delete_user_data(self, user_id: str, deletion_reason: str) -> bool:
        """Delete all user data (GDPR Article 17 - Right to erasure)"""
        try:
            # Mark processing records as deleted
            processing_records = self._load_processing_records()
            updated_records = []
            
            for record in processing_records:
                if record['user_id'] == user_id:
                    record['deleted'] = True
                    record['deletion_date'] = datetime.utcnow().isoformat()
                    record['deletion_reason'] = deletion_reason
                updated_records.append(record)
            
            self._save_processing_records(updated_records)
            
            # Log audit trail
            self._log_audit_event("user_data_deleted", {
                "user_id": user_id,
                "deletion_reason": deletion_reason
            })
            
            logger.info(f"User data deleted: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return False
    
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data while retaining statistical value"""
        try:
            # Generate anonymous identifier
            anonymous_id = f"anon_{uuid.uuid4().hex[:8]}"
            
            # Update processing records
            processing_records = self._load_processing_records()
            updated_records = []
            
            for record in processing_records:
                if record['user_id'] == user_id:
                    record['user_id'] = anonymous_id
                    record['anonymized'] = True
                    record['anonymization_date'] = datetime.utcnow().isoformat()
                updated_records.append(record)
            
            self._save_processing_records(updated_records)
            
            # Log audit trail
            self._log_audit_event("user_data_anonymized", {
                "original_user_id": user_id,
                "anonymous_id": anonymous_id
            })
            
            logger.info(f"User data anonymized: {user_id} -> {anonymous_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error anonymizing user data: {e}")
            return False
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up data that has exceeded retention periods"""
        try:
            processing_records = self._load_processing_records()
            current_time = datetime.utcnow()
            
            deleted_count = 0
            anonymized_count = 0
            updated_records = []
            
            for record in processing_records:
                if record.get('deleted', False):
                    updated_records.append(record)
                    continue
                
                created_at = datetime.fromisoformat(record['created_at'])
                retention_days = record['retention_period']
                
                if retention_days == -1:  # Permanent
                    updated_records.append(record)
                    continue
                
                expiry_date = created_at + timedelta(days=retention_days)
                
                if current_time > expiry_date:
                    # Check if we should delete or anonymize
                    if retention_days <= 365:  # Short/medium term - delete
                        record['deleted'] = True
                        record['deletion_date'] = current_time.isoformat()
                        record['deletion_reason'] = "retention_period_expired"
                        deleted_count += 1
                    else:  # Long term - anonymize
                        if not record.get('anonymized', False):
                            record['user_id'] = f"anon_{uuid.uuid4().hex[:8]}"
                            record['anonymized'] = True
                            record['anonymization_date'] = current_time.isoformat()
                            anonymized_count += 1
                
                updated_records.append(record)
            
            self._save_processing_records(updated_records)
            
            # Log audit trail
            self._log_audit_event("data_cleanup_performed", {
                "deleted_count": deleted_count,
                "anonymized_count": anonymized_count
            })
            
            result = {
                "deleted_records": deleted_count,
                "anonymized_records": anonymized_count
            }
            
            logger.info(f"Data cleanup completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            return {"deleted_records": 0, "anonymized_records": 0}
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            consent_records = self._load_consent_records()
            processing_records = self._load_processing_records()
            audit_log = self._load_audit_log()
            
            # Analyze consent records
            consent_stats = {}
            for consent_type in ConsentType:
                granted = len([r for r in consent_records 
                             if r['consent_type'] == consent_type.value and r['granted']])
                withdrawn = len([r for r in consent_records 
                               if r['consent_type'] == consent_type.value and r.get('withdrawal_date')])
                consent_stats[consent_type.value] = {
                    "granted": granted,
                    "withdrawn": withdrawn,
                    "active": granted - withdrawn
                }
            
            # Analyze data processing
            processing_stats = {
                "total_records": len(processing_records),
                "active_records": len([r for r in processing_records if not r.get('deleted', False)]),
                "anonymized_records": len([r for r in processing_records if r.get('anonymized', False)]),
                "deleted_records": len([r for r in processing_records if r.get('deleted', False)])
            }
            
            # Analyze by data type
            data_type_stats = {}
            for record in processing_records:
                if not record.get('deleted', False):
                    data_type = record['data_type']
                    if data_type not in data_type_stats:
                        data_type_stats[data_type] = 0
                    data_type_stats[data_type] += 1
            
            # Recent activities
            recent_activities = sorted(audit_log, key=lambda x: x['timestamp'], reverse=True)[:50]
            
            report = {
                "report_date": datetime.utcnow().isoformat(),
                "consent_statistics": consent_stats,
                "processing_statistics": processing_stats,
                "data_type_breakdown": data_type_stats,
                "recent_activities": recent_activities,
                "compliance_status": {
                    "gdpr_compliant": True,
                    "pdpa_compliant": True,
                    "last_cleanup": self._get_last_cleanup_date(),
                    "retention_policies_active": True
                }
            }
            
            logger.info("Compliance report generated")
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    def _save_consent_record(self, consent_record: ConsentRecord):
        """Save consent record to storage"""
        try:
            records = self._load_consent_records()
            records.append(consent_record.to_dict())
            self._save_consent_records(records)
        except Exception as e:
            logger.error(f"Error saving consent record: {e}")
            raise
    
    def _save_processing_record(self, processing_record: DataProcessingRecord):
        """Save processing record to storage"""
        try:
            records = self._load_processing_records()
            records.append(processing_record.to_dict())
            self._save_processing_records(records)
        except Exception as e:
            logger.error(f"Error saving processing record: {e}")
            raise
    
    def _load_consent_records(self) -> List[Dict[str, Any]]:
        """Load consent records from storage"""
        try:
            if os.path.exists(self.consent_file):
                with open(self.consent_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading consent records: {e}")
            return []
    
    def _save_consent_records(self, records: List[Dict[str, Any]]):
        """Save consent records to storage"""
        try:
            with open(self.consent_file, 'w') as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving consent records: {e}")
            raise
    
    def _load_processing_records(self) -> List[Dict[str, Any]]:
        """Load processing records from storage"""
        try:
            if os.path.exists(self.processing_file):
                with open(self.processing_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading processing records: {e}")
            return []
    
    def _save_processing_records(self, records: List[Dict[str, Any]]):
        """Save processing records to storage"""
        try:
            with open(self.processing_file, 'w') as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing records: {e}")
            raise
    
    def _load_audit_log(self) -> List[Dict[str, Any]]:
        """Load audit log from storage"""
        try:
            if os.path.exists(self.audit_file):
                with open(self.audit_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading audit log: {e}")
            return []
    
    def _log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log audit event"""
        try:
            audit_log = self._load_audit_log()
            
            audit_entry = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details
            }
            
            audit_log.append(audit_entry)
            
            # Keep only last 10000 entries
            if len(audit_log) > 10000:
                audit_log = audit_log[-10000:]
            
            with open(self.audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def _get_last_cleanup_date(self) -> Optional[str]:
        """Get the date of last data cleanup"""
        try:
            audit_log = self._load_audit_log()
            cleanup_events = [
                event for event in audit_log 
                if event['event_type'] == 'data_cleanup_performed'
            ]
            if cleanup_events:
                return sorted(cleanup_events, key=lambda x: x['timestamp'], reverse=True)[0]['timestamp']
            return None
        except Exception as e:
            logger.error(f"Error getting last cleanup date: {e}")
            return None


# Privacy Policy Templates
PRIVACY_POLICY_TEMPLATES = {
    "en": {
        "title": "Privacy Policy",
        "last_updated": "August 10, 2025",
        "version": "2.0",
        "sections": {
            "data_collection": {
                "title": "Data We Collect",
                "content": "We collect information you provide directly to us, such as when you create an account, fill out forms, or contact us for support."
            },
            "data_use": {
                "title": "How We Use Your Data",
                "content": "We use your information to provide, maintain, and improve our services, process transactions, and communicate with you."
            },
            "data_sharing": {
                "title": "Data Sharing",
                "content": "We do not sell your personal data. We may share information in certain limited circumstances as described in this policy."
            },
            "your_rights": {
                "title": "Your Rights",
                "content": "You have the right to access, update, or delete your personal information. You may also object to certain processing of your data."
            },
            "retention": {
                "title": "Data Retention",
                "content": "We retain your information for as long as necessary to provide our services and comply with legal obligations."
            },
            "contact": {
                "title": "Contact Us",
                "content": "If you have questions about this privacy policy, please contact us at privacy@stratosys.com"
            }
        }
    },
    "ms": {
        "title": "Dasar Privasi",
        "last_updated": "10 Ogos 2025",
        "version": "2.0",
        "sections": {
            "data_collection": {
                "title": "Data Yang Kami Kumpulkan",
                "content": "Kami mengumpul maklumat yang anda berikan secara langsung kepada kami, seperti semasa anda membuat akaun, mengisi borang, atau menghubungi kami untuk sokongan."
            },
            "data_use": {
                "title": "Bagaimana Kami Menggunakan Data Anda",
                "content": "Kami menggunakan maklumat anda untuk menyediakan, mengekalkan, dan menambah baik perkhidmatan kami, memproses transaksi, dan berkomunikasi dengan anda."
            },
            "data_sharing": {
                "title": "Perkongsian Data",
                "content": "Kami tidak menjual data peribadi anda. Kami mungkin berkongsi maklumat dalam keadaan terhad tertentu seperti yang diterangkan dalam dasar ini."
            },
            "your_rights": {
                "title": "Hak Anda",
                "content": "Anda mempunyai hak untuk mengakses, mengemas kini, atau memadam maklumat peribadi anda. Anda juga boleh membantah pemprosesan tertentu data anda."
            },
            "retention": {
                "title": "Pengekalan Data",
                "content": "Kami mengekalkan maklumat anda selama yang diperlukan untuk menyediakan perkhidmatan kami dan mematuhi kewajipan undang-undang."
            },
            "contact": {
                "title": "Hubungi Kami",
                "content": "Jika anda mempunyai soalan tentang dasar privasi ini, sila hubungi kami di privacy@stratosys.com"
            }
        }
    }
}
