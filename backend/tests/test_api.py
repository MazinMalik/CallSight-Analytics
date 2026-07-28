import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.services.audio.audio_preprocessor import audio_preprocessor, AudioPreprocessingError
from app.services.extraction.qwen_extractor import qwen_extractor
from app.schemas.call import CallStatusEnum, ExtractedInfoSchema
from app.services.export.csv_exporter import csv_exporter

# Setup test DB
TEST_DB_URL = "sqlite:///./test_telecaller.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_telecaller.db"):
        try:
            os.remove("test_telecaller.db")
        except Exception:
            pass

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_upload_validation_invalid_format():
    with pytest.raises(AudioPreprocessingError):
        audio_preprocessor.validate_file("document.pdf", 1024)

def test_qwen_json_parsing_valid():
    raw_json = """
    {
      "telecaller_name": "Rohan",
      "company_name": "Test Company",
      "contact_person_name": "Amit",
      "phone_number": "+919876543210",
      "call_status": "interested",
      "products_or_services_discussed": ["ERP System"],
      "objections": ["High price"],
      "summary": "Interested in ERP system.",
      "confidence_score": 0.95
    }
    """
    res = qwen_extractor._parse_and_validate_json(
        raw_text=raw_json,
        default_telecaller="Rohan",
        default_company="Test Company",
        default_phone="+919876543210",
        default_category="Software"
    )
    assert res.call_status == CallStatusEnum.INTERESTED
    assert res.products_or_services_discussed == ["ERP System"]
    assert res.objections == ["High price"]
    assert res.confidence_score == 0.95

def test_qwen_invalid_status_fallback():
    raw_json = """
    {
      "call_status": "invalid_status_string"
    }
    """
    res = qwen_extractor._parse_and_validate_json(
        raw_text=raw_json,
        default_telecaller="Rohan",
        default_company="Test Company",
        default_phone="+919876543210",
        default_category=None
    )
    assert res.call_status == CallStatusEnum.UNCLEAR

@patch("app.workers.job_queue.job_worker.enqueue_job")
def test_upload_call_api(mock_enqueue):
    audio_content = b"RIFF....WAVEfmt ....data...."
    response = client.post(
        "/api/calls",
        data={
            "telecaller_name": "Priya",
            "company_name": "Acme Corp",
            "phone_number": "9876543210",
            "category": "Real Estate",
            "notes": "Testing upload API"
        },
        files={"file": ("test.wav", audio_content, "audio/wav")}
    )
    assert response.status_code == 202
    data = response.json()
    assert "call_id" in data
    assert data["processing_status"] == "queued"
    assert mock_enqueue.called

def test_get_stats_empty():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_calls"] == 0
    assert data["success_rate"] == 100.0
