#!/usr/bin/env python3
"""
Standalone script to load race results from Racing Australia into the database.
Only requires SQLAlchemy and psycopg2 - no ML dependencies needed.
"""

import sys
import os

# Data extracted from racingaustralia.horse for Caulfield Heath - March 18, 2026
CAULFIELD_HEATH_DATA = {
    "key": "2026Mar18,VIC,Caulfield Heath",
    "state": "VIC",
    "venue": "Caulfield Heath",
    "date": "2026-03-18",
    "rail_position": "True Entire Circuit",
    "races": [
        {
            "race_number": 1,
            "race_name": "Sportsbet BlackBook Handicap",
            "distance": 1500,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "SAVITRI", "trainer": "Mitchell Freedman", "jockey": "John Allen", "margin": "", "barrier": 2, "weight": 56.5, "starting_price": 2.50},
                {"position": 2, "horse_name": "ENGINE OF WAR (NZ)", "trainer": "Mick Price & Michael Kent (Jnr)", "jockey": "Luke Cartwright", "margin": "1L", "barrier": 1, "weight": 61.5, "starting_price": 6.00},
                {"position": 3, "horse_name": "LOUD CHARLIE", "trainer": "Lloyd Kennewell", "jockey": "Mark Zahra", "margin": "2L", "barrier": 4, "weight": 61.5, "starting_price": 2.70},
                {"position": 4, "horse_name": "MERIMBULA", "trainer": "Matt Laurie", "jockey": "Daniel Stackhouse", "margin": "4.75L", "barrier": 3, "weight": 57.5, "starting_price": 41.00},
                {"position": 5, "horse_name": "LIGHT MOVES", "trainer": "Mick Price & Michael Kent (Jnr)", "jockey": "Ben Melham", "margin": "5.5L", "barrier": 5, "weight": 58.5, "starting_price": 8.00},
                {"position": 6, "horse_name": "SIRIUSLY HOT", "trainer": "Ciaron Maher", "jockey": "Craig Williams", "margin": "7L", "barrier": 6, "weight": 59.5, "starting_price": 12.00},
            ]
        },
        {
            "race_number": 2,
            "race_name": "The Big Screen Company Handicap",
            "distance": 1500,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "GRAND OMAHA", "trainer": "Matt Laurie", "jockey": "Patrick Moloney", "margin": "", "barrier": 7, "weight": 55.5, "starting_price": 4.20},
                {"position": 2, "horse_name": "ALL BUSINESS", "trainer": "Leon & Troy Corstens & Will Larkin", "jockey": "Luke Cartwright", "margin": "1.75L", "barrier": 5, "weight": 59.0, "starting_price": 3.30},
                {"position": 3, "horse_name": "STRAAND DEAL", "trainer": "Lloyd Kennewell", "jockey": "Mark Zahra", "margin": "1.77L", "barrier": 8, "weight": 60.5, "starting_price": 10.00},
                {"position": 4, "horse_name": "ROCK THEM JOOLS (NZ)", "trainer": "Chris Waller", "jockey": "Damian Lane", "margin": "2.77L", "barrier": 6, "weight": 60.5, "starting_price": 10.00},
                {"position": 5, "horse_name": "VIANARRA", "trainer": "Trent Busuttin & Natalie Young", "jockey": "Craig Newitt", "margin": "3.52L", "barrier": 2, "weight": 59.0, "starting_price": 6.50},
                {"position": 6, "horse_name": "CROWN CRUSHER", "trainer": "Stephen V Brown", "jockey": "Ms Emily Pozman", "margin": "3.67L", "barrier": 4, "weight": 59.0, "starting_price": 9.50},
                {"position": 7, "horse_name": "DELIVERING", "trainer": "Ciaron Maher", "jockey": "Ms Dakotah Keane", "margin": "5.67L", "barrier": 3, "weight": 63.5, "starting_price": 7.50},
                {"position": 8, "horse_name": "HEAVENLY EAGLE (NZ)", "trainer": "Stephen V Brown", "jockey": "Stephen M Brown", "margin": "6.42L", "barrier": 1, "weight": 61.0, "starting_price": 19.00},
            ]
        },
        {
            "race_number": 3,
            "race_name": "Stow Storage Solutions Handicap",
            "distance": 1200,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "OLIVEANOTHERDAY", "trainer": "Tom Dabernig", "jockey": "Damian Lane", "margin": "", "barrier": 5, "weight": 60.5, "starting_price": 1.40},
                {"position": 2, "horse_name": "HOTSPUR REALE", "trainer": "Brian McGrath", "jockey": "Craig Williams", "margin": "3.25L", "barrier": 2, "weight": 57.5, "starting_price": 7.50},
                {"position": 3, "horse_name": "ALZARO", "trainer": "Ciaron Maher", "jockey": "John Allen", "margin": "3.4L", "barrier": 1, "weight": 56.0, "starting_price": 10.00},
                {"position": 4, "horse_name": "KEEP IT REAL", "trainer": "John Symons & Sheila Laxon", "jockey": "Daniel Stackhouse", "margin": "5.15L", "barrier": 8, "weight": 58.0, "starting_price": 31.00},
                {"position": 5, "horse_name": "BIG STAR", "trainer": "Ben Brisbourne", "jockey": "Luke Cartwright", "margin": "5.5L", "barrier": 3, "weight": 55.0, "starting_price": 31.00},
                {"position": 6, "horse_name": "BRICKENDON", "trainer": "Anthony & Sam Freedman", "jockey": "Mark Zahra", "margin": "6.75L", "barrier": 6, "weight": 58.0, "starting_price": 13.00},
                {"position": 7, "horse_name": "IMMERSE", "trainer": "Tony & Calvin McEvoy", "jockey": "Harry Coffey", "margin": "7.75L", "barrier": 4, "weight": 57.5, "starting_price": 19.00},
                {"position": 8, "horse_name": "DREAM ENUFF", "trainer": "Mark & Levi Kavanagh", "jockey": "Brad Rawiller", "margin": "8.75L", "barrier": 7, "weight": 58.5, "starting_price": 26.00},
            ]
        },
        {
            "race_number": 4,
            "race_name": "Sportsbet Up & Coming Stars Series Heat 4",
            "distance": 1200,
            "prize_money": 100000,
            "results": [
                {"position": 1, "horse_name": "TEN WARRIORS", "trainer": "Trevor Rogers", "jockey": "Jamie Mott", "margin": "", "barrier": 7, "weight": 59.5, "starting_price": 2.70},
                {"position": 2, "horse_name": "SANTANA", "trainer": "Michael, John & Wayne Hawkes", "jockey": "Ms Jamie Melham", "margin": "0.4L", "barrier": 9, "weight": 59.0, "starting_price": 2.60},
                {"position": 3, "horse_name": "DAMA ROYALE", "trainer": "Trent Busuttin & Natalie Young", "jockey": "Craig Williams", "margin": "2.15L", "barrier": 8, "weight": 57.0, "starting_price": 9.00},
                {"position": 4, "horse_name": "SILVER LIGHTNING", "trainer": "Peter Foster", "jockey": "Ms Molly Bourke", "margin": "2.61L", "barrier": 3, "weight": 59.5, "starting_price": 81.00},
                {"position": 5, "horse_name": "LADY LONSDALE", "trainer": "Ciaron Maher", "jockey": "John Allen", "margin": "2.96L", "barrier": 11, "weight": 57.0, "starting_price": 21.00},
                {"position": 6, "horse_name": "BIG KAPOW", "trainer": "Rory Hunter", "jockey": "Ms Melea Castle", "margin": "3.06L", "barrier": 6, "weight": 59.0, "starting_price": 12.00},
                {"position": 7, "horse_name": "SEE NO CITY", "trainer": "Graeme McQueen", "jockey": "Craig Newitt", "margin": "5.81L", "barrier": 1, "weight": 59.5, "starting_price": 81.00},
                {"position": 8, "horse_name": "NAR NAR GOON", "trainer": "Phillip Stokes", "jockey": "Lachlan Neindorf", "margin": "6.56L", "barrier": 4, "weight": 59.5, "starting_price": 7.00},
                {"position": 9, "horse_name": "GOTTALUVSPORT", "trainer": "Ricardo Meunier", "jockey": "Valentin Le Boeuf", "margin": "6.91L", "barrier": 2, "weight": 57.5, "starting_price": 201.00},
                {"position": 10, "horse_name": "MORNING RALPH", "trainer": "Leon & Troy Corstens & Will Larkin", "jockey": "Luke Cartwright", "margin": "12.91L", "barrier": 10, "weight": 59.0, "starting_price": 26.00},
                {"position": 11, "horse_name": "MIDNIGHT LOOT", "trainer": "Peter Ioannou", "jockey": "Remi Tremsal", "margin": "14.91L", "barrier": 5, "weight": 59.5, "starting_price": 201.00},
            ]
        },
        {
            "race_number": 5,
            "race_name": "Tile Importer Handicap",
            "distance": 1800,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "HALLOWED HALLS (NZ)", "trainer": "Chris Waller", "jockey": "Jye McNeil", "margin": "", "barrier": 1, "weight": 54.5, "starting_price": 5.50},
                {"position": 2, "horse_name": "CURSE IT", "trainer": "Greg Eurell", "jockey": "Logan Bates", "margin": "0.4L", "barrier": 7, "weight": 61.5, "starting_price": 4.60},
                {"position": 3, "horse_name": "AURA", "trainer": "Michael, John & Wayne Hawkes", "jockey": "Ms Jamie Melham", "margin": "0.5L", "barrier": 6, "weight": 54.0, "starting_price": 9.50},
                {"position": 4, "horse_name": "ALL SO CLEAR", "trainer": "Ben, Will & JD Hayes", "jockey": "Mark Zahra", "margin": "0.65L", "barrier": 5, "weight": 60.0, "starting_price": 7.50},
                {"position": 5, "horse_name": "KURAKKA (FR)", "trainer": "Ciaron Maher", "jockey": "Thomas Stockdale", "margin": "0.8L", "barrier": 2, "weight": 61.0, "starting_price": 41.00},
                {"position": 6, "horse_name": "SOTOMAYOR", "trainer": "Matt Laurie", "jockey": "Jackson Radley", "margin": "2.55L", "barrier": 8, "weight": 57.0, "starting_price": 8.50},
                {"position": 7, "horse_name": "GEORGIE GET MAD (GB)", "trainer": "Denis Pagan", "jockey": "Ms Dakotah Keane", "margin": "3.3L", "barrier": 3, "weight": 60.0, "starting_price": 6.50},
                {"position": 8, "horse_name": "BAYOU MUSIC", "trainer": "Anthony & Sam Freedman", "jockey": "Craig Williams", "margin": "3.8L", "barrier": 4, "weight": 55.5, "starting_price": 3.90},
            ]
        },
        {
            "race_number": 6,
            "race_name": "Sportsbet Same Race Multi Handicap",
            "distance": 1200,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "ETERNAL", "trainer": "Chris Waller", "jockey": "Ben Melham", "margin": "", "barrier": 6, "weight": 58.0, "starting_price": 3.70},
                {"position": 2, "horse_name": "BOHEMIAN ANGEL", "trainer": "Peter G Moody & Katherine Coleman", "jockey": "Zac Spain", "margin": "0.75L", "barrier": 3, "weight": 56.5, "starting_price": 7.00},
                {"position": 3, "horse_name": "STREET CONQUEROR", "trainer": "Enver Jusufovic", "jockey": "Lachlan Neindorf", "margin": "0.81L", "barrier": 5, "weight": 59.5, "starting_price": 12.00},
                {"position": 4, "horse_name": "COMMANDS SUCCESS", "trainer": "Dwayne Reid", "jockey": "Ms Holly Durnan", "margin": "1.56L", "barrier": 7, "weight": 61.0, "starting_price": 16.00},
                {"position": 5, "horse_name": "SPARKLING LUCK", "trainer": "Lloyd Kennewell", "jockey": "Damian Lane", "margin": "2.56L", "barrier": 1, "weight": 58.5, "starting_price": 6.50},
                {"position": 6, "horse_name": "MR BLUNT", "trainer": "Tony & Calvin McEvoy", "jockey": "Harry Coffey", "margin": "3.02L", "barrier": 2, "weight": 60.5, "starting_price": 2.35},
                {"position": 7, "horse_name": "STATICE", "trainer": "Michael, John & Wayne Hawkes", "jockey": "Ms Jamie Melham", "margin": "4.52L", "barrier": 4, "weight": 55.5, "starting_price": 20.00},
                {"position": 8, "horse_name": "TOLPUDDLE", "trainer": "Nick Ryan", "jockey": "Rhys McLeod", "margin": "4.62L", "barrier": 8, "weight": 59.5, "starting_price": 61.00},
            ]
        },
        {
            "race_number": 7,
            "race_name": "Quayclean Handicap",
            "distance": 1000,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "JENNYANYDOTS", "trainer": "Mitchell Freedman", "jockey": "John Allen", "margin": "", "barrier": 6, "weight": 61.5, "starting_price": 4.60},
                {"position": 2, "horse_name": "CROATIAN ART", "trainer": "Michael & Luke Cerchi", "jockey": "Ms Dakotah Keane", "margin": "0.1L", "barrier": 3, "weight": 59.5, "starting_price": 31.00},
                {"position": 3, "horse_name": "NORMANDY LASS", "trainer": "Robbie Griffiths", "jockey": "Patrick Moloney", "margin": "0.2L", "barrier": 9, "weight": 59.5, "starting_price": 5.50},
                {"position": 4, "horse_name": "EGERTON", "trainer": "Cliff Brown", "jockey": "Luke Cartwright", "margin": "0.3L", "barrier": 5, "weight": 60.0, "starting_price": 11.00},
                {"position": 5, "horse_name": "POCKET SIZE", "trainer": "Bill Papazaharoudakis", "jockey": "Jamie Mott", "margin": "0.45L", "barrier": 4, "weight": 58.5, "starting_price": 16.00},
                {"position": 6, "horse_name": "DREAMZEL", "trainer": "Tom Dabernig", "jockey": "Ms Jordyn Weatherley", "margin": "0.6L", "barrier": 2, "weight": 63.5, "starting_price": 21.00},
                {"position": 7, "horse_name": "MRS IGLESIA", "trainer": "Ben, Will & JD Hayes", "jockey": "Jackson Radley", "margin": "0.62L", "barrier": 7, "weight": 58.0, "starting_price": 3.30},
                {"position": 8, "horse_name": "DON'T RUSSIA", "trainer": "Craig Blackshaw", "jockey": "Craig Newitt", "margin": "1.87L", "barrier": 10, "weight": 58.5, "starting_price": 16.00},
                {"position": 9, "horse_name": "TIZ WORTHY", "trainer": "Lloyd Kennewell", "jockey": "Ms Jamie Melham", "margin": "2.02L", "barrier": 8, "weight": 59.0, "starting_price": 6.00},
                {"position": 10, "horse_name": "SHANGHAI VENTURE", "trainer": "Brian McGrath", "jockey": "Jye McNeil", "margin": "2.52L", "barrier": 1, "weight": 54.5, "starting_price": 41.00},
            ]
        },
        {
            "race_number": 8,
            "race_name": "Sportsbet Race Replays Handicap",
            "distance": 1000,
            "prize_money": 55000,
            "results": [
                {"position": 1, "horse_name": "REGENERATION", "trainer": "Anthony & Sam Freedman", "jockey": "Damian Lane", "margin": "", "barrier": 6, "weight": 58.0, "starting_price": 2.45},
                {"position": 2, "horse_name": "ALONG THE RIVER", "trainer": "Michael & Luke Cerchi", "jockey": "Jordan Childs", "margin": "0.5L", "barrier": 3, "weight": 60.5, "starting_price": 6.00},
                {"position": 3, "horse_name": "EXCESS", "trainer": "Julius Sandhu", "jockey": "Beau Mertens", "margin": "1.25L", "barrier": 2, "weight": 61.0, "starting_price": 8.00},
                {"position": 4, "horse_name": "VIASAIN", "trainer": "John McArdle", "jockey": "Jamie Mott", "margin": "2L", "barrier": 4, "weight": 57.5, "starting_price": 12.00},
                {"position": 5, "horse_name": "AUXILIARY", "trainer": "Greg Eurell", "jockey": "Ms Holly Durnan", "margin": "2.46L", "barrier": 5, "weight": 58.0, "starting_price": 8.50},
                {"position": 6, "horse_name": "MARTIAL MUSIC", "trainer": "Ben, Will & JD Hayes", "jockey": "Ms Dakotah Keane", "margin": "2.52L", "barrier": 1, "weight": 63.0, "starting_price": 3.60},
                {"position": 7, "horse_name": "SHALAILED", "trainer": "Con Kelly", "jockey": "Harry Coffey", "margin": "5.27L", "barrier": 7, "weight": 60.0, "starting_price": 101.00},
            ]
        }
    ]
}


# Import only what's needed for database operations
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from typing import Optional, List, Dict, Any

# Database URL
DATABASE_URL = "postgresql://sreeni.chinthakunta@localhost:5432/horse_racing_db"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Simplified models (subset of database.py)
class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    state = Column(String(10), nullable=False)
    ra_venue_code = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    ra_meeting_id = Column(String(100), unique=True)
    rail_position = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    race_number = Column(Integer, nullable=False)
    race_name = Column(String(300))
    distance = Column(Integer, nullable=False)
    prize_money = Column(Float)
    race_time = Column(DateTime, nullable=False)
    race_type = Column(String(50), default="Gallops")
    status = Column(String(20), default="completed")
    ra_race_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Horse(Base):
    __tablename__ = "horses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trainer(Base):
    __tablename__ = "trainers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Jockey(Base):
    __tablename__ = "jockeys"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    jockey_id = Column(Integer, ForeignKey("jockeys.id"))
    trainer_id = Column(Integer, ForeignKey("trainers.id"))
    barrier = Column(Integer)
    carried_weight = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class RaceResult(Base):
    __tablename__ = "race_results"
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    finishing_position = Column(Integer, nullable=False)
    dividend = Column(Float)
    margin = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class DataLoader:
    """Simple data loader for race results."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def close(self):
        self.db.close()
    
    def _get_or_create_venue(self, name: str, state: str) -> Venue:
        venue = self.db.query(Venue).filter(Venue.name == name).first()
        if not venue:
            venue = Venue(
                name=name,
                state=state,
                ra_venue_code=name.upper().replace(" ", "_")
            )
            self.db.add(venue)
            self.db.flush()
            print(f"  Created venue: {name} ({state})")
        return venue
    
    def _get_or_create_meeting(self, venue_id: int, date: datetime, ra_meeting_id: str) -> Meeting:
        meeting = self.db.query(Meeting).filter(Meeting.ra_meeting_id == ra_meeting_id).first()
        if not meeting:
            meeting = Meeting(
                venue_id=venue_id,
                date=date,
                ra_meeting_id=ra_meeting_id
            )
            self.db.add(meeting)
            self.db.flush()
            print(f"  Created meeting: {ra_meeting_id}")
        return meeting
    
    def _get_or_create_race(self, meeting_id: int, race_data: Dict) -> Race:
        ra_race_id = f"{meeting_id}_{race_data['race_number']}"
        race = self.db.query(Race).filter(Race.ra_race_id == ra_race_id).first()
        
        if not race:
            race = Race(
                meeting_id=meeting_id,
                race_number=race_data["race_number"],
                race_name=race_data["race_name"],
                distance=race_data["distance"],
                prize_money=race_data["prize_money"],
                race_time=datetime.now().replace(hour=12, minute=0, second=0),
                ra_race_id=ra_race_id
            )
            self.db.add(race)
            self.db.flush()
        return race
    
    def _get_or_create_horse(self, name: str) -> Horse:
        horse = self.db.query(Horse).filter(Horse.name == name).first()
        if not horse:
            horse = Horse(name=name)
            self.db.add(horse)
            self.db.flush()
        return horse
    
    def _get_or_create_trainer(self, name: str) -> Optional[Trainer]:
        if not name:
            return None
        trainer = self.db.query(Trainer).filter(Trainer.name == name).first()
        if not trainer:
            trainer = Trainer(name=name)
            self.db.add(trainer)
            self.db.flush()
        return trainer
    
    def _get_or_create_jockey(self, name: str) -> Optional[Jockey]:
        if not name:
            return None
        clean_name = name.split("(")[0].strip()
        jockey = self.db.query(Jockey).filter(Jockey.name == clean_name).first()
        if not jockey:
            jockey = Jockey(name=clean_name)
            self.db.add(jockey)
            self.db.flush()
        return jockey
    
    def _get_or_create_participant(self, race_id: int, horse_id: int, 
                                   jockey_id: Optional[int] = None,
                                   trainer_id: Optional[int] = None,
                                   barrier: int = None, weight: float = None) -> Participant:
        participant = self.db.query(Participant).filter(
            Participant.race_id == race_id,
            Participant.horse_id == horse_id
        ).first()
        
        if not participant:
            participant = Participant(
                race_id=race_id,
                horse_id=horse_id,
                jockey_id=jockey_id,
                trainer_id=trainer_id,
                barrier=barrier,
                carried_weight=weight
            )
            self.db.add(participant)
            self.db.flush()
        return participant
    
    def _load_result(self, race_id: int, result_data: Dict) -> bool:
        horse = self._get_or_create_horse(result_data["horse_name"])
        trainer = self._get_or_create_trainer(result_data.get("trainer", ""))
        jockey = self._get_or_create_jockey(result_data.get("jockey", ""))
        
        participant = self._get_or_create_participant(
            race_id=race_id,
            horse_id=horse.id,
            jockey_id=jockey.id if jockey else None,
            trainer_id=trainer.id if trainer else None,
            barrier=result_data.get("barrier"),
            weight=result_data.get("weight")
        )
        
        # Check if result exists
        existing = self.db.query(RaceResult).filter(
            RaceResult.race_id == race_id,
            RaceResult.participant_id == participant.id
        ).first()
        
        if not existing:
            result = RaceResult(
                race_id=race_id,
                participant_id=participant.id,
                finishing_position=result_data["position"],
                dividend=result_data.get("starting_price"),
                margin=result_data.get("margin")
            )
            self.db.add(result)
            print(f"    {result_data['position']}. {result_data['horse_name']} (SP: ${result_data.get('starting_price', 'N/A')})")
            return True
        return False
    
    def load_meeting(self, meeting_data: Dict) -> Optional[int]:
        try:
            # Get or create venue
            venue = self._get_or_create_venue(meeting_data["venue"], meeting_data["state"])
            
            # Parse date
            date_str = meeting_data["date"]
            if isinstance(date_str, str):
                meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                meeting_date = date_str
            
            # Get or create meeting
            meeting = self._get_or_create_meeting(venue.id, meeting_date, meeting_data["key"])
            
            # Load races
            races_loaded = 0
            results_loaded = 0
            for race_data in meeting_data["races"]:
                race = self._get_or_create_race(meeting.id, race_data)
                print(f"  Race {race.race_number}: {race.race_name} ({race.distance}m)")
                races_loaded += 1
                
                for result_data in race_data["results"]:
                    if self._load_result(race.id, result_data):
                        results_loaded += 1
            
            self.db.commit()
            return {"races": races_loaded, "results": results_loaded}
            
        except Exception as e:
            self.db.rollback()
            print(f"Error loading meeting: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    print("=" * 60)
    print("Loading Race Results from Racing Australia")
    print("=" * 60)
    print(f"\nMeeting: {CAULFIELD_HEATH_DATA['venue']}")
    print(f"Date: {CAULFIELD_HEATH_DATA['date']}")
    print(f"State: {CAULFIELD_HEATH_DATA['state']}")
    
    total_results = sum(len(race['results']) for race in CAULFIELD_HEATH_DATA['races'])
    print(f"Races: {len(CAULFIELD_HEATH_DATA['races'])}")
    print(f"Total entries: {total_results}")
    print()
    
    loader = DataLoader()
    try:
        result = loader.load_meeting(CAULFIELD_HEATH_DATA)
        if result:
            print(f"\n✓ Successfully loaded {result['races']} races with {result['results']} results")
        else:
            print("\n✗ Failed to load data")
    finally:
        loader.close()


if __name__ == "__main__":
    main()
