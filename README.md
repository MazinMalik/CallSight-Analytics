# CallSight Analytics: AI Telecaller Transcription & Extraction System

A complete, production-ready full-stack application for telecaller call recording processing, IndicConformer speech-to-text transcription, Qwen 4B local LLM lead extraction via Ollama, SQLite storage, and CSV reporting.

---

## Architecture Overview

```text
+-------------------------------------------------------------+
|                 Frontend Dashboard (Vercel)                 |
|             React + Vite + TypeScript + Tailwind CSS         |
+------------------------------+------------------------------+
                               | HTTPS API Calls
                               v
+-------------------------------------------------------------+
|           Backend VM (Oracle Cloud Free Tier / Local)        |
|             FastAPI + Uvicorn + SQLAlchemy + SQLite          |
+---------------+------------------------------+--------------+
                |                              |
                v                              v
    +-----------------------+      +-----------------------+
    | Single Queue Worker   |      | Ollama Server         |
    |  - FFmpeg 16kHz Mono  |      |  - Qwen 4B Model      |
    |  - IndicConformer STT |      |  - Temperature 0      |
    +-----------+-----------+      |  - Format: JSON       |
                |                  +-----------+-----------+
                v                              v
    +------------------------------------------------------+
    | SQLite Database & Master CSV Export Synchronization  |
    +------------------------------------------------------+
```

---

## Features

- **Executive Dashboard**: Real-time aggregated KPIs (total calls, today's calls, interested leads, orders confirmed, missed calls, follow-ups required, success rate, status distribution).
- **Audio Upload & Processing**: Drag-and-Drop file browser accepting MP3, WAV, M4A, AAC, OGG, WebM formats (up to 50 MB and 15 mins). Includes live stage progress bar (`queued` -> `converting` -> `transcribing` -> `extracting` -> `saving` -> `completed`).
- **IndicConformer STT Adapter**: Adapter layer integrating AI4Bharat IndicConformer speech-to-text (`AUDIO_AUTOMATION_SYSTEM`).
- **Qwen 4B Lead Extraction**: Sends transcript to local Ollama API to extract structured fields (contact person, phone numbers, email, business category, call status, intent, products, order details, quantity, budget, follow-up date/time, requirements, objections, summary, confidence score).
- **Searchable Calls Directory**: Multi-parameter search and filters (telecaller, call status, business category, processing state, date range).
- **Call Details & Re-processing**: Inspect complete transcripts, edit extracted lead fields inline, rerun Qwen extraction, or re-transcribe original audio.
- **CSV Reporting**: Master CSV generation with atomic file replacement and array serialization into semicolon-separated strings.
- **Decoupled Architecture**: Frontend ready for Vercel deployment; Backend ready for Oracle Cloud Free Tier Ubuntu (ARM64/x86).

---

## Project Directory Structure

```text
c:\Users\malik\OneDrive\Desktop\indian guy project/
├── frontend/                     # React + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/                  # Axios API client & endpoints
│   │   ├── components/           # StatCard, StatusBadge, ProgressBar
│   │   ├── layouts/              # DashboardLayout & Navigation
│   │   ├── pages/                # Overview, Upload, Calls Table, Details, Export, Settings
│   │   ├── types/                # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── vercel.json
├── backend/                      # CallSight Analytics
│   ├── app/
│   │   ├── api/                  # REST endpoints
│   │   ├── core/                 # Config & settings
│   │   ├── database/             # SQLAlchemy engine & session
│   │   ├── models/               # CallRecord database model
│   │   ├── schemas/              # Pydantic schemas & enums
│   │   ├── services/
│   │   │   ├── audio/            # FFmpeg audio normalizer
│   │   │   ├── transcription/    # IndicConformer adapter
│   │   │   ├── extraction/       # Ollama Qwen 4B JSON extractor
│   │   │   └── export/           # CSV exporter
│   │   ├── workers/              # Single-worker background queue
│   │   └── main.py               # FastAPI application entrypoint
│   ├── data/                     # SQLite database storage
│   ├── uploads/                  # Temporary upload files
│   ├── exports/                  # CSV exports
│   ├── tests/                    # Pytest test suite
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── start.sh
├── deploy/                       # Oracle Cloud Deployment Scripts
│   ├── nginx.conf
│   ├── oracle-setup.sh
│   └── README.md
└── README.md
```

---

## Local Development Setup

### 1. Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed
- FFmpeg installed and available on system PATH
- Ollama installed (`https://ollama.com`)

### 2. Ollama & Qwen Model Setup
1. Start Ollama locally:
   ```bash
   ollama serve
   ```
2. Pull the Qwen 4B model:
   ```bash
   ollama pull qwen3:4b
   ```
   *(or `ollama pull qwen:4b` / `ollama pull qwen2.5:3b` depending on local tag)*

### 3. Backend Setup
1. Navigate to `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Run the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 4. Running Backend Tests
```bash
cd backend
python -m pytest
```

### 5. Frontend Setup
1. Navigate to `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
4. Start Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## IndicConformer STT Installation Notes

The transcription service uses the AI4Bharat IndicConformer implementation from:
`https://github.com/Mreeb/AUDIO_AUTOMATION_SYSTEM.git`

To install native PyTorch and IndicConformer dependencies on GPU/CPU production servers:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install git+https://github.com/ai4bharat/IndicConformer.git
```
The backend includes a clean adapter layer `IndicConformerTranscriber` in [indic_conformer.py](file:///c:/Users/malik/OneDrive/Desktop/indian%20guy%20project/backend/app/services/transcription/indic_conformer.py) that automatically handles model loading and fallback modes seamlessly.

---

## Docker Deployment

To run the backend with Docker Compose:
```bash
cd backend
docker-compose up --build -d
```

---

## Production Deployment Guide

### Deploying Frontend to Vercel
1. Push `frontend/` to GitHub repository.
2. In Vercel, select `frontend` as Root Directory.
3. Set Environment Variable:
   `VITE_API_BASE_URL=http://<YOUR_ORACLE_IP>/api`
4. Deploy.

### Deploying Backend to Oracle Cloud Free Tier
1. Copy repository files to Oracle Cloud Ubuntu VM.
2. Execute setup script:
   ```bash
   chmod +x deploy/oracle-setup.sh
   sudo ./deploy/oracle-setup.sh
   ```

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health & Ollama connectivity check |
| `GET` | `/api/stats` | Dashboard metrics & status distribution charts |
| `POST` | `/api/calls` | Upload audio recording & enqueue background job |
| `GET` | `/api/calls` | List call recordings with search & filter |
| `GET` | `/api/calls/{id}` | Get call detail, full transcript & lead fields |
| `PATCH` | `/api/calls/{id}` | Update extracted lead fields |
| `DELETE` | `/api/calls/{id}` | Delete call record and temporary audio |
| `GET` | `/api/calls/{id}/status` | Poll background worker processing stage |
| `POST` | `/api/calls/{id}/reprocess` | Rerun transcript through Qwen extraction |
| `POST` | `/api/calls/{id}/retranscribe` | Rerun audio through IndicConformer |
| `GET` | `/api/export/csv` | Download filtered CSV report |
