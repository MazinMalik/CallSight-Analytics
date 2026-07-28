import csv
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.call import CallRecord

logger = logging.getLogger("csv_exporter")

CSV_COLUMNS = [
    "id",
    "created_at",
    "telecaller_name",
    "company_name",
    "contact_person_name",
    "phone_number",
    "alternate_phone_number",
    "email",
    "business_category",
    "call_status",
    "customer_intent",
    "products_or_services_discussed",
    "order_details",
    "quantity",
    "budget_or_price",
    "follow_up_date",
    "follow_up_time",
    "customer_requirements",
    "objections",
    "summary",
    "confidence_score",
    "transcript",
    "audio_filename",
    "audio_duration",
    "processing_status",
    "processing_time_seconds",
    "error_message"
]

def format_semicolon_list(value) -> str:
    """Formats array or json list into semicolon-separated string."""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return "; ".join(str(item) for item in parsed if item)
            return value
        except Exception:
            return value
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item)
    return str(value)

class CSVExporter:
    def export_calls_to_csv(
        self,
        db: Session,
        output_filepath: Path,
        telecaller_name: Optional[str] = None,
        call_status: Optional[str] = None,
        submitted_category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Path:
        """
        Queries DB for calls matching optional filters and outputs CSV.
        """
        query = db.query(CallRecord)

        if telecaller_name:
            query = query.filter(CallRecord.telecaller_name == telecaller_name)
        if call_status:
            query = query.filter(CallRecord.call_status == call_status)
        if submitted_category:
            query = query.filter(CallRecord.submitted_category == submitted_category)
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

        records: List[CallRecord] = query.order_by(CallRecord.created_at.desc()).all()

        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_file = output_filepath.with_suffix(".tmp")

        with open(temp_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()

            for rec in records:
                row = {
                    "id": rec.id,
                    "created_at": rec.created_at.isoformat() if rec.created_at else "",
                    "telecaller_name": rec.telecaller_name or "",
                    "company_name": rec.company_name or "",
                    "contact_person_name": rec.contact_person_name or "",
                    "phone_number": rec.phone_number or rec.submitted_phone_number or "",
                    "alternate_phone_number": rec.alternate_phone_number or "",
                    "email": rec.email or "",
                    "business_category": rec.business_category or rec.submitted_category or "",
                    "call_status": rec.call_status or "unclear",
                    "customer_intent": rec.customer_intent or "",
                    "products_or_services_discussed": format_semicolon_list(rec.products_or_services_discussed),
                    "order_details": rec.order_details or "",
                    "quantity": rec.quantity or "",
                    "budget_or_price": rec.budget_or_price or "",
                    "follow_up_date": rec.follow_up_date or "",
                    "follow_up_time": rec.follow_up_time or "",
                    "customer_requirements": rec.customer_requirements or "",
                    "objections": format_semicolon_list(rec.objections),
                    "summary": rec.summary or "",
                    "confidence_score": rec.confidence_score or 0.0,
                    "transcript": rec.transcript or "",
                    "audio_filename": rec.audio_filename or "",
                    "audio_duration": rec.audio_duration or 0.0,
                    "processing_status": rec.processing_status or "queued",
                    "processing_time_seconds": rec.processing_time_seconds or 0.0,
                    "error_message": rec.error_message or ""
                }
                writer.writerow(row)

        # Atomic replacement
        temp_file.replace(output_filepath)
        logger.info(f"Exported {len(records)} calls to CSV: {output_filepath}")
        return output_filepath

    def refresh_master_csv(self, db: Session) -> Path:
        """Refreshes default master CSV export file."""
        master_path = settings.abs_export_dir / "master_call_report.csv"
        return self.export_calls_to_csv(db, master_path)

csv_exporter = CSVExporter()
