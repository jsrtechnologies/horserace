"""
Historical Data Loader Service.
Loads 2 years of Australian horse racing data into the database.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Generator
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import database

logger = logging.getLogger(__name__)

# Australian race venues with realistic data
VENUES = [
    {"name": "Flemington", "state": "VIC", "track_type": "Turf"},
    {"name": "Caulfield", "state": "VIC", "track_type": "Turf"},
    {"name": "Moonee Valley", "state": "VIC", "track_type": "Turf"},
    {"name": "Sandown", "state": "VIC", "track_type": "Turf"},
    {"name": "Randwick", "state": "NSW", "track_type": "Turf"},
    {"name": "Rosehill", "state": "NSW", "track_type": "Turf"},
    {"name": "Warwick Farm", "state": "NSW", "track_type": "Turf"},
    {"name": "Newcastle", "state": "NSW", "track_type": "Turf"},
    {"name": "Hawkesbury", "state": "NSW", "track_type": "Turf"},
    {"name": "Canterbury", "state": "NSW", "track_type": "Turf"},
    {"name": "Doomben", "state": "QLD", "track_type": "Turf"},
    {"name": "Eagle Farm", "state": "QLD", "track_type": "Turf"},
    {"name": "Gold Coast", "state": "QLD", "track_type": "Turf"},
    {"name": "Sunshine Coast", "state": "QLD", "track_type": "Turf"},
    {"name": "Toowoomba", "state": "QLD", "track_type": "Turf"},
    {"name": "Morphettville", "state": "SA", "track_type": "Turf"},
    {"name": "Gawler", "state": "SA", "track_type": "Turf"},
    {"name": "Ascot", "state": "WA", "track_type": "Turf"},
    {"name": "Belmont Park", "state": "WA", "track_type": "Turf"},
    {"name": "Pinjarra", "state": "WA", "track_type": "Turf"},
    {"name": "Hobart", "state": "TAS", "track_type": "Turf"},
    {"name": "Launceston", "state": "TAS", "track_type": "Turf"},
    {"name": "Wagga Wagga", "state": "NSW", "track_type": "Turf"},
    {"name": "Dubbo", "state": "NSW", "track_type": "Turf"},
    {"name": "Bathurst", "state": "NSW", "track_type": "Turf"},
    {"name": "Orange", "state": "NSW", "track_type": "Turf"},
    {"name": "Tamworth", "state": "NSW", "track_type": "Turf"},
    {"name": "Coffs Harbour", "state": "NSW", "track_type": "Turf"},
    {"name": "Grafton", "state": "NSW", "track_type": "Turf"},
    {"name": "Geelong", "state": "VIC", "track_type": "Turf"},
    {"name": "Ballarat", "state": "VIC", "track_type": "Turf"},
    {"name": "Bendigo", "state": "VIC", "track_type": "Turf"},
    {"name": "Mildura", "state": "VIC", "track_type": "Turf"},
    {"name": "Warrnambool", "state": "VIC", "track_type": "Turf"},
    {"name": "Pakenham", "state": "VIC", "track_type": "Turf"},
    {"name": "Cranbourne", "state": "VIC", "track_type": "Turf"},
    {"name": "Kembla Grange", "state": "NSW", "track_type": "Turf"},
    {"name": "Scone", "state": "NSW", "track_type": "Turf"},
    {"name": "Muswellbrook", "state": "NSW", "track_type": "Turf"},
    {"name": "Mudgee", "state": "NSW", "track_type": "Turf"},
    {"name": "Rockhampton", "state": "QLD", "track_type": "Turf"},
    {"name": "Townsville", "state": "QLD", "track_type": "Turf"},
    {"name": "Cairns", "state": "QLD", "track_type": "Turf"},
]

# Popular Australian horses (real and simulated)
HORSES_DATA = [
    {"name": "Winx", "sire": "Street Cry", "dam": "Vegas Showgirl", "age": 7},
    {"name": "Mer de Glace", "sire": "Rulership", "dam": "Megalodon", "age": 5},
    {"name": "Verry Elleegant", "sire": " Zed", "dam": "Exceeds", "age": 6},
    {"name": "Caulfield Cup", "sire": "Giant's Causeway", "dam": "Diamond Like", "age": 5},
    {"name": "Mugatoo", "sire": "Encosta de Lago", "dam": "Screaming Ruby", "age": 7},
    {"name": "Colette", "sire": "Hallowed Crown", "dam": "Mona Lisa", "age": 4},
    {"name": "King's Legacy", "sire": "Star Witness", "dam": "Breakfast", "age": 4},
    {"name": "Anamoe", "sire": "Street Boss", "dam": "Anatola", "age": 4},
    {"name": "Profiteer", "sire": "Capitalist", "dam": "Misfit", "age": 4},
    {"name": "Artorius", "sire": "Flying Artie", "dam": "Marmelo", "age": 4},
    {"name": "Zaaki", "sire": "Leroidesanimaux", "dam": "Kazda", "age": 6},
    {"name": "Mr Brightside", "sire": "Bullbars", "dam": "Luna", "age": 5},
    {"name": "Cascadian", "sire": "Famous Again", "dam": "Cascadia", "age": 6},
    {"name": "Mo'unga", "sire": "Savabeel", "dam": "Kalash", "age": 5},
    {"name": "Denormal", "sire": "More Than Ready", "dam": "Denouncement", "age": 4},
    {"name": "Pericles", "sire": "Capitalist", "dam": "Kalter", "age": 4},
    {"name": "Kovalica", "sire": "Ocean Park", "dam": "Acacius", "age": 4},
    {"name": "Mighty Ulysses", "sire": "Ulysses", "dam": "Mighty High", "age": 5},
    {"name": "Pinfluence", "sire": "Toronado", "dam": "Influence", "age": 5},
    {"name": "Lunick", "sire": "Lunar Rise", "dam": "Nickel", "age": 4},
]

# Generatemore horses
for i in range(50):
    sires = ["Lonhro", "Snitzel", "Exceed and Excel", "Fastnet Rock", "Danehill Dancer", 
             "Written Tycoon", "I Am Invincible", "Redoute's Choice", "High Chaparral", "Zabeel"]
    dams = ["Star", "Queen", "Lady", "Princess", "Duchess", "Angel", "Diamond", "Pearl", "Gold", "Silver"]
    HORSES_DATA.append({
        "name": f"Thunder {chr(65+i)}",
        "sire": random.choice(sires),
        "dam": f"{random.choice(dams)} {chr(65+i)}",
        "age": random.randint(3, 8)
    })

# Australian jockeys
JOCKEYS = [
    "James McDonald", "Mark Zahra", "Blake Shinn", "Tommy Berry", "Ben Melham",
    "Craig Williams", "Damien Oliver", "John Allen", "Koby Jennings", "Michael Dee",
    "William Pike", "Nash Rawiller", "Levi Kamei", "Jamie Kah", "Daniel Stackhouse",
    "Jye McNeil", "Declan Bates", "Boris Thornton", "Ryan Maloney", "Tim Clark",
    "Hugh Bowman", "Kerrin McEvoy", "Glyn Schofield", "Christian Reith", "Jason Collett"
]

# Australian trainers
TRAINERS = [
    "Chris Waller", "James Cummings", "Peter & Paul Snowden", "Gai Waterhouse",
    "Mick Price", "Grahame Begg", "Peter Moody", "Leon & Troy Corstens",
    "Kelly Schweida", "Matt Laurie", "Annabel Neasham", "John O'Shea",
    "Tony & Calvin McEvoy", "Patrick Payne", "Symon Wilde", "Michele Young",
    "Clinton Taylor", "Greg Eurell", "David & B Hayes", "Robert Smerdon"
]

WEATHER_CONDITIONS = ["Fine", "Cloudy", "Overcast", "Light Rain", "Heavy Rain", "Wind"]
TRACK_RATINGS = ["Good 3", "Good 4", "Soft 5", "Soft 6", "Heavy 7", "Heavy 8", "Heavy 9", "Heavy 10"]
RACE_CLASSES = ["BM72", "BM78", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", 
                "Maiden", "Open", "Group 3", "Group 2", "Group 1", "Listed"]


class HistoricalDataLoader:
    """Service to load 2 years of historical horse racing data."""

    def __init__(self, db: Session):
        self.db = db
        self.venues_cache = {}
        self.horses_cache = {}
        self.jockeys_cache = {}
        self.trainers_cache = {}

    def load_all_data(self, days_back: int = 730) -> Dict[str, Any]:
        """
        Load historical data for specified number of days.
        
        Args:
            days_back: Number of days to go back (default 730 = 2 years)
            
        Returns:
            Dictionary with loading statistics
        """
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        
        stats = {
            "venues_created": 0,
            "horses_created": 0,
            "jockeys_created": 0,
            "trainers_created": 0,
            "meetings_created": 0,
            "races_created": 0,
            "participants_created": 0,
            "results_created": 0,
            "market_data_created": 0,
            "days_processed": 0,
            "errors": []
        }

        logger.info(f"Starting historical data load from {start_date} to {end_date}")

        # Create/fetch base entities
        self._ensure_base_entities(stats)

        # Process each day
        current_date = start_date
        while current_date <= end_date:
            try:
                # Skip some days (no racing on some days)
                if random.random() > 0.3:  # 70% of days have racing
                    self._process_day(current_date, stats)
                    stats["days_processed"] += 1
                
                # Commit periodically
                if stats["days_processed"] % 10 == 0:
                    self.db.commit()
                    logger.info(f"Processed {stats['days_processed']} days, {stats['races_created']} races")
                    
            except Exception as e:
                error_msg = f"Error processing {current_date}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            current_date += timedelta(days=1)

        # Final commit
        self.db.commit()
        
        logger.info(f"Historical data load completed: {stats}")
        return stats

    def _ensure_base_entities(self, stats: Dict):
        """Ensure all base entities exist."""
        
        # Create venues
        for venue_data in VENUES:
            venue = self.db.query(database.Venue).filter(
                database.Venue.name == venue_data["name"]
            ).first()
            if not venue:
                venue = database.Venue(**venue_data)
                self.db.add(venue)
                stats["venues_created"] += 1
        
        self.db.commit()
        
        # Cache venues
        venues = self.db.query(database.Venue).all()
        self.venues_cache = {v.name: v for v in venues}

        # Create horses
        for horse_data in HORSES_DATA:
            horse = self.db.query(database.Horse).filter(
                database.Horse.name == horse_data["name"]
            ).first()
            if not horse:
                horse = database.Horse(**horse_data)
                self.db.add(horse)
                stats["horses_created"] += 1
        
        self.db.commit()
        
        # Cache horses
        horses = self.db.query(database.Horse).all()
        self.horses_cache = {h.name: h for h in horses}

        # Create jockeys
        for jockey_name in JOCKEYS:
            jockey = self.db.query(database.Jockey).filter(
                database.Jockey.name == jockey_name
            ).first()
            if not jockey:
                jockey = database.Jockey(name=jockey_name)
                self.db.add(jockey)
                stats["jockeys_created"] += 1
        
        self.db.commit()
        
        # Cache jockeys
        jockeys = self.db.query(database.Jockey).all()
        self.jockeys_cache = {j.name: j for j in jockeys}

        # Create trainers
        for trainer_name in TRAINERS:
            trainer = self.db.query(database.Trainer).filter(
                database.Trainer.name == trainer_name
            ).first()
            if not trainer:
                trainer = database.Trainer(name=trainer_name)
                self.db.add(trainer)
                stats["trainers_created"] += 1
        
        self.db.commit()
        
        # Cache trainers
        trainers = self.db.query(database.Trainer).all()
        self.trainers_cache = {t.name: t for t in trainers}

    def _process_day(self, date: datetime, stats: Dict):
        """Process a single day of racing."""
        
        # Select random venues for this day (1-3 meetings)
        num_meetings = random.randint(1, 3)
        selected_venues = random.sample(list(self.venues_cache.values()), 
                                        min(num_meetings, len(self.venues_cache)))
        
        for venue in selected_venues:
            # Create meeting
            meeting = database.Meeting(
                venue_id=venue.id,
                date=date,
                weather=random.choice(WEATHER_CONDITIONS),
                track_rating=random.choice(TRACK_RATINGS),
                track_condition=random.choice(["Turf", "Synthetic"])
            )
            self.db.add(meeting)
            self.db.flush()
            stats["meetings_created"] += 1

            # Create races for this meeting (6-10 races)
            num_races = random.randint(6, 10)
            race_times = [12, 13, 14, 15, 16, 17, 18]  # Hour of race
            
            for race_num in range(1, num_races + 1):
                race = self._create_race(meeting.id, race_num, date, race_times[race_num-1])
                self.db.add(race)
                self.db.flush()
                stats["races_created"] += 1

                # Create participants
                participants = self._create_participants(race.id, stats)
                stats["participants_created"] += len(participants)
                
                # Flush participants to get their IDs
                self.db.flush()

                # Create results (for past races)
                if date < datetime.now() - timedelta(days=1):
                    results = self._create_results(race.id, participants, stats)
                    stats["results_created"] += len(results)

                    # Create some market data
                    market_data = self._create_market_data(participants, stats)
                    stats["market_data_created"] += len(market_data)

    def _create_race(self, meeting_id: int, race_num: int, date: datetime, hour: int) -> database.Race:
        """Create a race record."""
        
        distances = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 2000, 2200, 2400, 2600, 2800]
        
        # Determine status based on date
        if date < datetime.now() - timedelta(days=1):
            status = "completed"
        elif date.date() == datetime.now().date():
            status = "scheduled"
        else:
            status = "scheduled"
        
        return database.Race(
            meeting_id=meeting_id,
            race_number=race_num,
            race_name=f"Race {race_num}",
            distance=random.choice(distances),
            race_class=random.choice(RACE_CLASSES),
            prize_money=random.choice([10000, 15000, 20000, 25000, 30000, 50000, 75000, 100000, 150000, 200000, 300000]),
            race_time=date.replace(hour=hour, minute=random.choice([0, 15, 30, 45])),
            race_type="Gallops",
            status=status
        )

    def _create_participants(self, race_id: int, stats: Dict) -> List[database.Participant]:
        """Create race participants."""
        
        participants = []
        horse_list = list(self.horses_cache.values())
        jockey_list = list(self.jockeys_cache.values())
        trainer_list = list(self.trainers_cache.values())
        
        # Select 8-15 horses
        num_horses = random.randint(8, 15)
        selected_horses = random.sample(horse_list, min(num_horses, len(horse_list)))
        
        for i, horse in enumerate(selected_horses):
            # Generate form string
            form_string = "-".join([str(random.randint(1, 15)) for _ in range(5)])
            
            participant = database.Participant(
                race_id=race_id,
                horse_id=horse.id,
                jockey_id=random.choice(jockey_list).id,
                trainer_id=random.choice(trainer_list).id,
                barrier=i + 1,
                carried_weight=random.uniform(50, 62),
                rating=random.randint(60, 120),
                form_string=form_string,
                days_since_last_run=random.randint(7, 60),
                weight_change=random.uniform(-2, 2),
                is_scratched=random.random() < 0.05  # 5% scratched
            )
            participants.append(participant)
            self.db.add(participant)
        
        return participants

    def _create_results(self, race_id: int, participants: List, stats: Dict) -> List:
        """Create race results."""
        
        results = []
        # Shuffle participants to determine finishing order
        finishing_order = participants.copy()
        random.shuffle(finishing_order)
        
        for position, participant in enumerate(finishing_order, 1):
            # Determine dividend based on position
            if position == 1:
                dividend = random.uniform(2.0, 15.0)
            elif position == 2:
                dividend = random.uniform(2.0, 10.0)
            elif position == 3:
                dividend = random.uniform(1.5, 8.0)
            else:
                dividend = random.uniform(1.1, 5.0)
            
            result = database.RaceResult(
                race_id=race_id,
                participant_id=participant.id,
                finishing_position=position,
                dividend=dividend,
                place_dividend=dividend / 3 if position <= 3 else None,
                time=random.choice(["0:00.00", "0:00.01", "0:00.02", "0:00.03"]),
                margin=f"{random.uniform(0, 5):.1f}L"
            )
            results.append(result)
            self.db.add(result)
        
        return results

    def _create_market_data(self, participants: List, stats: Dict) -> List:
        """Create market/odds data."""
        
        market_data_list = []
        
        for participant in participants:
            if not participant.is_scratched:
                # Generate realistic odds
                base_odds = random.uniform(2.0, 50.0)
                
                market_data = database.MarketData(
                    participant_id=participant.id,
                    timestamp=datetime.now() - timedelta(hours=random.randint(1, 24)),
                    fixed_win=base_odds,
                    fixed_place=base_odds / 3,
                    parimutuel_win=base_odds * random.uniform(0.9, 1.1),
                    parimutuel_place=base_odds / 3 * random.uniform(0.9, 1.1),
                    SP=base_odds,
                    is_available=True
                )
                market_data_list.append(market_data)
                self.db.add(market_data)
        
        return market_data_list

    def add_upcoming_events(self, days_forward: int = 30) -> Dict[str, Any]:
        """
        Add upcoming (future) race events to the database.
        
        Args:
            days_forward: Number of days into the future to create events
            
        Returns:
            Statistics about added events
        """
        stats = {
            "meetings_created": 0,
            "races_created": 0,
            "participants_created": 0,
            "days_processed": 0,
            "errors": []
        }
        
        logger.info(f"Adding upcoming events for next {days_forward} days")
        
        # Ensure we have base entities
        self._ensure_base_entities(stats)
        
        # Start from tomorrow
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_date = start_date + timedelta(days=days_forward)
        
        current_date = start_date
        while current_date <= end_date:
            try:
                # Skip some days (no racing on some days)
                if random.random() > 0.25:  # 75% of days have racing
                    self._process_future_day(current_date, stats)
                    stats["days_processed"] += 1
                
                # Commit periodically
                if stats["days_processed"] % 5 == 0:
                    self.db.commit()
                    logger.info(f"Processed {stats['days_processed']} future days, {stats['races_created']} upcoming races")
                    
            except Exception as e:
                error_msg = f"Error processing future {current_date}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            current_date += timedelta(days=1)
        
        # Final commit
        self.db.commit()
        
        logger.info(f"Upcoming events added: {stats}")
        return stats

    def _process_future_day(self, date: datetime, stats: Dict):
        """Process a future day of racing (no results, no market data yet)."""
        
        # Select random venues for this day (1-4 meetings)
        num_meetings = random.randint(1, 4)
        selected_venues = random.sample(list(self.venues_cache.values()), 
                                        min(num_meetings, len(self.venues_cache)))
        
        for venue in selected_venues:
            # Check if meeting already exists for this venue/date
            existing = self.db.query(database.Meeting).filter(
                database.Meeting.venue_id == venue.id,
                database.Meeting.date >= date,
                database.Meeting.date < date + timedelta(days=1)
            ).first()
            
            if existing:
                continue  # Skip if meeting already exists
                
            # Create meeting
            meeting = database.Meeting(
                venue_id=venue.id,
                date=date,
                weather="TBC",  # To be confirmed
                track_rating="TBC",
                track_condition="TBC"
            )
            self.db.add(meeting)
            self.db.flush()
            stats["meetings_created"] += 1

            # Create races for this meeting (6-10 races)
            num_races = random.randint(6, 10)
            race_times = [12, 13, 14, 15, 16, 17, 18, 19]  # Hour of race
            
            for race_num in range(1, num_races + 1):
                race_time = date.replace(hour=race_times[min(race_num-1, len(race_times)-1)], minute=random.choice([0, 15, 30, 45]))
                
                # Check if race already exists
                existing_race = self.db.query(database.Race).filter(
                    database.Race.meeting_id == meeting.id,
                    database.Race.race_number == race_num
                ).first()
                
                if existing_race:
                    continue
                
                race = database.Race(
                    meeting_id=meeting.id,
                    race_number=race_num,
                    race_name=f"Race {race_num}",
                    distance=random.choice([1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 2000, 2200, 2400]),
                    race_class=random.choice(RACE_CLASSES),
                    prize_money=random.choice([10000, 15000, 20000, 25000, 30000, 50000, 75000, 100000, 150000, 200000]),
                    race_time=race_time,
                    race_type="Gallops",
                    status="scheduled"
                )
                self.db.add(race)
                self.db.flush()
                stats["races_created"] += 1

                # Create participants (no results, limited market data for future races)
                participants = self._create_participants(race.id, stats)
                stats["participants_created"] += len(participants)


def load_historical_data(days_back: int = 730) -> Dict[str, Any]:
    """
    Main function to load historical data.
    
    Args:
        days_back: Number of days of history to load
        
    Returns:
        Loading statistics
    """
    db = SessionLocal()
    try:
        loader = HistoricalDataLoader(db)
        return loader.load_all_data(days_back)
    finally:
        db.close()


def add_upcoming_events(days_forward: int = 30) -> Dict[str, Any]:
    """
    Add upcoming/future race events to the database.
    
    Args:
        days_forward: Number of days into the future to create events
        
    Returns:
        Statistics about added events
    """
    db = SessionLocal()
    try:
        loader = HistoricalDataLoader(db)
        return loader.add_upcoming_events(days_forward)
    finally:
        db.close()


if __name__ == "__main__":
    # Run the loader
    print("Starting historical data load...")
    stats = load_historical_data(730)  # 2 years
    print(f"Completed: {stats}")
