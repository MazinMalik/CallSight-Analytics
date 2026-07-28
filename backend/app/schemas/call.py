from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator

class CallStatusEnum(str, Enum):
    INTERESTED = "interested"
    ORDERED = "ordered"
    NOT_INTERESTED = "not_interested"
    DID_NOT_PICK = "did_not_pick"
    CALLBACK_REQUESTED = "callback_requested"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    WRONG_NUMBER = "wrong_number"
    UNAVAILABLE = "unavailable"
    UNCLEAR = "unclear"

class ProcessingStatusEnum(str, Enum):
    QUEUED = "queued"
    CONVERTING = "converting"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"

class ExtractedInfoSchema(BaseModel):
    telecaller_name: Optional[str] = None
    company_name: Optional[str] = None
    contact_person_name: Optional[str] = None
    phone_number: Optional[str] = None
    alternate_phone_number: Optional[str] = None
    email: Optional[str] = None
    business_category: Optional[str] = None
    call_status: CallStatusEnum = CallStatusEnum.UNCLEAR
    customer_intent: Optional[str] = None
    products_or_services_discussed: List[str] = Field(default_factory=list)
    order_details: Optional[str] = None
    quantity: Optional[str] = None
    budget_or_price: Optional[str] = None
    follow_up_date: Optional[str] = None  # ISO date string or YYYY-MM-DD
    follow_up_time: Optional[str] = None
    customer_requirements: Optional[str] = None
    objections: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    confidence_score: float = 0.0

class CallCreateResponse(BaseModel):
    call_id: str
    processing_status: str
    message: str = "Audio upload received and queued for processing."

class CallStatusResponse(BaseModel):
    call_id: str
    processing_status: str
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = 0.0
    updated_at: datetime

class CallUpdateSchema(BaseModel):
    telecaller_name: Optional[str] = None
    company_name: Optional[str] = None
    contact_person_name: Optional[str] = None
    phone_number: Optional[str] = None
    alternate_phone_number: Optional[str] = None
    email: Optional[str] = None
    business_category: Optional[str] = None
    call_status: Optional[CallStatusEnum] = None
    customer_intent: Optional[str] = None
    products_or_services_discussed: Optional[List[str]] = None
    order_details: Optional[str] = None
    quantity: Optional[str] = None
    budget_or_price: Optional[str] = None
    follow_up_date: Optional[str] = None
    follow_up_time: Optional[str] = None
    customer_requirements: Optional[str] = None
    objections: Optional[List[str]] = None
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    transcript: Optional[str] = None

class CallDetailSchema(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    
    # Metadata
    telecaller_name: str
    company_name: str
    submitted_phone_number: str
    submitted_category: Optional[str] = None
    submitted_notes: Optional[str] = None
    
    # Audio
    audio_filename: Optional[str] = None
    audio_path: Optional[str] = None
    audio_duration: float = 0.0
    
    # Processing
    processing_status: str
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    
    # Transcript & Extracted details
    transcript: Optional[str] = None
    extracted_json: Optional[Any] = None
    
    contact_person_name: Optional[str] = None
    phone_number: Optional[str] = None
    alternate_phone_number: Optional[str] = None
    email: Optional[str] = None
    business_category: Optional[str] = None
    call_status: Optional[str] = "unclear"
    customer_intent: Optional[str] = None
    products_or_services_discussed: List[str] = Field(default_factory=list)
    order_details: Optional[str] = None
    quantity: Optional[str] = None
    budget_or_price: Optional[str] = None
    follow_up_date: Optional[str] = None
    follow_up_time: Optional[str] = None
    customer_requirements: Optional[str] = None
    objections: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    confidence_score: float = 0.0

    @field_validator("products_or_services_discussed", "objections", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v if x]
        return [str(v)]

    model_config = ConfigDict(from_attributes=True)

class CallListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CallDetailSchema]

class DashboardStatsResponse(BaseModel):
    total_calls: int
    calls_today: int
    interested_leads: int
    orders_confirmed: int
    did_not_pick: int
    follow_ups_required: int
    processing_failures: int
    success_rate: float
    status_distribution: dict
    calls_per_telecaller: dict
    calls_per_category: dict
    calls_per_day: dict
    recent_calls: List[CallDetailSchema]
