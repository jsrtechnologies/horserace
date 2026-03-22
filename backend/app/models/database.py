from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Venue(Base):
    """Racing venues/tracks."""
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    state = Column(String(10), nullable=False)  # VIC, NSW, QLD, etc.
    track_type = Column(String(50))  # Turf, Synthetic, Dirt
    latitude = Column(Float)
    longitude = Column(Float)
    ra_venue_code = Column(String(50), unique=True)  # Racing Australia venue code
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meetings = relationship("Meeting", back_populates="venue")


class Meeting(Base):
    """Race meetings (typically one day at one venue)."""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    weather = Column(String(50))  # Fine, Overcast, Rain, etc.
    track_rating = Column(String(20))  # Good 4, Soft 5, Heavy 8, etc.
    track_condition = Column(String(50))
    rainfall = Column(Float)  # mm
    humidity = Column(Float)
    wind_speed = Column(Float)
    is_abandoned = Column(Boolean, default=False)
    ra_meeting_id = Column(String(100), unique=True)  # Racing Australia meeting ID
    rail_position = Column(String(100))  # Rail position info
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue = relationship("Venue", back_populates="meetings")
    races = relationship("Race", back_populates="meeting")


class Race(Base):
    """Individual races within a meeting."""
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    race_number = Column(Integer, nullable=False)
    race_name = Column(String(300))
    distance = Column(Integer, nullable=False)  # meters
    race_class = Column(String(100))
    prize_money = Column(Float)
    race_time = Column(DateTime, nullable=False)
    race_type = Column(String(50))  # Gallops, Harness, Greyhounds
    status = Column(String(20), default="scheduled")  # scheduled, completed, abandoned
    ra_race_id = Column(String(100), unique=True)  # Racing Australia race ID
    weather_updated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="races")
    participants = relationship("Participant", back_populates="race")
    results = relationship("RaceResult", back_populates="race")


class Horse(Base):
    """Horse information."""
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    sire = Column(String(200))
    dam = Column(String(200))
    dam_sire = Column(String(200))
    foal_date = Column(DateTime)
    age = Column(Integer)
    gender = Column(String(10))  # Colt, Filly, Mare, Gelding, Horse
    color = Column(String(50))
    trainer_id = Column(Integer, ForeignKey("trainers.id"))
    owner = Column(String(300))
    country = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("Participant", back_populates="horse")
    trainer = relationship("Trainer", back_populates="horses")


class Jockey(Base):
    """Jockey information."""
    __tablename__ = "jockeys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    license_number = Column(String(50))
    state = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("Participant", back_populates="jockey")
    statistics = relationship("JockeyStatistics", back_populates="jockey", uselist=False)


class Trainer(Base):
    """Trainer information."""
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    license_number = Column(String(50))
    state = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("Participant", back_populates="trainer")
    statistics = relationship("TrainerStatistics", back_populates="trainer", uselist=False)
    horses = relationship("Horse", back_populates="trainer")


class Participant(Base):
    """Horse in a race (runner)."""
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    jockey_id = Column(Integer, ForeignKey("jockeys.id"))
    trainer_id = Column(Integer, ForeignKey("trainers.id"))
    barrier = Column(Integer)
    carried_weight = Column(Float)
    rating = Column(Integer)
    form_string = Column(String(50))  # Last 5 finishes
    last_5_positions = Column(JSON)  # [1, 3, 2, 5, 1]
    days_since_last_run = Column(Integer)
    weight_change = Column(Float)
    is_scratched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    race = relationship("Race", back_populates="participants")
    horse = relationship("Horse", back_populates="participants")
    jockey = relationship("Jockey", back_populates="participants")
    trainer = relationship("Trainer", back_populates="participants")
    prediction = relationship("Prediction", back_populates="participant", uselist=False)
    result = relationship("RaceResult", back_populates="participant", uselist=False)
    market_data = relationship("MarketData", back_populates="participant")


class RaceResult(Base):
    """Race results."""
    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    finishing_position = Column(Integer, nullable=False)
    dividend = Column(Float)  # Win dividend
    place_dividend = Column(Float)
    time = Column(String(20))
    margin = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    race = relationship("Race", back_populates="results")
    participant = relationship("Participant", back_populates="result")


class Prediction(Base):
    """ML predictions for each participant."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    win_probability = Column(Float, nullable=False)
    place_probability = Column(Float)
    predicted_position = Column(Integer)
    confidence_score = Column(Float)
    model_version = Column(String(50))
    factors = Column(JSON)  # Key factors influencing prediction
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="prediction")


class JockeyStatistics(Base):
    """Jockey performance statistics."""
    __tablename__ = "jockey_statistics"

    id = Column(Integer, primary_key=True, index=True)
    jockey_id = Column(Integer, ForeignKey("jockeys.id"), nullable=False)
    total_rides = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    place_rate = Column(Float, default=0.0)
    strike_rate_30_days = Column(Float, default=0.0)
    wet_track_wins = Column(Integer, default=0)
    dry_track_wins = Column(Integer, default=0)
    first_timer_wins = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    jockey = relationship("Jockey", back_populates="statistics")


class TrainerStatistics(Base):
    """Trainer performance statistics."""
    __tablename__ = "trainer_statistics"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    total_runners = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    place_rate = Column(Float, default=0.0)
    strike_rate_30_days = Column(Float, default=0.0)
    wet_track_wins = Column(Integer, default=0)
    synthetic_wins = Column(Integer, default=0)
    metro_wins = Column(Integer, default=0)
    provincial_wins = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    trainer = relationship("Trainer", back_populates="statistics")


class ModelPerformance(Base):
    """Model training and performance metrics."""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)
    training_samples = Column(Integer)
    top_1_accuracy = Column(Float)
    top_3_accuracy = Column(Float)
    top_1_roi = Column(Float)  # Return on investment
    features_used = Column(JSON)
    hyperparameters = Column(JSON)
    notes = Column(Text)


class MarketData(Base):
    """Real-time odds and market data for runners."""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    fixed_win = Column(Float)  # Fixed odds win
    fixed_place = Column(Float)  # Fixed odds place
    parimutuel_win = Column(Float)  # Tote odds win
    parimutuel_place = Column(Float)  # Tote odds place
    SP = Column(Float)  # Starting Price
    is_available = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="market_data")

    participant = relationship("Participant", back_populates="market_data")


class SyncStatus(Base):
    """Track data sync status and scheduling."""
    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False)  # historical, live, weather
    status = Column(String(20), default="idle")  # idle, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    progress_percent = Column(Float, default=0.0)
    total_expected = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExternalSource(Base):
    """Track external data sources and their configuration."""
    __tablename__ = "external_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(50))  # racing_api, odds_api, weather_api
    base_url = Column(String(500))
    api_key = Column(String(200))
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # requests per minute
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
