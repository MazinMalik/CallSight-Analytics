import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.call import CallRecord
from app.services.audio.audio_preprocessor import audio_preprocessor
from app.services.transcription.indic_conformer import indic_transcriber
from app.services.extraction.qwen_extractor import qwen_extractor
from app.services.export.csv_exporter import csv_exporter

logger = logging.getLogger("job_queue")

class BackgroundJobWorker:
    """
    Asynchronous single-worker queue manager.
    Processes call recordings 1 job at a time to prevent OOM/CPU starvation.
    Automatically recovers queued/stuck jobs on startup.
    """
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running: bool = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts worker loop and recovers any pending queued jobs from SQLite database."""
        if self.is_running:
            return
        self.is_running = True
        self._worker_task = asyncio.create_task(self._process_queue_loop())
        logger.info("Background job processing worker started.")

    def _recover_pending_jobs(self):
        """Finds any calls with status 'queued' or 'processing' and re-enqueues them."""
        db: Session = SessionLocal()
        try:
            pending = db.query(CallRecord).filter(
                CallRecord.processing_status.in_(["queued", "processing"])
            ).order_by(CallRecord.created_at.asc()).all()
            
            for call in pending:
                call.processing_status = "queued"
                call.processing_stage = "Queued for processing"
                self.queue.put_nowait(call.id)
                logger.info(f"Recovered pending job {call.id} into processing queue.")
            db.commit()
        except Exception as err:
            logger.error(f"Error recovering pending jobs on startup: {err}")
        finally:
            db.close()

    async def stop(self):
        """Stops the worker thread gracefully."""
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background job worker stopped.")

    async def enqueue_job(self, call_id: str):
        """Adds a call_id job to the processing queue."""
        await self.queue.put(call_id)
        logger.info(f"Call job {call_id} added to processing queue (Queue size: {self.queue.qsize()}).")

    async def _process_queue_loop(self):
        """Infinite loop consuming jobs from queue."""
        self._recover_pending_jobs()

        while self.is_running:
            try:
                call_id = await self.queue.get()
                logger.info(f"Starting processing for call job: {call_id}")
                
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._process_call_job, call_id)
                
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background worker queue loop: {e}")
                await asyncio.sleep(1)

    def _process_call_job(self, call_id: str):
        """
        Processes call pipeline: Audio Normalization -> Speech Transcription -> Qwen Extraction -> Export.
        """
        db: Session = SessionLocal()
        start_time = time.time()

        try:
            call = db.query(CallRecord).filter(CallRecord.id == call_id).first()
            if not call:
                logger.error(f"Call record {call_id} not found in database.")
                return

            call.processing_status = "processing"
            call.processing_stage = "Normalizing audio waveform"
            db.commit()

            raw_path = Path(call.audio_path)
            norm_path = raw_path.parent / f"{call_id}_norm.wav"

            # Step 1: Audio Normalization
            try:
                audio_preprocessor.convert_to_wav(str(raw_path), str(norm_path))
                target_audio_path = str(norm_path)
            except Exception as norm_err:
                logger.warning(f"Audio normalization warning (using raw file): {norm_err}")
                target_audio_path = str(raw_path)

            # Step 2: Speech-to-Text Transcription via AI4Bharat IndicConformer
            call.processing_stage = "Transcribing speech audio with AI4Bharat IndicConformer"
            db.commit()

            logger.info(f"Transcribing audio file: {target_audio_path}...")
            transcription_res = indic_transcriber.transcribe(
                audio_path=target_audio_path,
                language=settings.DEFAULT_TRANSCRIPTION_LANGUAGE
            )

            call.transcript = transcription_res.text
            call.audio_duration_seconds = transcription_res.duration_seconds
            call.processing_duration_seconds = round(time.time() - start_time, 2)
            db.commit()

            # Step 3: Structured Lead Extraction via Local Qwen LLM
            call.processing_stage = "Extracting business lead details via Qwen LLM"
            db.commit()

            extracted_info = qwen_extractor.extract_lead_info(
                transcript=transcription_res.text,
                telecaller_name=call.telecaller_name,
                company_name=call.company_name,
                submitted_phone_number=call.submitted_phone_number,
                submitted_category=call.submitted_category,
                submitted_notes=call.submitted_notes
            )

            call.contact_person_name = extracted_info.contact_person_name
            call.extracted_phone_number = extracted_info.phone_number
            call.alternate_phone_number = extracted_info.alternate_phone_number
            call.email = extracted_info.email
            call.business_category = extracted_info.business_category or call.submitted_category
            call.call_status = extracted_info.call_status.value
            call.customer_intent = extracted_info.customer_intent
            call.products_or_services_discussed = extracted_info.products_or_services_discussed
            call.order_details = extracted_info.order_details
            call.quantity = extracted_info.quantity
            call.budget_or_price = extracted_info.budget_or_price
            call.follow_up_date = extracted_info.follow_up_date
            call.follow_up_time = extracted_info.follow_up_time
            call.customer_requirements = extracted_info.customer_requirements
            call.objections = extracted_info.objections
            call.summary = extracted_info.summary
            call.confidence_score = extracted_info.confidence_score

            call.processing_status = "completed"
            call.processing_stage = "Completed successfully"
            call.processing_duration_seconds = round(time.time() - start_time, 2)
            db.commit()

            # Step 4: Export Master CSV
            try:
                all_calls = db.query(CallRecord).order_by(CallRecord.created_at.desc()).all()
                csv_exporter.export_calls_to_csv(all_calls)
            except Exception as csv_err:
                logger.error(f"Failed to auto-export CSV report: {csv_err}")

            logger.info(f"Call job {call_id} completed in {call.processing_duration_seconds}s.")

        except Exception as err:
            logger.error(f"Fatal error processing call job {call_id}: {err}", exc_info=True)
            db.rollback()
            failed_call = db.query(CallRecord).filter(CallRecord.id == call_id).first()
            if failed_call:
                failed_call.processing_status = "failed"
                failed_call.error_message = str(err)
                failed_call.processing_stage = "Processing failed"
                failed_call.processing_duration_seconds = round(time.time() - start_time, 2)
                db.commit()
        finally:
            db.close()

job_worker = BackgroundJobWorker()
