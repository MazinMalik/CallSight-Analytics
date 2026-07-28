import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, Index, JSON
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class CallRecord(Base):
    __tablename__ = "calls"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Metadata submitted at upload (only audio is mandatory, rest optional)
    telecaller_id = Column(String(36), nullable=True, index=True) # Foreign key to User.id (if authenticated)
    telecaller_name = Column(String(255), nullable=True, default="Telecaller", index=True)
    company_name = Column(String(255), nullable=True, default="Unspecified Company", index=True)
    submitted_phone_number = Column(String(50), nullable=True, default="N/A", index=True)
    submitted_category = Column(String(100), nullable=True, index=True)
    submitted_notes = Column(Text, nullable=True)

    # Audio details
    audio_filename = Column(String(255), nullable=True)
    audio_path = Column(String(500), nullable=True)
    audio_duration = Column(Float, nullable=True, default=0.0)

    # Processing state
    processing_status = Column(String(50), nullable=False, default="queued", index=True)
    processing_stage = Column(String(100), nullable=True, default="queued")
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True, default=0.0)

    # Transcription & raw extraction
    transcript = Column(Text, nullable=True)
    extracted_json = Column(JSON, nullable=True)

    # Structured fields extracted by Qwen 4B
    contact_person_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True, index=True)
    alternate_phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    business_category = Column(String(100), nullable=True, index=True)
    
    call_status = Column(String(50), nullable=True, default="unclear", index=True)
    customer_intent = Column(Text, nullable=True)
    products_or_services_discussed = Column(JSON, nullable=True)  # List of strings
    order_details = Column(Text, nullable=True)
    quantity = Column(String(100), nullable=True)
    budget_or_price = Column(String(100), nullable=True)
    
    follow_up_date = Column(String(20), nullable=True, index=True)  # YYYY-MM-DD
    follow_up_time = Column(String(50), nullable=True)
    customer_requirements = Column(Text, nullable=True)
    objections = Column(JSON, nullable=True)  # List of strings
    summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_calls_created_at", "created_at"),
        Index("idx_calls_telecaller_id", "telecaller_id"),
        Index("idx_calls_telecaller", "telecaller_name"),
        Index("idx_calls_company", "company_name"),
        Index("idx_calls_phone", "submitted_phone_number"),
        Index("idx_calls_status", "call_status"),
        Index("idx_calls_category", "submitted_category"),
        Index("idx_calls_followup", "follow_up_date"),
        Index("idx_calls_proc_status", "processing_status"),
    )
