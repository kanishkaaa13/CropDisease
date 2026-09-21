from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, farmer, officer, admin, scan, risk, advisory, pest_trap, pipeline, chat
from app.db.connection import engine, Base

# Create all tables on startup (if database is reachable)
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    import logging
    logging.getLogger("main").warning("Database connection failed on startup (%s). Tables not auto-created.", exc)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="KrushiRakshak AI",
    description="AI-powered crop disease detection and advisory system for Indian farmers",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Static media uploads directory for scan images
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
(uploads_dir / "scans").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api")
app.include_router(scan.router, prefix="/api", tags=["AI Scan"])
app.include_router(risk.router, prefix="/api", tags=["Risk Engine"])
app.include_router(advisory.router, prefix="/api", tags=["Agronomic Advisory"])
app.include_router(farmer.router, prefix="/api/farmer", tags=["Farmer"])
app.include_router(officer.router, prefix="/api/officer", tags=["Officer"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(pest_trap.router, prefix="/api", tags=["Pest Trap"])
app.include_router(pipeline.router, prefix="/api", tags=["Full Pipeline"])
app.include_router(chat.router, prefix="/api", tags=["Farmer Officer Chat"])
app.include_router(chat.ws_router, tags=["Farmer Officer Chat"])
