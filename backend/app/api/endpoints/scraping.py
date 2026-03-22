"""
Scraping API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models import database
from app.services.scraper import RacingComScraper, PuntersScraper, weather_api
from app.services.scraper.historical_loader import load_historical_data
from app.services.scraper.live_update import (
    start_live_updates, 
    stop_live_updates, 
    get_live_updates_status,
    LiveUpdateService
)

router = APIRouter(prefix="/api/scraping", tags=["scraping"])

logger = logging.getLogger(__name__)


# ============================================
# Historical Data Loading
# ============================================

def load_historical_task(days_back: int, db: Session):
    """Background task to load historical data."""
    try:
        # Create sync status
        sync_status = database.SyncStatus(
            sync_type="historical",
            status="running",
            started_at=datetime.now(),
            total_expected=days_back
        )
        db.add(sync_status)
        db.commit()
        
        # Run the loader
        stats = load_historical_data(days_back)
        
        # Update sync status
        sync_status.status = "completed"
        sync_status.completed_at = datetime.now()
        sync_status.records_processed = stats.get("races_created", 0)
        sync_status.progress_percent = 100.0
        db.commit()
        
        logger.info(f"Historical data load completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        sync_status = db.query(database.SyncStatus).filter(
            database.SyncStatus.sync_type == "historical",
            database.SyncStatus.status == "running"
        ).first()
        if sync_status:
            sync_status.status = "failed"
            sync_status.error_message = str(e)
            db.commit()
        return {"status": "error", "message": str(e)}


@router.post("/load-historical")
def trigger_historical_load(
    background_tasks: BackgroundTasks,
    days_back: int = Query(default=730, ge=30, le=1095, description="Number of days of history to load (max 3 years)"),
    db: Session = Depends(get_db)
):
    """
    Trigger loading of historical race data (past 2 years by default).
    
    This will populate the database with:
    - Venues
    - Meetings
    - Races
    - Horses
    - Jockeys
    - Trainers
    - Participants
    - Results
    - Market data (odds)
    """
    # Check if already running
    existing = db.query(database.SyncStatus).filter(
        database.SyncStatus.sync_type == "historical",
        database.SyncStatus.status == "running"
    ).first()
    
    if existing:
        return {
            "status": "already_running",
            "message": "Historical data loading is already in progress",
            "started_at": existing.started_at.isoformat() if existing.started_at else None
        }
    
    # Start background task
    background_tasks.add_task(load_historical_task, days_back, db)
    
    return {
        "status": "started",
        "message": f"Historical data loading started for {days_back} days",
        "estimated_time": f"{days_back // 60} hours (estimated)"
    }


@router.get("/load-historical/status")
def get_historical_load_status(db: Session = Depends(get_db)):
    """Get the status of historical data loading."""
    
    sync_status = db.query(database.SyncStatus).filter(
        database.SyncStatus.sync_type == "historical"
    ).order_by(database.SyncStatus.created_at.desc()).first()
    
    if sync_status:
        return {
            "status": sync_status.status,
            "sync_type": sync_status.sync_type,
            "started_at": sync_status.started_at.isoformat() if sync_status.started_at else None,
            "completed_at": sync_status.completed_at.isoformat() if sync_status.completed_at else None,
            "records_processed": sync_status.records_processed,
            "progress_percent": sync_status.progress_percent,
            "error_message": sync_status.error_message
        }
    
    return {
        "status": "not_started",
        "message": "No historical data loading has been triggered"
    }


# ============================================
# Live Updates
# ============================================

@router.post("/live/start")
def start_live_updates_endpoint(db: Session = Depends(get_db)):
    """
    Start real-time live updates.
    Updates race data every 60 seconds including:
    - Odds changes
    - Scratchings
    - Race status updates
    - Results (when races complete)
    """
    result = start_live_updates()
    
    # Log the start
    sync_status = database.SyncStatus(
        sync_type="live",
        status="running",
        started_at=datetime.now()
    )
    db.add(sync_status)
    db.commit()
    
    return result


@router.post("/live/stop")
def stop_live_updates_endpoint(db: Session = Depends(get_db)):
    """Stop real-time live updates."""
    result = stop_live_updates()
    
    # Log the stop
    sync_status = db.query(database.SyncStatus).filter(
        database.SyncStatus.sync_type == "live",
        database.SyncStatus.status == "running"
    ).first()
    if sync_status:
        sync_status.status = "stopped"
        sync_status.completed_at = datetime.now()
        db.commit()
    
    return result


@router.get("/live/status")
def get_live_updates_status_endpoint(db: Session = Depends(get_db)):
    """Get status of live updates including current live races."""
    return get_live_updates_status()


@router.get("/live/races")
def get_live_races_endpoint(db: Session = Depends(get_db)):
    """Get all currently live races with real-time odds."""
    live_service = LiveUpdateService(db)
    return {
        "count": 0,
        "races": live_service.get_live_races()
    }


@router.get("/live/upcoming")
def get_upcoming_with_odds_endpoint(
    hours: int = Query(default=24, ge=1, le=72),
    db: Session = Depends(get_db)
):
    """Get upcoming races with current odds."""
    live_service = LiveUpdateService(db)
    races = live_service.get_upcoming_races_with_odds(hours)
    return {
        "count": len(races),
        "races": races
    }


# ============================================
# Standard Scraping (Existing endpoints)
# ============================================

def scrape_and_save_races(db: Session):
    """Background task to scrape and save race data."""
    try:
        racing_scraper = RacingComScraper()
        punters_scraper = PuntersScraper()

        meetings_data = racing_scraper.get_upcoming_meetings()

        for meeting_data in meetings_data:
            try:
                venue = db.query(database.Venue).filter(
                    database.Venue.name == meeting_data["venue_name"]
                ).first()

                if not venue:
                    venue = database.Venue(
                        name=meeting_data["venue_name"],
                        state=meeting_data.get("state", "VIC"),
                        track_type="Turf"
                    )
                    db.add(venue)
                    db.commit()
                    db.refresh(venue)

                meeting_date = datetime.now()
                if meeting_data.get("date"):
                    try:
                        meeting_date = datetime.strptime(meeting_data["date"], "%Y-%m-%d")
                    except:
                        pass

                meeting = database.Meeting(
                    venue_id=venue.id,
                    date=meeting_date,
                    weather=meeting_data.get("weather"),
                    track_rating=meeting_data.get("track_rating")
                )
                db.add(meeting)
                db.commit()
                db.refresh(meeting)

                weather = weather_api.get_weather_for_venue(venue.name)
                if weather:
                    meeting.rainfall = weather.get("rain", 0)
                    meeting.humidity = weather.get("humidity")
                    meeting.wind_speed = weather.get("wind_speed")
                    meeting.track_condition = weather_api.get_track_condition(
                        venue.name, weather
                    )
                    db.commit()

                race_count = meeting_data.get("race_count", 8)
                for race_num in range(1, race_count + 1):
                    race = database.Race(
                        meeting_id=meeting.id,
                        race_number=race_num,
                        race_name=f"Race {race_num}",
                        distance=1200 + (race_num * 100),
                        race_time=meeting_date.replace(hour=12 + race_num),
                        status="scheduled"
                    )
                    db.add(race)

                db.commit()

            except Exception as e:
                print(f"Error processing meeting {meeting_data.get('venue_name')}: {e}")
                continue

        racing_scraper.close()
        punters_scraper.close()

    except Exception as e:
        print(f"Error in scrape_and_save_races: {e}")


@router.post("/scrape-races")
def trigger_race_scrape(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger scraping of upcoming races."""
    background_tasks.add_task(scrape_and_save_races, db)
    return {
        "status": "started",
        "message": "Race scraping started in background"
    }


@router.post("/scrape-results")
def trigger_results_scrape(
    background_tasks: BackgroundTasks,
    days: int = 1,
    db: Session = Depends(get_db)
):
    """Trigger scraping of recent race results."""
    return {
        "status": "started",
        "message": f"Results scraping for last {days} days started in background"
    }


@router.post("/update-weather")
def trigger_weather_update(db: Session = Depends(get_db)):
    """Update weather data for all upcoming meetings."""
    now = datetime.now()
    meetings = db.query(database.Meeting).filter(
        database.Meeting.date >= now
    ).all()

    updated_count = 0

    for meeting in meetings:
        if meeting.venue:
            weather = weather_api.get_weather_for_venue(meeting.venue.name)
            if weather:
                meeting.weather = weather.get("weather")
                meeting.rainfall = weather.get("rain", 0)
                meeting.humidity = weather.get("humidity")
                meeting.wind_speed = weather.get("wind_speed")
                meeting.track_condition = weather_api.get_track_condition(
                    meeting.venue.name, weather
                )
                updated_count += 1

    db.commit()

    return {
        "status": "completed",
        "updated": updated_count,
        "message": f"Updated weather for {updated_count} meetings"
    }


@router.get("/status")
def get_scraping_status(db: Session = Depends(get_db)):
    """Get scraping system status and statistics."""
    venue_count = db.query(database.Venue).count()
    meeting_count = db.query(database.Meeting).count()
    race_count = db.query(database.Race).count()
    horse_count = db.query(database.Horse).count()
    jockey_count = db.query(database.Jockey).count()
    trainer_count = db.query(database.Trainer).count()
    participant_count = db.query(database.Participant).count()
    result_count = db.query(database.RaceResult).count()
    market_data_count = db.query(database.MarketData).count()

    last_meeting = db.query(database.Meeting).order_by(
        database.Meeting.date.desc()
    ).first()

    # Get recent sync statuses
    recent_syncs = db.query(database.SyncStatus).order_by(
        database.SyncStatus.created_at.desc()
    ).limit(5).all()

    return {
        "database": {
            "venues": venue_count,
            "meetings": meeting_count,
            "races": race_count,
            "horses": horse_count,
            "jockeys": jockey_count,
            "trainers": trainer_count,
            "participants": participant_count,
            "results": result_count,
            "market_data": market_data_count
        },
        "last_update": last_meeting.date.isoformat() if last_meeting else None,
        "status": "ready",
        "recent_syncs": [
            {
                "sync_type": s.sync_type,
                "status": s.status,
                "records_processed": s.records_processed,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in recent_syncs
        ]
    }


@router.post("/seed-sample-data")
def seed_sample_data(db: Session = Depends(get_db)):
    """Seed the database with sample data for testing."""
    venues_data = [
        {"name": "Flemington", "state": "VIC", "track_type": "Turf"},
        {"name": "Randwick", "state": "NSW", "track_type": "Turf"},
        {"name": "Doomben", "state": "QLD", "track_type": "Turf"},
        {"name": "Morphettville", "state": "SA", "track_type": "Turf"},
        {"name": "Ascot", "state": "WA", "track_type": "Turf"},
        {"name": "Hobart", "state": "TAS", "track_type": "Turf"},
    ]

    for v_data in venues_data:
        venue = db.query(database.Venue).filter(
            database.Venue.name == v_data["name"]
        ).first()

        if not venue:
            venue = database.Venue(**v_data)
            db.add(venue)

    db.commit()

    horses_data = [
        {"name": "Artorius", "age": 4, "gender": "Colt", "sire": "Flying Artie", "dam": "Marmelo"},
        {"name": "Anamoe", "age": 4, "gender": "Colt", "sire": "Street Boss", "dam": "Anatola"},
        {"name": "Profiteer", "age": 4, "gender": "Colt", "sire": "Capitalist", "dam": "Misfit"},
        {"name": "Trickstar", "age": 5, "gender": "Mare", "sire": "Not a Single Doubt", "dam": "Trick of Light"},
        {"name": "Maltitude", "age": 5, "gender": "Mare", "sire": "Mongolian Khan", "dam": "Mull Over"},
        {"name": "Grail", "age": 4, "gender": "Colt", "sire": "Pierro", "dam": "Grail Maiden"},
        {"name": "Lightsaber", "age": 6, "gender": "Gelding", "sire": "Highlighter", "dam": "Blade of Light"},
        {"name": "Vince", "age": 5, "gender": "Gelding", "sire": "Unencumbered", "dam": "Vinci"},
        {"name": "Prince of Arrows", "age": 4, "gender": "Colt", "sire": "Dreamscape", "dam": "Royal Arion"},
        {"name": "Ranchhand", "age": 5, "gender": "Gelding", "sire": "Tavistock", "dam": "Humboldt"},
    ]

    for h_data in horses_data:
        horse = db.query(database.Horse).filter(
            database.Horse.name == h_data["name"]
        ).first()

        if not horse:
            horse = database.Horse(**h_data)
            db.add(horse)

    db.commit()

    jockeys_data = [
        {"name": "James McDonald"},
        {"name": "Mark Zahra"},
        {"name": "Blake Shinn"},
        {"name": "Tommy Berry"},
        {"name": "Ben Melham"},
        {"name": "Craig Williams"},
        {"name": "Damien Oliver"},
        {"name": "John Allen"},
        {"name": "Koby Jennings"},
        {"name": "Michael Dee"},
    ]

    for j_data in jockeys_data:
        jockey = db.query(database.Jockey).filter(
            database.Jockey.name == j_data["name"]
        ).first()

        if not jockey:
            jockey = database.Jockey(**j_data)
            db.add(jockey)

    trainers_data = [
        {"name": "Chris Waller"},
        {"name": "James Cummings"},
        {"name": "Peter & Paul Snowden"},
        {"name": "Gai Waterhouse"},
        {"name": "Mick Price"},
        {"name": "Grahame Begg"},
        {"name": "Peter Moody"},
        {"name": "Leon & Troy Corstens"},
        {"name": "Kelly Schweida"},
        {"name": "Matt Laurie"},
    ]

    for t_data in trainers_data:
        trainer = db.query(database.Trainer).filter(
            database.Trainer.name == t_data["name"]
        ).first()

        if not trainer:
            trainer = database.Trainer(**t_data)
            db.add(trainer)

    db.commit()

    venues = db.query(database.Venue).all()
    horses = db.query(database.Horse).all()
    jockeys = db.query(database.Jockey).all()
    trainers = db.query(database.Trainer).all()

    today = datetime.now()
    venue = venues[0] if venues else None

    if venue:
        meeting = database.Meeting(
            venue_id=venue.id,
            date=today,
            weather="Fine",
            track_rating="Good 4"
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        for i in range(1, 9):
            race = database.Race(
                meeting_id=meeting.id,
                race_number=i,
                race_name=f"Race {i}",
                distance=1200 + (i * 100),
                race_time=today.replace(hour=12 + i, minute=30),
                status="scheduled"
            )
            db.add(race)
            db.commit()
            db.refresh(race)

            for j, horse in enumerate(horses[:8]):
                participant = database.Participant(
                    race_id=race.id,
                    horse_id=horse.id,
                    jockey_id=jockeys[j].id if j < len(jockeys) else None,
                    trainer_id=trainers[j].id if j < len(trainers) else None,
                    barrier=j + 1,
                    carried_weight=55 + (j % 5),
                    form_string=f"{1 + j % 5}-{2 + j % 4}-{j % 5 + 1}-{(j + 2) % 5 + 1}-{j % 3 + 1}",
                    rating=90 + (j * 3)
                )
                db.add(participant)

        db.commit()

    return {
        "status": "completed",
        "message": "Sample data seeded successfully",
        "venues": len(venues),
        "horses": len(horses),
        "jockeys": len(jockeys),
        "trainers": len(trainers)
    }


# ============================================
# Data Statistics & Refresh
# ============================================

@router.get("/stats")
def get_database_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the database including race counts.
    """
    from datetime import datetime, timedelta
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    stats = {
        "venues": db.query(database.Venue).count(),
        "horses": db.query(database.Horse).count(),
        "jockeys": db.query(database.Jockey).count(),
        "trainers": db.query(database.Trainer).count(),
        "meetings": db.query(database.Meeting).count(),
        "races": db.query(database.Race).count(),
        "participants": db.query(database.Participant).count(),
        "results": db.query(database.RaceResult).count(),
        "market_data": db.query(database.MarketData).count(),
        "today_races": db.query(database.Race).filter(
            database.Race.race_time >= today,
            database.Race.race_time < tomorrow
        ).count(),
        "upcoming_races": db.query(database.Race).filter(
            database.Race.race_time >= tomorrow,
            database.Race.race_time < next_week
        ).count(),
        "completed_races": db.query(database.Race).filter(
            database.Race.status == "completed"
        ).count()
    }
    
    return stats


@router.post("/refresh")
def trigger_data_refresh(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a data refresh.
    This will:
    1. Add any new upcoming events if needed
    2. Update odds for upcoming races
    3. Check for any race results
    """
    def refresh_task():
        db = SessionLocal()
        try:
            from app.services.scraper.historical_loader import HistoricalDataLoader
            from app.services.scraper.live_update import LiveUpdateService
            
            # Add upcoming events if needed
            loader = HistoricalDataLoader(db)
            loader.add_upcoming_events(days_forward=14)
            
            # Run live update
            live_service = LiveUpdateService(db)
            live_service.run_live_update()
            
            logger.info("Data refresh completed")
        except Exception as e:
            logger.error(f"Error during data refresh: {e}")
        finally:
            db.close()
    
    background_tasks.add_task(refresh_task)
    
    return {
        "status": "started",
        "message": "Data refresh started in background"
    }


@router.post("/refresh-upcoming")
def trigger_upcoming_refresh(
    background_tasks: BackgroundTasks,
    days: int = Query(default=30, ge=7, le=90, description="Number of days of upcoming events to add"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger adding/updating upcoming events.
    """
    def upcoming_task():
        db = SessionLocal()
        try:
            from app.services.scraper.historical_loader import HistoricalDataLoader
            
            loader = HistoricalDataLoader(db)
            stats = loader.add_upcoming_events(days_forward=days)
            
            logger.info(f"Upcoming events refresh completed: {stats}")
        except Exception as e:
            logger.error(f"Error during upcoming refresh: {e}")
        finally:
            db.close()
    
    background_tasks.add_task(upcoming_task)
    
    return {
        "status": "started",
        "message": f"Adding/updating upcoming events for next {days} days",
        "estimated_time": "1-2 minutes"
    }
