import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import engine, Base
from app.api.endpoints import router as api_router
from app.workers.job_queue import job_worker

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

# Auto-create tables on startup
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager starting background worker and preloading transcription model."""
    logger.info(f"Starting Telecaller API (Env: {settings.APP_ENV})...")
    await job_worker.start()
    yield
    logger.info("Shutting down background worker...")
    await job_worker.stop()

app = FastAPI(
    title="Telecaller Audio Automation API",
    description="Backend API for telecaller call recording transcription (IndicConformer) & lead extraction (Qwen 4B)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
