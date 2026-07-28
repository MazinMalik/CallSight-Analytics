import os
import uuid
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.config import settings
from app.database.session import get_db
from app.models.call import CallRecord
from app.models.user import User
from app.api.auth import get_current_user
from app.schemas.call import (
    CallCreateResponse, CallStatusResponse, CallDetailSchema, CallListResponse,
    DashboardStatsResponse, CallUpdateSchema, ExtractedInfoSchema, CallStatusEnum
)
from app.services.audio.audio_preprocessor import audio_preprocessor, AudioPreprocessingError
from app.services.extraction.qwen_extractor import qwen_extractor
from app.services.export.csv_exporter import csv_exporter
from app.workers.job_queue import job_worker

router = APIRouter()

def get_call_record_for_user(db: Session, call_id: str, user: User) -> CallRecord:
    query = db.query(CallRecord).filter(CallRecord.id == call_id)
    if user.role == "telecaller":
        query = query.filter(CallRecord.telecaller_id == user.id)
    rec = query.first()
    if not rec:
        raise HTTPException(status_code=404, detail="Call record not found or not accessible.")
    return rec

@router.get("/health")
def health_check():
    """Health check endpoint checking Ollama connectivity."""
    ollama_ok = False
    try:
        res = requests.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=3)
        ollama_ok = (res.status_code == 200)
    except Exception:
        ollama_ok = False

    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "ollama_connected": ollama_ok,
        "ollama_model": settings.OLLAMA_MODEL,
        "transcription_engine": settings.TRANSCRIPTION_ENGINE,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Computes aggregated dashboard statistics, distributions, and charts data."""
    base_query = db.query(CallRecord)
    if current_user.role == "telecaller":
        base_query = base_query.filter(CallRecord.telecaller_id == current_user.id)
        
    total_calls = base_query.count()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = base_query.filter(CallRecord.created_at >= today_start).count()

    interested_leads = base_query.filter(CallRecord.call_status == "interested").count()
    orders_confirmed = base_query.filter(CallRecord.call_status == "ordered").count()
    did_not_pick = base_query.filter(CallRecord.call_status == "did_not_pick").count()
    follow_ups_required = base_query.filter(
        or_(CallRecord.call_status == "follow_up_required", CallRecord.call_status == "callback_requested")
    ).count()
    processing_failures = base_query.filter(CallRecord.processing_status == "failed").count()

    success_rate = round((((total_calls - processing_failures) / total_calls) * 100), 1) if total_calls > 0 else 100.0

    # Status distribution
    status_counts = db.query(CallRecord.call_status, func.count(CallRecord.id))
    if current_user.role == "telecaller":
        status_counts = status_counts.filter(CallRecord.telecaller_id == current_user.id)
    status_counts = status_counts.group_by(CallRecord.call_status).all()
    status_dist = {s or "unclear": count for s, count in status_counts}

    # Telecaller distribution
    tc_counts = db.query(CallRecord.telecaller_name, func.count(CallRecord.id))
    if current_user.role == "telecaller":
        tc_counts = tc_counts.filter(CallRecord.telecaller_id == current_user.id)
    tc_counts = tc_counts.group_by(CallRecord.telecaller_name).all()
    calls_per_tc = {tc or "Telecaller": count for tc, count in tc_counts}

    # Business category distribution
    cat_counts = db.query(CallRecord.business_category, func.count(CallRecord.id))
    if current_user.role == "telecaller":
        cat_counts = cat_counts.filter(CallRecord.telecaller_id == current_user.id)
    cat_counts = cat_counts.group_by(CallRecord.business_category).all()
    calls_per_cat = {cat or "Uncategorized": count for cat, count in cat_counts}

    # Calls per day (last 7 days)
    seven_days_ago = today_start - timedelta(days=6)
    daily_records = base_query.filter(CallRecord.created_at >= seven_days_ago).all()
    calls_per_day = {}
    for i in range(7):
        day_str = (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d")
        calls_per_day[day_str] = 0
    for r in daily_records:
        if r.created_at:
            day_str = r.created_at.strftime("%Y-%m-%d")
            if day_str in calls_per_day:
                calls_per_day[day_str] += 1

    # Recent calls
    recent_records = base_query.order_by(CallRecord.created_at.desc()).limit(5).all()

    return DashboardStatsResponse(
        total_calls=total_calls,
        calls_today=calls_today,
        interested_leads=interested_leads,
        orders_confirmed=orders_confirmed,
        did_not_pick=did_not_pick,
        follow_ups_required=follow_ups_required,
        processing_failures=processing_failures,
        success_rate=success_rate,
        status_distribution=status_dist,
        calls_per_telecaller=calls_per_tc,
        calls_per_category=calls_per_cat,
        calls_per_day=calls_per_day,
        recent_calls=[CallDetailSchema.model_validate(r) for r in recent_records]
    )

@router.post("/calls", response_model=CallCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_call_record(
    company_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validates upload file. Enqueues background job for isolated audio transcription.
    """
    file_bytes = await file.read()
    file_size = len(file_bytes)

    try:
        audio_preprocessor.validate_file(file.filename, file_size)
    except AudioPreprocessingError as err:
        raise HTTPException(status_code=400, detail=str(err))

    call_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    raw_filename = f"{call_id}_raw{ext}"
    raw_filepath = settings.abs_upload_dir / raw_filename

    with open(raw_filepath, "wb") as f:
        f.write(file_bytes)

    call_record = CallRecord(
        id=call_id,
        telecaller_id=current_user.id,
        telecaller_name=current_user.name,
        company_name=company_name.strip() if company_name and company_name.strip() else "Unspecified Company",
        submitted_phone_number=phone_number.strip() if phone_number and phone_number.strip() else "N/A",
        submitted_category=category.strip() if category and category.strip() else None,
        submitted_notes=notes.strip() if notes and notes.strip() else None,
        audio_filename=file.filename,
        audio_path=str(raw_filepath),
        processing_status="queued",
        processing_stage="Queued for processing"
    )

    db.add(call_record)
    db.commit()
    db.refresh(call_record)

    await job_worker.enqueue_job(call_id)

    return CallCreateResponse(
        call_id=call_id,
        processing_status="queued",
        message="Call recording uploaded successfully and queued for isolated transcription and extraction."
    )

@router.get("/calls", response_model=CallListResponse)
def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    telecaller: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    processing_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CallRecord)
    
    if current_user.role == "telecaller":
        query = query.filter(CallRecord.telecaller_id == current_user.id)

    if telecaller and current_user.role == "admin":
        query = query.filter(CallRecord.telecaller_name == telecaller)
    if status:
        query = query.filter(CallRecord.call_status == status)
    if category:
        query = query.filter(CallRecord.submitted_category == category)
    if processing_status:
        query = query.filter(CallRecord.processing_status == processing_status)
    if start_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(CallRecord.created_at >= s_dt)
        except ValueError:
            pass
    if end_date:
        try:
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(CallRecord.created_at <= e_dt)
        except ValueError:
            pass
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CallRecord.telecaller_name.ilike(search_pattern),
                CallRecord.company_name.ilike(search_pattern),
                CallRecord.submitted_phone_number.ilike(search_pattern),
                CallRecord.contact_person_name.ilike(search_pattern),
                CallRecord.summary.ilike(search_pattern)
            )
        )

    total = query.count()
    records = query.order_by(CallRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return CallListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[CallDetailSchema.model_validate(r) for r in records]
    )

@router.get("/calls/{call_id}", response_model=CallDetailSchema)
def get_call_detail(call_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = get_call_record_for_user(db, call_id, current_user)
    return CallDetailSchema.model_validate(rec)

@router.get("/calls/{call_id}/status", response_model=CallStatusResponse)
def get_call_status(call_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = get_call_record_for_user(db, call_id, current_user)
    return CallStatusResponse(
        call_id=rec.id,
        processing_status=rec.processing_status,
        processing_stage=rec.processing_stage,
        error_message=rec.error_message,
        processing_time_seconds=rec.processing_time_seconds,
        updated_at=rec.updated_at
    )

@router.patch("/calls/{call_id}", response_model=CallDetailSchema)
def update_call_record(
    call_id: str,
    update_data: CallUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = get_call_record_for_user(db, call_id, current_user)

    update_dict = update_data.model_dump(exclude_unset=True)
    if "call_status" in update_dict and update_dict["call_status"] is not None:
        update_dict["call_status"] = update_dict["call_status"].value

    for key, value in update_dict.items():
        setattr(rec, key, value)

    rec.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    csv_exporter.refresh_master_csv(db)

    return CallDetailSchema.model_validate(rec)

@router.delete("/calls/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call_record(call_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = get_call_record_for_user(db, call_id, current_user)

    if rec.audio_path and os.path.exists(rec.audio_path):
        try:
            os.remove(rec.audio_path)
        except Exception:
            pass

    db.delete(rec)
    db.commit()
    csv_exporter.refresh_master_csv(db)
    return None

@router.post("/calls/{call_id}/reprocess", response_model=CallStatusResponse)
async def reprocess_call_lead_extraction(call_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = get_call_record_for_user(db, call_id, current_user)
    if not rec.transcript:
        raise HTTPException(status_code=400, detail="Cannot reprocess: transcript is empty.")

    rec.processing_status = "extracting"
    rec.processing_stage = "Reprocessing transcript with Qwen 4B"
    rec.error_message = None
    db.commit()

    extracted = qwen_extractor.extract_lead_info(
        transcript=rec.transcript,
        telecaller_name=rec.telecaller_name or "Telecaller",
        company_name=rec.company_name or "Unspecified Company",
        submitted_phone_number=rec.submitted_phone_number or "N/A",
        submitted_category=rec.submitted_category,
        submitted_notes=rec.submitted_notes
    )

    rec.contact_person_name = extracted.contact_person_name
    rec.phone_number = extracted.phone_number or rec.submitted_phone_number
    rec.alternate_phone_number = extracted.alternate_phone_number
    rec.email = extracted.email
    rec.business_category = extracted.business_category or rec.submitted_category
    rec.call_status = extracted.call_status.value
    rec.customer_intent = extracted.customer_intent
    rec.products_or_services_discussed = extracted.products_or_services_discussed
    rec.order_details = extracted.order_details
    rec.quantity = extracted.quantity
    rec.budget_or_price = extracted.budget_or_price
    rec.follow_up_date = extracted.follow_up_date
    rec.follow_up_time = extracted.follow_up_time
    rec.customer_requirements = extracted.customer_requirements
    rec.objections = extracted.objections
    rec.summary = extracted.summary
    rec.confidence_score = extracted.confidence_score
    rec.extracted_json = extracted.model_dump()
    rec.processing_status = "completed"
    rec.processing_stage = "Reprocessed successfully"

    db.commit()
    csv_exporter.refresh_master_csv(db)

    return CallStatusResponse(
        call_id=rec.id,
        processing_status=rec.processing_status,
        processing_stage=rec.processing_stage,
        error_message=rec.error_message,
        processing_time_seconds=rec.processing_time_seconds,
        updated_at=rec.updated_at
    )

@router.post("/calls/{call_id}/retranscribe", response_model=CallStatusResponse)
async def retranscribe_call_audio(call_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = get_call_record_for_user(db, call_id, current_user)

    raw_path = Path(rec.audio_path) if rec.audio_path else None
    if not raw_path or not raw_path.exists():
        raise HTTPException(status_code=400, detail="Original audio file has been deleted or is not available.")

    rec.processing_status = "queued"
    rec.processing_stage = "Re-queued for transcription"
    db.commit()

    await job_worker.enqueue_job(call_id)

    return CallStatusResponse(
        call_id=rec.id,
        processing_status="queued",
        processing_stage="Re-queued for transcription",
        error_message=None,
        processing_time_seconds=0.0,
        updated_at=rec.updated_at
    )

@router.get("/export/csv")
def download_csv_export(
    telecaller: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "telecaller":
        telecaller = current_user.name

    filename = f"telecaller_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    export_path = settings.abs_export_dir / filename

    csv_exporter.export_calls_to_csv(
        db=db,
        output_filepath=export_path,
        telecaller_name=telecaller,
        call_status=status,
        submitted_category=category,
        start_date=start_date,
        end_date=end_date
    )

    return FileResponse(
        path=export_path,
        filename=filename,
        media_type="text/csv"
    )
