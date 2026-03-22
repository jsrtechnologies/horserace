"""
Script to generate predictions for all upcoming races.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import database
from app.services.ml.predictor import Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_predictions_for_upcoming_races(days: int = 7) -> dict:
    """
    Generate predictions for all upcoming races in the next N days.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        Statistics about prediction generation
    """
    db = SessionLocal()
    predictor = Predictor()
    
    stats = {
        "races_processed": 0,
        "predictions_generated": 0,
        "errors": []
    }
    
    try:
        # Get upcoming scheduled races
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today + timedelta(days=days)
        
        races = db.query(database.Race).filter(
            database.Race.race_time >= today,
            database.Race.race_time < end_date,
            database.Race.status == "scheduled"
        ).all()
        
        logger.info(f"Found {len(races)} upcoming scheduled races")
        
        for race in races:
            try:
                # Check if predictions already exist
                existing = db.query(database.Prediction).join(database.Participant).filter(
                    database.Participant.race_id == race.id
                ).first()
                
                if existing:
                    logger.debug(f"Predictions already exist for race {race.id}")
                    stats["races_processed"] += 1
                    continue
                
                # Generate predictions for this race
                predictions = predictor.predict_race(race.id, db)
                
                # Save predictions to database
                for pred_data in predictions:
                    participant_id = pred_data["participant_id"]
                    
                    # Get or create prediction
                    participant = db.query(database.Participant).filter(
                        database.Participant.id == participant_id
                    ).first()
                    
                    if not participant:
                        continue
                    
                    # Check if prediction exists
                    existing_pred = db.query(database.Prediction).filter(
                        database.Prediction.participant_id == participant_id
                    ).first()
                    
                    if not existing_pred:
                        prediction = database.Prediction(
                            participant_id=participant_id,
                            win_probability=pred_data["win_probability"],
                            place_probability=pred_data.get("place_probability", 0),
                            predicted_position=pred_data.get("predicted_position"),
                            confidence_score=pred_data["confidence_score"],
                            model_version="v1.0",
                            factors=pred_data.get("factors", {})
                        )
                        db.add(prediction)
                        stats["predictions_generated"] += 1
                
                db.commit()
                stats["races_processed"] += 1
                
                logger.info(f"Generated predictions for {race.meeting.venue.name} Race {race.race_number}")
                
            except Exception as e:
                error_msg = f"Error processing race {race.id}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                db.rollback()
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        stats["errors"].append(str(e))
        
    finally:
        db.close()
    
    return stats


if __name__ == "__main__":
    print("Generating predictions for upcoming races...")
    stats = generate_predictions_for_upcoming_races(days=7)
    print(f"\nResults:")
    print(f"  Races processed: {stats['races_processed']}")
    print(f"  Predictions generated: {stats['predictions_generated']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
        print(f"  First error: {stats['errors'][0]}")
