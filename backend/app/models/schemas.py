from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


# Venue schemas
class VenueBase(BaseModel):
    name: str
    state: str
    track_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class VenueCreate(VenueBase):
    pass


class Venue(VenueBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Meeting schemas
class MeetingBase(BaseModel):
    venue_id: int
    date: datetime
    weather: Optional[str] = None
    track_rating: Optional[str] = None
    track_condition: Optional[str] = None
    rainfall: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    is_abandoned: bool = False


class MeetingCreate(MeetingBase):
    pass


class Meeting(MeetingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    venue: Optional[Venue] = None

    model_config = ConfigDict(from_attributes=True)


# Race schemas
class RaceBase(BaseModel):
    meeting_id: int
    race_number: int
    race_name: Optional[str] = None
    distance: int
    race_class: Optional[str] = None
    prize_money: Optional[float] = None
    race_time: datetime
    race_type: str = "Gallops"
    status: str = "scheduled"


class RaceCreate(RaceBase):
    pass


class Race(RaceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    meeting: Optional[Meeting] = None

    model_config = ConfigDict(from_attributes=True)


# Horse schemas
class HorseBase(BaseModel):
    name: str
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    foal_date: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    trainer_id: Optional[int] = None
    owner: Optional[str] = None
    country: Optional[str] = None


class HorseCreate(HorseBase):
    pass


class Horse(HorseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Jockey schemas
class JockeyBase(BaseModel):
    name: str
    license_number: Optional[str] = None
    state: Optional[str] = None


class JockeyCreate(JockeyBase):
    pass


class Jockey(JockeyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Trainer schemas
class TrainerBase(BaseModel):
    name: str
    license_number: Optional[str] = None
    state: Optional[str] = None


class TrainerCreate(TrainerBase):
    pass


class Trainer(TrainerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Participant schemas
class ParticipantBase(BaseModel):
    race_id: int
    horse_id: int
    jockey_id: Optional[int] = None
    trainer_id: Optional[int] = None
    barrier: Optional[int] = None
    carried_weight: Optional[float] = None
    rating: Optional[int] = None
    form_string: Optional[str] = None
    days_since_last_run: Optional[int] = None
    weight_change: Optional[float] = None
    is_scratched: bool = False


class ParticipantCreate(ParticipantBase):
    pass


class Participant(ParticipantBase):
    id: int
    created_at: datetime
    updated_at: datetime
    horse: Optional[Horse] = None
    jockey: Optional[Jockey] = None
    trainer: Optional[Trainer] = None
    prediction: Optional["Prediction"] = None
    result: Optional["RaceResult"] = None

    model_config = ConfigDict(from_attributes=True)


# Race Result schemas
class RaceResultBase(BaseModel):
    race_id: int
    participant_id: int
    finishing_position: int
    dividend: Optional[float] = None
    place_dividend: Optional[float] = None
    time: Optional[str] = None
    margin: Optional[str] = None


class RaceResultCreate(RaceResultBase):
    pass


class RaceResult(RaceResultBase):
    id: int
    created_at: datetime
    participant: Optional[Participant] = None

    model_config = ConfigDict(from_attributes=True)


# Prediction schemas
class PredictionBase(BaseModel):
    participant_id: int
    win_probability: float
    place_probability: Optional[float] = None
    predicted_position: Optional[int] = None
    confidence_score: Optional[float] = None
    model_version: Optional[str] = None
    factors: Optional[dict] = None


class PredictionCreate(PredictionBase):
    pass


class Prediction(PredictionBase):
    id: int
    generated_at: datetime
    created_at: datetime
    participant: Optional[Participant] = None

    model_config = ConfigDict(from_attributes=True)


# Statistics schemas
class JockeyStatisticsBase(BaseModel):
    jockey_id: int
    total_rides: int = 0
    wins: int = 0
    win_rate: float = 0.0
    place_rate: float = 0.0
    strike_rate_30_days: float = 0.0
    wet_track_wins: int = 0
    dry_track_wins: int = 0
    first_timer_wins: int = 0


class JockeyStatisticsCreate(JockeyStatisticsBase):
    pass


class JockeyStatistics(JockeyStatisticsBase):
    id: int
    calculated_at: datetime
    jockey: Optional[Jockey] = None

    model_config = ConfigDict(from_attributes=True)


class TrainerStatisticsBase(BaseModel):
    trainer_id: int
    total_runners: int = 0
    wins: int = 0
    win_rate: float = 0.0
    place_rate: float = 0.0
    strike_rate_30_days: float = 0.0
    wet_track_wins: int = 0
    synthetic_wins: int = 0
    metro_wins: int = 0
    provincial_wins: int = 0


class TrainerStatisticsCreate(TrainerStatisticsBase):
    pass


class TrainerStatistics(TrainerStatisticsBase):
    id: int
    calculated_at: datetime
    trainer: Optional[Trainer] = None

    model_config = ConfigDict(from_attributes=True)


# Model Performance schemas
class ModelPerformanceBase(BaseModel):
    model_version: str
    training_samples: Optional[int] = None
    top_1_accuracy: Optional[float] = None
    top_3_accuracy: Optional[float] = None
    top_1_roi: Optional[float] = None
    features_used: Optional[dict] = None
    hyperparameters: Optional[dict] = None
    notes: Optional[str] = None


class ModelPerformanceCreate(ModelPerformanceBase):
    pass


class ModelPerformance(ModelPerformanceBase):
    id: int
    training_date: datetime

    model_config = ConfigDict(from_attributes=True)


# Combined schemas for API responses
class RaceWithDetails(Race):
    """Race with all related details."""
    meeting: Optional[Meeting] = None
    participants: List[Participant] = []

    model_config = ConfigDict(from_attributes=True)


class ParticipantWithPrediction(Participant):
    """Participant with prediction data."""
    horse: Optional[Horse] = None
    jockey: Optional[Jockey] = None
    trainer: Optional[Trainer] = None
    prediction: Optional[Prediction] = None

    model_config = ConfigDict(from_attributes=True)


class MeetingWithRaces(Meeting):
    """Meeting with all races."""
    venue: Optional[Venue] = None
    races: List[Race] = []

    model_config = ConfigDict(from_attributes=True)


# Update forward references
Prediction.model_rebuild()
Participant.model_rebuild()
