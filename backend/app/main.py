import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.api import endpoints, auth, users
from app.models.user import User
from app.core import security
from app.workers.job_queue import job_worker

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(endpoints.router, prefix="/api")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.login_id == "admin").first()
        if not admin:
            admin = User(
                login_id="admin",
                name="System Administrator",
                hashed_password=security.get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created (admin / admin123)")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
