"""
Races API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models import database
from app.models.schemas import (
    RaceBase, RaceCreate, Race, RaceWithDetails,
    MeetingBase, MeetingCreate, Meeting, MeetingWithRaces,
    VenueBase, VenueCreate, Venue
)

router = APIRouter(prefix="/api/races", tags=["races"])


@router.get("/", response_model=List[Race])
def get_races(
    skip: int = 0,
    limit: int = 100,
    date: Optional[str] = None,
    venue_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of races with optional filters.
    """
    query = db.query(database.Race)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = target_date + timedelta(days=1)
            query = query.filter(
                and_(
                    database.Race.race_time >= target_date,
                    database.Race.race_time < next_day
                )
            )
        except ValueError:
            pass

    if venue_id:
        query = query.join(database.Meeting).filter(
            database.Meeting.venue_id == venue_id
        )

    if status:
        query = query.filter(database.Race.status == status)

    races = query.order_by(database.Race.race_time).offset(skip).limit(limit).all()
    return races


@router.get("/{race_id}", response_model=RaceWithDetails)
def get_race(race_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific race.
    """
    race = db.query(database.Race).filter(database.Race.id == race_id).first()

    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    return race


@router.get("/meetings/", response_model=List[MeetingWithRaces])
def get_meetings(
    date: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get race meetings with their races.
    """
    query = db.query(database.Meeting)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = target_date + timedelta(days=1)
            query = query.filter(
                and_(
                    database.Meeting.date >= target_date,
                    database.Meeting.date < next_day
                )
            )
        except ValueError:
            pass

    if state:
        query = query.join(database.Venue).filter(
            database.Venue.state == state.upper()
        )

    meetings = query.order_by(database.Meeting.date).all()
    return meetings


@router.get("/meetings/{meeting_id}", response_model=MeetingWithRaces)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific meeting.
    """
    meeting = db.query(database.Meeting).filter(
        database.Meeting.id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return meeting


@router.get("/venues/", response_model=List[Venue])
def get_venues(
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of venues.
    """
    query = db.query(database.Venue)

    if state:
        query = query.filter(database.Venue.state == state.upper())

    venues = query.order_by(database.Venue.name).all()
    return venues


@router.post("/venues/", response_model=Venue)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """
    Create a new venue.
    """
    # Check if venue exists
    existing = db.query(database.Venue).filter(
        database.Venue.name == venue.name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Venue already exists")

    db_venue = database.Venue(**venue.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)

    return db_venue


@router.post("/", response_model=Race)
def create_race(race: RaceCreate, db: Session = Depends(get_db)):
    """
    Create a new race.
    """
    # Check if meeting exists
    meeting = db.query(database.Meeting).filter(
        database.Meeting.id == race.meeting_id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    db_race = database.Race(**race.dict())
    db.add(db_race)
    db.commit()
    db.refresh(db_race)

    return db_race


@router.post("/meetings/", response_model=Meeting)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    """
    Create a new meeting.
    """
    # Check if venue exists
    venue = db.query(database.Venue).filter(
        database.Venue.id == meeting.venue_id
    ).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    db_meeting = database.Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    return db_meeting


@router.get("/upcoming/")
def get_upcoming_races(
    hours: int = Query(default=24, ge=1, le=72),
    db: Session = Depends(get_db)
):
    """
    Get upcoming races within specified hours.
    """
    now = datetime.now()
    end_time = now + timedelta(hours=hours)

    races = db.query(database.Race).filter(
        and_(
            database.Race.race_time >= now,
            database.Race.race_time <= end_time,
            database.Race.status == "scheduled"
        )
    ).order_by(database.Race.race_time).all()

    return {
        "count": len(races),
        "races": [
            {
                "id": r.id,
                "race_number": r.race_number,
                "race_name": r.race_name,
                "distance": r.distance,
                "race_time": r.race_time.isoformat(),
                "venue": r.meeting.venue.name if r.meeting and r.meeting.venue else "Unknown",
                "track_rating": r.meeting.track_rating if r.meeting else "Unknown",
                "weather": r.meeting.weather if r.meeting else "Unknown"
            }
            for r in races
        ]
    }
