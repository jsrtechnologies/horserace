"""
FastAPI main application.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.api.endpoints import races, predictions, scraping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_initial_data():
    """Load historical data on startup if database is empty."""
    db = SessionLocal()
    try:
        from app.models import database
        
        # Check if we already have data
        race_count = db.query(database.Race).count()
        
        if race_count == 0:
            logger.info("No races found in database. Loading historical data...")
            from app.services.scraper.historical_loader import HistoricalDataLoader
            
            loader = HistoricalDataLoader(db)
            stats = loader.load_all_data(days_back=730)  # 2 years
            
            logger.info(f"Historical data loaded: {stats['races_created']} races")
        else:
            logger.info(f"Database already has {race_count} races. Skipping initial load.")
        
        # Add upcoming events (future dates)
        logger.info("Adding upcoming events...")
        from app.services.scraper.historical_loader import HistoricalDataLoader
        
        loader = HistoricalDataLoader(db)
        upcoming_stats = loader.add_upcoming_events(days_forward=30)  # Next 30 days
        
        logger.info(f"Upcoming events added: {upcoming_stats['races_created']} races")
        
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AusRace Predictor AI API")
    init_db()
    logger.info("Database initialized")
    
    # Load initial data in background
    load_initial_data()
    
    yield

    # Shutdown
    logger.info("Shutting down AusRace Predictor AI API")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(races.router)
app.include_router(predictions.router)
app.include_router(scraping.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "AusRace Predictor AI API",
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Mount static files if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")
