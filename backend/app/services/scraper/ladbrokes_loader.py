"""
Ladbrokes Data Loader.
Loads Australian horse racing data from Ladbrokes API into the database.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import database
from app.services.scraper.ladbrokes_scraper import LadbrokesScraper

logger = logging.getLogger(__name__)


class LadbrokesDataLoader:
    """Loads data from Ladbrokes API into the database."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scraper = LadbrokesScraper()
        
    def load_upcoming_races(self, days: int = 7) -> Dict[str, Any]:
        """
        Load upcoming races for the next N days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            Statistics about the load operation
        """
        stats = {
            "meetings_created": 0,
            "meetings_updated": 0,
            "races_created": 0,
            "races_updated": 0,
            "horses_created": 0,
            "participants_created": 0,
            "odds_updated": 0,
            "errors": []
        }
        
        try:
            # Fetch meetings from Ladbrokes
            meetings_data = self.scraper.get_upcoming_meetings(days=days)
            logger.info(f"Fetched {len(meetings_data)} meetings from Ladbrokes")
            
            for meeting_data in meetings_data:
                try:
                    self._process_meeting(meeting_data, stats)
                except Exception as e:
                    error_msg = f"Error processing meeting {meeting_data.get('venue_name')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Error loading upcoming races: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
        
        return stats
    
    def _process_meeting(self, meeting_data: Dict, stats: Dict):
        """Process a single meeting."""
        venue_name = meeting_data.get("venue_name")
        state = meeting_data.get("state")
        meeting_date = meeting_data.get("date")
        track_condition = meeting_data.get("track_condition")
        weather = meeting_data.get("weather")
        
        if not venue_name or not meeting_date:
            return
        
        # Parse date
        if isinstance(meeting_date, str):
            meeting_date = datetime.fromisoformat(meeting_date.replace("Z", "+00:00"))
        
        # Get or create venue
        venue = self._get_or_create_venue(venue_name, state)
        
        # Get or create meeting
        meeting = self._get_or_create_meeting(
            venue, meeting_date, track_condition, weather
        )
        
        stats["meetings_created"] += 1
        
        # Process races
        races_data = meeting_data.get("races", [])
        for race_data in races_data:
            try:
                self._process_race(meeting, race_data, stats)
            except Exception as e:
                error_msg = f"Error processing race {race_data.get('race_number')}: {str(e)}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)
    
    def _process_race(self, meeting: database.Meeting, race_data: Dict, stats: Dict):
        """Process a single race."""
        race_number = race_data.get("race_number")
        race_name = race_data.get("name")
        distance = race_data.get("distance")
        start_time = race_data.get("start_time")
        track_condition = race_data.get("track_condition")
        weather = race_data.get("weather")
        status = race_data.get("status", "scheduled")
        
        if not race_number or not distance:
            return
        
        # Parse start time
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        
        # Map Ladbrokes status to our status
        status_map = {
            "Open": "scheduled",
            "Final": "completed",
            "Abandoned": "abandoned",
            "Live": "running",
            "Interim": "barrier"
        }
        db_status = status_map.get(status, "scheduled")
        
        # Get or create race
        race = self._get_or_create_race(
            meeting, race_number, race_name, distance, 
            start_time, track_condition, weather, db_status
        )
        
        stats["races_created"] += 1
        
        # Fetch race details with runners
        race_id = race_data.get("external_id")
        if race_id:
            race_details = self.scraper.get_race_event(race_id)
            if race_details:
                runners = race_details.get("runners", [])
                for runner in runners:
                    try:
                        self._process_runner(race, runner, stats)
                    except Exception as e:
                        error_msg = f"Error processing runner {runner.get('name')}: {str(e)}"
                        logger.warning(error_msg)
    
    def _process_runner(self, race: database.Race, runner: Dict, stats: Dict):
        """Process a single runner (horse)."""
        horse_name = runner.get("name")
        barrier = runner.get("barrier")
        runner_number = runner.get("runner_number")
        is_scratched = runner.get("is_scratched", False)
        fixed_win = runner.get("fixed_win")
        fixed_place = runner.get("fixed_place")
        age = runner.get("age")
        sex = runner.get("sex")
        colour = runner.get("colour")
        gear = runner.get("gear")
        
        if not horse_name:
            return
        
        # Get or create horse
        horse = self._get_or_create_horse(horse_name, age, sex, colour)
        stats["horses_created"] += 1
        
        # Get or create jockey (name might not be in runner data - need to fetch separately)
        jockey = None
        
        # Get or create trainer
        trainer_name = runner.get("trainer")
        trainer = self._get_or_create_trainer(trainer_name) if trainer_name else None
        
        # Create participant
        participant = self._get_or_create_participant(
            race, horse, jockey, trainer, barrier, runner_number, is_scratched, gear
        )
        stats["participants_created"] += 1
        
        # Create market data (odds)
        if fixed_win:
            self._create_market_data(participant, fixed_win, fixed_place)
            stats["odds_updated"] += 1
    
    def _get_or_create_venue(self, name: str, state: str) -> database.Venue:
        """Get or create a venue."""
        venue = self.db.query(database.Venue).filter(
            database.Venue.name == name
        ).first()
        
        if not venue:
            venue = database.Venue(name=name, state=state)
            self.db.add(venue)
            self.db.flush()
            
        return venue
    
    def _get_or_create_meeting(
        self, venue: database.Venue, date: datetime, 
        track_condition: str, weather: str
    ) -> database.Meeting:
        """Get or create a meeting."""
        # Normalize date to just the date part
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        meeting = self.db.query(database.Meeting).filter(
            database.Meeting.venue_id == venue.id,
            database.Meeting.date == date_only
        ).first()
        
        if not meeting:
            meeting = database.Meeting(
                venue_id=venue.id,
                date=date_only,
                track_rating=track_condition,
                weather=weather
            )
            self.db.add(meeting)
            self.db.flush()
        else:
            # Update existing meeting
            meeting.track_rating = track_condition
            meeting.weather = weather
            
        return meeting
    
    def _get_or_create_race(
        self, meeting: database.Meeting, race_number: int, race_name: str,
        distance: int, race_time: datetime, track_condition: str, 
        weather: str, status: str
    ) -> database.Race:
        """Get or create a race."""
        race = self.db.query(database.Race).filter(
            database.Race.meeting_id == meeting.id,
            database.Race.race_number == race_number
        ).first()
        
        if not race:
            race = database.Race(
                meeting_id=meeting.id,
                race_number=race_number,
                race_name=race_name,
                distance=distance,
                race_time=race_time,
                status=status
            )
            self.db.add(race)
            self.db.flush()
        else:
            # Update existing race
            race.race_name = race_name
            race.distance = distance
            race.race_time = race_time
            race.status = status
            
        return race
    
    def _get_or_create_horse(
        self, name: str, age: Optional[int] = None, 
        sex: Optional[str] = None, colour: Optional[str] = None
    ) -> database.Horse:
        """Get or create a horse."""
        horse = self.db.query(database.Horse).filter(
            database.Horse.name == name
        ).first()
        
        if not horse:
            # Map sex to full gender
            gender_map = {"C": "Colt", "F": "Filly", "M": "Mare", "G": "Gelding", "H": "Horse"}
            gender = gender_map.get(sex, sex) if sex else None
            
            horse = database.Horse(
                name=name,
                age=age,
                gender=gender,
                color=colour
            )
            self.db.add(horse)
            self.db.flush()
            
        return horse
    
    def _get_or_create_trainer(self, name: str) -> database.Trainer:
        """Get or create a trainer."""
        if not name:
            return None
            
        trainer = self.db.query(database.Trainer).filter(
            database.Trainer.name == name
        ).first()
        
        if not trainer:
            trainer = database.Trainer(name=name)
            self.db.add(trainer)
            self.db.flush()
            
        return trainer
    
    def _get_or_create_participant(
        self, race: database.Race, horse: database.Horse,
        jockey: Optional[database.Jockey], trainer: Optional[database.Trainer],
        barrier: Optional[int], runner_number: Optional[int],
        is_scratched: bool, gear: Optional[str]
    ) -> database.Participant:
        """Get or create a participant."""
        participant = self.db.query(database.Participant).filter(
            database.Participant.race_id == race.id,
            database.Participant.horse_id == horse.id
        ).first()
        
        if not participant:
            participant = database.Participant(
                race_id=race.id,
                horse_id=horse.id,
                jockey_id=jockey.id if jockey else None,
                trainer_id=trainer.id if trainer else None,
                barrier=barrier,
                is_scratched=is_scratched
            )
            self.db.add(participant)
            self.db.flush()
        else:
            # Update existing participant
            participant.barrier = barrier
            participant.is_scratched = is_scratched
            if jockey:
                participant.jockey_id = jockey.id
            if trainer:
                participant.trainer_id = trainer.id
                
        return participant
    
    def _create_market_data(
        self, participant: database.Participant, 
        fixed_win: float, fixed_place: Optional[float]
    ):
        """Create market data (odds) for a participant."""
        market_data = database.MarketData(
            participant_id=participant.id,
            timestamp=datetime.utcnow(),
            fixed_win=fixed_win,
            fixed_place=fixed_place or fixed_win / 3,
            parimutuel_win=fixed_win,
            parimutuel_place=fixed_win / 3,
            SP=fixed_win,
            is_available=True
        )
        self.db.add(market_data)
    
    def commit(self):
        """Commit the transaction."""
        self.db.commit()


def load_ladbrokes_data(days: int = 7) -> Dict[str, Any]:
    """
    Convenience function to load Ladbrokes data into the database.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        Statistics about the load operation
    """
    db = SessionLocal()
    try:
        loader = LadbrokesDataLoader(db)
        stats = loader.load_upcoming_races(days=days)
        loader.commit()
        
        stats["status"] = "success"
        logger.info(f"Ladbrokes data loaded successfully: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error loading Ladbrokes data: {e}")
        db.rollback()
        return {"status": "error", "errors": [str(e)]}
        
    finally:
        db.close()


if __name__ == "__main__":
    # Test the loader
    print("Loading Ladbrokes data...")
    stats = load_ladbrokes_data(days=7)
    print(f"Results: {stats}")
