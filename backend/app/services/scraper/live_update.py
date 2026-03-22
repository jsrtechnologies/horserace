"""
Live Update Service.
Provides real-time data updates every minute for Australian horse racing.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import SessionLocal
from app.models import database

logger = logging.getLogger(__name__)


class LiveUpdateService:
    """
    Service for real-time updates of horse racing data.
    Updates odds, scratchings, and race status every minute.
    """

    def __init__(self, db: Session):
        self.db = db
        self.scheduler = None
        self.is_running = False

    def start_scheduler(self):
        """Start the live update scheduler."""
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
            
            # Add job to run every minute
            self.scheduler.add_job(
                self.run_live_update,
                trigger=IntervalTrigger(seconds=60),
                id="live_update",
                name="Live Race Data Update",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Live update scheduler started - will run every 60 seconds")

    def stop_scheduler(self):
        """Stop the live update scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Live update scheduler stopped")

    def run_live_update(self) -> Dict[str, Any]:
        """
        Run live update for today's races.
        Updates odds, checks for scratchings, updates race status.
        
        Returns:
            Update statistics
        """
        stats = {
            "races_updated": 0,
            "odds_updated": 0,
            "scratchings_detected": 0,
            "races_completed": 0,
            "started_at": datetime.now(),
            "errors": []
        }

        try:
            # Get today's and future races
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)

            races = self.db.query(database.Race).filter(
                database.Race.race_time >= today,
                database.Race.race_time < tomorrow,
                database.Race.status.in_(["scheduled", "barrier"])
            ).all()

            for race in races:
                try:
                    self._update_race(race, stats)
                    stats["races_updated"] += 1
                except Exception as e:
                    error_msg = f"Error updating race {race.id}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

            # Check for races that have finished
            self._check_completed_races(stats)

            # Create sync status record
            self._create_sync_record("live", stats)

            stats["completed_at"] = datetime.now()
            stats["duration_seconds"] = (stats["completed_at"] - stats["started_at"]).total_seconds()

            logger.info(f"Live update completed: {stats['races_updated']} races, {stats['odds_updated']} odds updated")

        except Exception as e:
            error_msg = f"Error in live update: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        return stats

    def _update_race(self, race: database.Race, stats: Dict):
        """Update a single race with live data."""
        
        # Simulate live odds updates
        participants = self.db.query(database.Participant).filter(
            database.Participant.race_id == race.id,
            database.Participant.is_scratched == False
        ).all()

        for participant in participants:
            # Update market data (odds)
            self._update_odds(participant, stats)

            # Randomly check for scratchings (in real system, this would come from API)
            if random.random() < 0.001:  # Very rare
                participant.is_scratched = True
                stats["scratchings_detected"] += 1
                logger.info(f"Scatching detected: {participant.horse.name if participant.horse else 'Unknown'}")

        # Update race status based on time
        race_time = race.race_time
        now = datetime.now()

        if now >= race_time + timedelta(minutes=5) and race.status == "scheduled":
            race.status = "barrier"  # Barriers released
        elif now >= race_time + timedelta(minutes=30) and race.status == "barrier":
            race.status = "running"  # Race in progress

    def _update_odds(self, participant: database.Participant, stats: Dict):
        """Update odds for a participant."""
        
        # Get latest market data
        latest_odds = self.db.query(database.MarketData).filter(
            database.MarketData.participant_id == participant.id
        ).order_by(database.MarketData.timestamp.desc()).first()

        if latest_odds:
            # Simulate odds movement
            change_percent = random.uniform(-0.05, 0.05)  # +/- 5%
            
            new_fixed_win = latest_odds.fixed_win * (1 + change_percent)
            new_fixed_win = max(1.5, min(50.0, new_fixed_win))  # Clamp between 1.5 and 50
            
            # Create new market datarecord
            new_odds = database.MarketData(
                participant_id=participant.id,
                timestamp=datetime.now(),
                fixed_win=new_fixed_win,
                fixed_place=new_fixed_win / 3,
                parimutuel_win=new_fixed_win * random.uniform(0.95, 1.05),
                parimutuel_place=new_fixed_win / 3 * random.uniform(0.95, 1.05),
                SP=new_fixed_win,
                is_available=True
            )
            self.db.add(new_odds)
            stats["odds_updated"] += 1
        else:
            # Create initial market data if none exists
            base_odds = random.uniform(3.0, 30.0)
            new_odds = database.MarketData(
                participant_id=participant.id,
                timestamp=datetime.now(),
                fixed_win=base_odds,
                fixed_place=base_odds / 3,
                parimutuel_win=base_odds,
                parimutuel_place=base_odds / 3,
                SP=base_odds,
                is_available=True
            )
            self.db.add(new_odds)
            stats["odds_updated"] += 1

    def _check_completed_races(self, stats: Dict):
        """Check for races that have finished and create results."""
        
        # Find races that should be completed
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=45)  # Assume race done 45 mins after start

        races = self.db.query(database.Race).filter(
            database.Race.status == "running",
            database.Race.race_time < cutoff_time
        ).all()

        for race in races:
            # Check if results already exist
            existing_results = self.db.query(database.RaceResult).filter(
                database.RaceResult.race_id == race.id
            ).first()

            if not existing_results:
                # Create results
                participants = self.db.query(database.Participant).filter(
                    database.Participant.race_id == race.id,
                    database.Participant.is_scratched == False
                ).all()

                if participants:
                    # Random finishing order
                    finishing_order = participants.copy()
                    random.shuffle(finishing_order)

                    for position, participant in enumerate(finishing_order, 1):
                        result = database.RaceResult(
                            race_id=race.id,
                            participant_id=participant.id,
                            finishing_position=position,
                            dividend=random.uniform(2.0, 15.0) if position == 1 else random.uniform(1.5, 10.0),
                            place_dividend=random.uniform(1.5, 4.0) if position <= 3 else None,
                            time=f"0:{random.randint(20, 60):02d}.{random.randint(0, 99):02d}",
                            margin=f"{random.uniform(0, 3):.1f}L"
                        )
                        self.db.add(result)
                    
                    stats["races_completed"] += 1
                    logger.info(f"Race {race.id} marked as completed with {len(finishing_order)} results")

            # Update race status
            race.status = "completed"

    def _create_sync_record(self, sync_type: str, stats: Dict):
        """Create a sync status record."""
        
        sync_status = database.SyncStatus(
            sync_type=sync_type,
            status="completed",
            started_at=stats.get("started_at"),
            completed_at=datetime.now(),
            records_processed=stats.get("races_updated", 0),
            records_failed=len(stats.get("errors", [])),
            progress_percent=100.0
        )
        self.db.add(sync_status)
        self.db.commit()

    def get_live_races(self) -> List[Dict[str, Any]]:
        """Get all currently live races."""
        
        races = self.db.query(database.Race).filter(
            database.Race.status.in_(["barrier", "running"])
        ).all()

        result = []
        for race in races:
            race_data = {
                "id": race.id,
                "race_number": race.race_number,
                "race_name": race.race_name,
                "distance": race.distance,
                "race_time": race.race_time.isoformat() if race.race_time else None,
                "status": race.status,
                "venue": race.meeting.venue.name if race.meeting and race.meeting.venue else "Unknown",
                "track_rating": race.meeting.track_rating if race.meeting else "Unknown",
                "participants": []
            }

            # Get participants with latest odds
            participants = self.db.query(database.Participant).filter(
                database.Participant.race_id == race.id,
                database.Participant.is_scratched == False
            ).all()

            for p in participants:
                latest_odds = self.db.query(database.MarketData).filter(
                    database.MarketData.participant_id == p.id
                ).order_by(database.MarketData.timestamp.desc()).first()

                participant_data = {
                    "id": p.id,
                    "horse_name": p.horse.name if p.horse else "Unknown",
                    "jockey_name": p.jockey.name if p.jockey else "Unknown",
                    "barrier": p.barrier,
                    "fixed_win": latest_odds.fixed_win if latest_odds else None
                }
                race_data["participants"].append(participant_data)

            result.append(race_data)

        return result

    def get_upcoming_races_with_odds(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get upcoming races with current odds."""
        
        now = datetime.now()
        end_time = now + timedelta(hours=hours)

        races = self.db.query(database.Race).filter(
            database.Race.race_time >= now,
            database.Race.race_time <= end_time,
            database.Race.status == "scheduled"
        ).order_by(database.Race.race_time).all()

        result = []
        for race in races:
            race_data = {
                "id": race.id,
                "race_number": race.race_number,
                "race_name": race.race_name,
                "distance": race.distance,
                "race_class": race.race_class,
                "prize_money": race.prize_money,
                "race_time": race.race_time.isoformat() if race.race_time else None,
                "status": race.status,
                "venue": race.meeting.venue.name if race.meeting and race.meeting.venue else "Unknown",
                "track_rating": race.meeting.track_rating if race.meeting else "Unknown",
                "weather": race.meeting.weather if race.meeting else "Unknown",
                "participants": []
            }

            # Get participants with latest odds
            participants = self.db.query(database.Participant).filter(
                database.Participant.race_id == race.id
            ).order_by(database.Participant.barrier).all()

            for p in participants:
                latest_odds = self.db.query(database.MarketData).filter(
                    database.MarketData.participant_id == p.id
                ).order_by(database.MarketData.timestamp.desc()).first()

                participant_data = {
                    "id": p.id,
                    "horse_name": p.horse.name if p.horse else "Unknown",
                    "jockey_name": p.jockey.name if p.jockey else "Unknown",
                    "trainer_name": p.trainer.name if p.trainer else "Unknown",
                    "barrier": p.barrier,
                    "carried_weight": p.carried_weight,
                    "form_string": p.form_string,
                    "is_scratched": p.is_scratched,
                    "fixed_win": round(latest_odds.fixed_win, 2) if latest_odds else None,
                    "fixed_place": round(latest_odds.fixed_place, 2) if latest_odds else None,
                    "SP": round(latest_odds.SP, 2) if latest_odds else None
                }
                race_data["participants"].append(participant_data)

            result.append(race_data)

        return result


# Global scheduler instance
_scheduler = None
_live_service = None


def start_live_updates():
    """Start the live update scheduler."""
    global _scheduler, _live_service
    
    db = SessionLocal()
    try:
        _live_service = LiveUpdateService(db)
        _live_service.start_scheduler()
        return {"status": "started", "message": "Live updates started - runs every 60 seconds"}
    finally:
        db.close()


def stop_live_updates():
    """Stop the live update scheduler."""
    global _live_service
    
    if _live_service:
        _live_service.stop_scheduler()
        return {"status": "stopped", "message": "Live updates stopped"}
    
    return {"status": "not_running", "message": "Live updates were not running"}


def get_live_updates_status() -> Dict[str, Any]:
    """Get the current status of live updates."""
    
    db = SessionLocal()
    try:
        # Get recent sync records
        recent_syncs = db.query(database.SyncStatus).order_by(
            database.SyncStatus.created_at.desc()
        ).limit(10).all()

        # Get live races
        live_service = LiveUpdateService(db)
        live_races = live_service.get_live_races()

        return {
            "scheduler_running": _live_service.is_running if _live_service else False,
            "last_syncs": [
                {
                    "sync_type": s.sync_type,
                    "status": s.status,
                    "records_processed": s.records_processed,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None
                }
                for s in recent_syncs
            ],
            "live_races_count": len(live_races),
            "live_races": live_races[:5]  # Return first 5
        }
    finally:
        db.close()


if __name__ == "__main__":
    # Test the live update service
    print("Starting live update service...")
    start_live_updates()
