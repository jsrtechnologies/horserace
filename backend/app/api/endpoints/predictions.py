"""
Predictions API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import database
from app.models.schemas import Prediction, PredictionCreate
from app.services.ml.predictor import predictor

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/{race_id}")
def get_predictions(
    race_id: int,
    db: Session = Depends(get_db)
):
    """
    Get predictions for a specific race.
    """
    # Check if race exists
    race = db.query(database.Race).filter(database.Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    # Check if predictions already exist
    existing_predictions = db.query(database.Participant).filter(
        database.Participant.race_id == race_id
    ).join(
        database.Participant.prediction
    ).all()

    if existing_predictions:
        # Return stored predictions
        participants = db.query(database.Participant).filter(
            database.Participant.race_id == race_id
        ).all()

        predictions = []
        for p in participants:
            pred_data = {
                "participant_id": p.id,
                "horse_name": p.horse.name if p.horse else "Unknown",
                "jockey_name": p.jockey.name if p.jockey else "Unknown",
                "trainer_name": p.trainer.name if p.trainer else "Unknown",
                "barrier": p.barrier,
                "weight": p.carried_weight,
                "form": p.form_string
            }

            if p.prediction:
                pred_data.update({
                    "win_probability": p.prediction.win_probability * 100,
                    "place_probability": p.prediction.place_probability * 100 if p.prediction.place_probability else 0,
                    "predicted_position": p.prediction.predicted_position,
                    "confidence_score": p.prediction.confidence_score,
                    "factors": p.prediction.factors
                })
            else:
                pred_data.update({
                    "win_probability": 0,
                    "place_probability": 0,
                    "predicted_position": 0,
                    "confidence_score": 0,
                    "factors": {"positive": [], "negative": []}
                })

            predictions.append(pred_data)

        # Sort by win probability
        predictions.sort(key=lambda x: x["win_probability"], reverse=True)

        return {
            "race_id": race_id,
            "race_name": race.race_name,
            "distance": race.distance,
            "race_time": race.race_time.isoformat() if race.race_time else None,
            "venue": race.meeting.venue.name if race.meeting and race.meeting.venue else "Unknown",
            "predictions": predictions
        }

    # Generate new predictions
    return generate_predictions(race_id, db)


@router.post("/generate/{race_id}")
def generate_predictions(
    race_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate new predictions for a race.
    """
    # Check if race exists
    race = db.query(database.Race).filter(database.Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    # Get predictions from predictor
    predictions = predictor.predict_race(race_id, db)

    if not predictions:
        raise HTTPException(status_code=500, detail="Failed to generate predictions")

    # Save predictions to database
    for pred in predictions:
        participant = db.query(database.Participant).filter(
            database.Participant.id == pred["participant_id"]
        ).first()

        if participant:
            # Check if prediction exists
            existing = db.query(database.Prediction).filter(
                database.Prediction.participant_id == participant.id
            ).first()

            if existing:
                # Update existing prediction
                existing.win_probability = pred["win_probability"] / 100
                existing.place_probability = pred["place_probability"] / 100 if pred.get("place_probency") else None
                existing.predicted_position = pred["predicted_position"]
                existing.confidence_score = pred["confidence_score"]
                existing.factors = pred.get("factors")
                existing.generated_at = datetime.now()
            else:
                # Create new prediction
                db_prediction = database.Prediction(
                    participant_id=participant.id,
                    win_probability=pred["win_probability"] / 100,
                    place_probability=pred["place_probability"] / 100 if pred.get("place_probability") else None,
                    predicted_position=pred["predicted_position"],
                    confidence_score=pred["confidence_score"],
                    factors=pred.get("factors")
                )
                db.add(db_prediction)

    db.commit()

    return {
        "race_id": race_id,
        "race_name": race.race_name,
        "distance": race.distance,
        "race_time": race.race_time.isoformat() if race.race_time else None,
        "venue": race.meeting.venue.name if race.meeting and race.meeting.venue else "Unknown",
        "predictions": predictions
    }


@router.get("/best-bet/today")
def get_best_bets_today(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=2, ge=1, le=7, description="Number of days to include"),
    min_confidence: float = Query(default=10, ge=0, le=100, description="Minimum confidence score"),
    db: Session = Depends(get_db)
):
    """
    Get best bets for today based on high confidence predictions.
    """
    from datetime import timedelta
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today_start + timedelta(days=days)

    # Get today's and upcoming races with predictions
    races = db.query(database.Race).filter(
        database.Race.race_time >= today_start,
        database.Race.race_time <= end_date,
        database.Race.status == "scheduled"
    ).all()

    best_bets = []

    for race in races:
        # Get predictions for this race
        participants = db.query(database.Participant).filter(
            database.Participant.race_id == race.id
        ).join(
            database.Prediction
        ).filter(
            database.Prediction.win_probability <= 1.0  # Filter out corrupted predictions
        ).order_by(
            database.Prediction.confidence_score.desc()
        ).limit(3).all()

        if participants and participants[0].prediction:
            top = participants[0].prediction

            # Include if confidence is above threshold
            if top.confidence_score and top.confidence_score >= min_confidence:
                best_bets.append({
                    "race_id": race.id,
                    "race_number": race.race_number,
                    "race_name": race.race_name,
                    "distance": race.distance,
                    "race_time": race.race_time.isoformat() if race.race_time else None,
                    "venue": race.meeting.venue.name if race.meeting and race.meeting.venue else "Unknown",
                    "horse_name": top.participant.horse.name if top.participant.horse else "Unknown",
                    "jockey_name": top.participant.jockey.name if top.participant.jockey else "Unknown",
                    "win_probability": round(top.win_probability * 100, 2),
                    "confidence_score": round(top.confidence_score, 2),
                    "factors": top.factors
                })

    # Sort by confidence score
    best_bets.sort(key=lambda x: x["confidence_score"], reverse=True)

    return {
        "count": len(best_bets),
        "best_bets": best_bets[:limit]
    }


@router.post("/clear/{race_id}")
def clear_predictions(
    race_id: int,
    db: Session = Depends(get_db)
):
    """
    Clear predictions for a race.
    """
    # Get all participants for this race
    participants = db.query(database.Participant).filter(
        database.Participant.race_id == race_id
    ).all()

    deleted_count = 0

    for participant in participants:
        # Delete prediction if exists
        if participant.prediction:
            db.delete(participant.prediction)
            deleted_count += 1

    db.commit()

    return {
        "race_id": race_id,
        "deleted": deleted_count,
        "message": f"Cleared {deleted_count} predictions"
    }
