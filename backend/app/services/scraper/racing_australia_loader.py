"""
Data loader for Racing Australia scraped data.
Loads scraped data into the PostgreSQL database.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.database import Venue, Meeting, Race, Horse, Jockey, Trainer, Participant, RaceResult
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class RacingAustraliaLoader:
    """Data loader for Racing Australia scraped data."""
    
    def __init__(self):
        self.db: Session = None
        
    def _get_db(self):
        """Get database session."""
        if not self.db:
            self.db = SessionLocal()
        return self.db
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()
    
    def load_meeting_results(self, meeting_data: Dict[str, Any]) -> Optional[int]:
        """
        Load meeting results into the database.
        
        Args:
            meeting_data: Dictionary with meeting details and race results
            
        Returns:
            Meeting ID if successful, None otherwise
        """
        db = self._get_db()
        
        try:
            key = meeting_data.get("key")
            state = meeting_data.get("state")
            venue_name = meeting_data.get("venue")
            date_str = meeting_data.get("date")
            
            # Parse date
            if isinstance(date_str, str):
                try:
                    meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    meeting_date = datetime.now()
            else:
                meeting_date = date_str
            
            # Get or create venue
            venue = self._get_or_create_venue(db, venue_name, state)
            
            # Get or create meeting
            meeting = self._get_or_create_meeting(db, venue.id, meeting_date, key)
            
            # Load races
            races_data = meeting_data.get("races", [])
            for race_data in races_data:
                self._load_race(db, meeting.id, race_data)
            
            db.commit()
            logger.info(f"Loaded meeting {key} with {len(races_data)} races")
            return meeting.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error loading meeting {meeting_data.get('key')}: {e}")
            return None
        finally:
            self.close()
    
    def _get_or_create_venue(self, db: Session, name: str, state: str) -> Venue:
        """Get or create a venue."""
        venue = db.query(Venue).filter(Venue.name == name).first()
        
        if not venue:
            venue = Venue(
                name=name,
                state=state,
                ra_venue_code=name.upper().replace(" ", "_")
            )
            db.add(venue)
            db.flush()
            logger.info(f"Created venue: {name} ({state})")
        
        return venue
    
    def _get_or_create_meeting(
        self, 
        db: Session, 
        venue_id: int, 
        date: datetime, 
        ra_meeting_id: str
    ) -> Meeting:
        """Get or create a meeting."""
        meeting = db.query(Meeting).filter(
            Meeting.ra_meeting_id == ra_meeting_id
        ).first()
        
        if not meeting:
            meeting = Meeting(
                venue_id=venue_id,
                date=date,
                ra_meeting_id=ra_meeting_id
            )
            db.add(meeting)
            db.flush()
            logger.info(f"Created meeting: {ra_meeting_id}")
        
        return meeting
    
    def _load_race(
        self, 
        db: Session, 
        meeting_id: int, 
        race_data: Dict[str, Any]
    ) -> Optional[Race]:
        """Load a race and its results."""
        try:
            race_number = race_data.get("race_number", 1)
            distance = race_data.get("distance", 1200)
            race_name = race_data.get("race_name", "")
            prize_money = race_data.get("prize_money", 0)
            
            # Create race ID from meeting and race number
            ra_race_id = f"{meeting_id}_{race_number}"
            
            # Check if race already exists
            race = db.query(Race).filter(
                Race.ra_race_id == ra_race_id
            ).first()
            
            if not race:
                # Use a default race time (noon)
                race_time = datetime.now().replace(hour=12, minute=0, second=0)
                
                race = Race(
                    meeting_id=meeting_id,
                    race_number=race_number,
                    race_name=race_name,
                    distance=distance,
                    prize_money=prize_money,
                    race_time=race_time,
                    race_type="Gallops",
                    status="completed",
                    ra_race_id=ra_race_id
                )
                db.add(race)
                db.flush()
                logger.info(f"Created race {race_number} at meeting {meeting_id}")
            
            # Load results
            results = race_data.get("results", [])
            for result_data in results:
                self._load_result(db, race.id, result_data)
            
            return race
            
        except Exception as e:
            logger.error(f"Error loading race: {e}")
            return None
    
    def _load_result(
        self, 
        db: Session, 
        race_id: int, 
        result_data: Dict[str, Any]
    ) -> Optional[RaceResult]:
        """Load a race result."""
        try:
            position = result_data.get("position")
            horse_name = result_data.get("horse_name", "").strip()
            trainer_name = result_data.get("trainer", "").strip()
            jockey_name = result_data.get("jockey", "").strip()
            starting_price = result_data.get("starting_price")
            weight = result_data.get("weight")
            margin = result_data.get("margin")
            
            if not horse_name or not position:
                return None
            
            # Get or create horse
            horse = self._get_or_create_horse(db, horse_name)
            
            # Get or create trainer
            trainer = self._get_or_create_trainer(db, trainer_name) if trainer_name else None
            
            # Get or create jockey
            jockey = self._get_or_create_jockey(db, jockey_name) if jockey_name else None
            
            # Create or get participant
            participant = self._get_or_create_participant(
                db, race_id, horse.id, 
                jockey_id=jockey.id if jockey else None,
                trainer_id=trainer.id if trainer else None,
                weight=weight
            )
            
            # Check if result already exists
            existing_result = db.query(RaceResult).filter(
                RaceResult.race_id == race_id,
                RaceResult.participant_id == participant.id
            ).first()
            
            if not existing_result:
                # Create result
                result = RaceResult(
                    race_id=race_id,
                    participant_id=participant.id,
                    finishing_position=position,
                    dividend=starting_price,
                    margin=margin
                )
                db.add(result)
                logger.info(f"Added result: {position}. {horse_name}")
            
            return existing_result
            
        except Exception as e:
            logger.error(f"Error loading result: {e}")
            return None
    
    def _get_or_create_horse(self, db: Session, name: str) -> Horse:
        """Get or create a horse."""
        horse = db.query(Horse).filter(Horse.name == name).first()
        
        if not horse:
            horse = Horse(name=name)
            db.add(horse)
            db.flush()
            logger.debug(f"Created horse: {name}")
        
        return horse
    
    def _get_or_create_trainer(self, db: Session, name: str) -> Trainer:
        """Get or create a trainer."""
        if not name:
            return None
            
        trainer = db.query(Trainer).filter(Trainer.name == name).first()
        
        if not trainer:
            trainer = Trainer(name=name)
            db.add(trainer)
            db.flush()
            logger.debug(f"Created trainer: {name}")
        
        return trainer
    
    def _get_or_create_jockey(self, db: Session, name: str) -> Jockey:
        """Get or create a jockey."""
        if not name:
            return None
        
        # Clean name (remove apprenticeship info)
        clean_name = name.split("(")[0].strip()
        
        jockey = db.query(Jockey).filter(Jockey.name == clean_name).first()
        
        if not jockey:
            jockey = Jockey(name=clean_name)
            db.add(jockey)
            db.flush()
            logger.debug(f"Created jockey: {clean_name}")
        
        return jockey
    
    def _get_or_create_participant(
        self, 
        db: Session, 
        race_id: int, 
        horse_id: int,
        jockey_id: Optional[int] = None,
        trainer_id: Optional[int] = None,
        weight: Optional[float] = None
    ) -> Participant:
        """Get or create a participant."""
        participant = db.query(Participant).filter(
            Participant.race_id == race_id,
            Participant.horse_id == horse_id
        ).first()
        
        if not participant:
            participant = Participant(
                race_id=race_id,
                horse_id=horse_id,
                jockey_id=jockey_id,
                trainer_id=trainer_id,
                carried_weight=weight
            )
            db.add(participant)
            db.flush()
        
        return participant
    
    def load_multiple_meetings(self, meetings_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Load multiple meetings.
        
        Returns:
            Dictionary with success/failure counts
        """
        stats = {
            "success": 0,
            "failed": 0
        }
        
        for meeting_data in meetings_data:
            result = self.load_meeting_results(meeting_data)
            if result:
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        return stats


def load_scraped_data_into_database(scraped_data: Dict[str, Any]) -> bool:
    """
    Convenience function to load scraped data into database.
    
    Args:
        scraped_data: Dictionary with meeting/race data from scraper
        
    Returns:
        True if successful, False otherwise
    """
    loader = RacingAustraliaLoader()
    
    try:
        # Handle both single meeting and multiple meetings
        if "races" in scraped_data:
            # Single meeting
            result = loader.load_meeting_results(scraped_data)
            return result is not None
        elif "meetings" in scraped_data:
            # Multiple meetings
            stats = loader.load_multiple_meetings(scraped_data["meetings"])
            return stats["failed"] == 0
        else:
            logger.error("Invalid scraped data format")
            return False
            
    finally:
        loader.close()


if __name__ == "__main__":
    # Test the loader
    print("Testing Racing Australia data loader...")
    
    # Create test data
    test_meeting = {
        "key": "2026Mar09,NSW,Coffs Harbour",
        "state": "NSW",
        "venue": "Coffs Harbour",
        "date": "2026-03-09",
        "races": [
            {
                "race_number": 1,
                "race_name": " maiden",
                "distance": 1200,
                "prize_money": 25000,
                "results": [
                    {"position": 1, "horse_name": "HEADSTREAM", "trainer": "Donna Grisedale", "jockey": "Jon Grisedale", "starting_price": 4.5},
                    {"position": 2, "horse_name": "CHISTOTA", "trainer": "Ciaron Maher", "jockey": "Luke Rolls", "starting_price": 3.0},
                    {"position": 3, "horse_name": "NAMARA (NZ)", "trainer": "Kris Lees", "jockey": "Ms Liberty Smyth", "starting_price": 8.0}
                ]
            }
        ]
    }
    
    loader = RacingAustraliaLoader()
    result = loader.load_meeting_results(test_meeting)
    
    if result:
        print(f"Successfully loaded meeting with ID: {result}")
    else:
        print("Failed to load meeting")
    
    loader.close()
