"""
Predictor service for generating horse racing predictions.
Uses trained ML model to generate predictions for race participants.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.services.ml.feature_engineering import FeatureEngineer
from app.services.ml.model_trainer import ModelTrainer
from app.core.database import SessionLocal
from app.models import database

logger = logging.getLogger(__name__)


class Predictor:
    """Horse racing prediction service."""

    def __init__(self):
        """Initialize the predictor."""
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        self.model_loaded = False

    def load_model(self) -> bool:
        """Load the trained model."""
        try:
            self.model_loaded = self.model_trainer._load_model()
            return self.model_loaded
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def predict_race(
        self,
        race_id: int,
        db: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for a race.

        Args:
            race_id: Race ID to predict
            db: Database session

        Returns:
            List of predictions with probabilities and factors
        """
        if db is None:
            db = SessionLocal()

        try:
            # Get race details
            race = db.query(database.Race).filter(database.Race.id == race_id).first()
            if not race:
                logger.warning(f"Race {race_id} not found")
                return []

            # Get race info
            race_info = {
                "distance": race.distance,
                "race_class": race.race_class,
                "prize_money": race.prize_money,
                "track_rating": race.meeting.track_rating if race.meeting else "Good 4",
                "track_condition": race.meeting.track_condition if race.meeting else None,
                "weather": race.meeting.weather if race.meeting else None
            }

            # Get participants
            participants = db.query(database.Participant).filter(
                database.Participant.race_id == race_id
            ).all()

            if not participants:
                logger.warning(f"No participants found for race {race_id}")
                return []

            # Get statistics
            jockey_stats = self._get_jockey_statistics(db)
            trainer_stats = self._get_trainer_statistics(db)
            horse_history = self._get_horse_history(db, [p.horse_id for p in participants])

            # Create participant data dictionaries
            participant_data = []
            for p in participants:
                data = {
                    "id": p.id,
                    "horse_id": p.horse_id,
                    "jockey_id": p.jockey_id,
                    "trainer_id": p.trainer_id,
                    "barrier": p.barrier,
                    "carried_weight": p.carried_weight,
                    "rating": p.rating,
                    "form_string": p.form_string,
                    "days_since_last_run": p.days_since_last_run,
                    "weight_change": p.weight_change,
                    "horse_name": p.horse.name if p.horse else "Unknown",
                    "jockey_name": p.jockey.name if p.jockey else "Unknown",
                    "trainer_name": p.trainer.name if p.trainer else "Unknown",
                    "age": p.horse.age if p.horse else 4
                }
                participant_data.append(data)

            # Create features
            features_df = self.feature_engineer.create_features(
                participant_data,
                race_info,
                jockey_stats,
                trainer_stats,
                horse_history
            )

            # Load model and predict
            if not self.model_loaded:
                self.load_model()

            if self.model_trainer.is_trained:
                # Get probabilities
                probabilities = self.model_trainer.predict_proba(features_df)

                # Normalize probabilities to sum to 1
                probabilities = probabilities / probabilities.sum()

                # Generate predictions
                predictions = []
                for i, (participant, prob) in enumerate(zip(participant_data, probabilities)):
                    prediction = {
                        "participant_id": participant["id"],
                        "horse_name": participant["horse_name"],
                        "jockey_name": participant["jockey_name"],
                        "trainer_name": participant["trainer_name"],
                        "barrier": participant["barrier"],
                        "weight": participant["carried_weight"],
                        "form": participant["form_string"],
                        "win_probability": round(prob * 100, 2),
                        "place_probability": round(min(prob * 3, 1) * 100, 2),  # Simplified place calc
                        "predicted_position": i + 1,
                        "confidence_score": round(prob * 100, 2),
                        "factors": self._generate_factors(
                            participant,
                            features_df.iloc[i].to_dict(),
                            prob
                        )
                    }
                    predictions.append(prediction)

                # Sort by probability
                predictions.sort(key=lambda x: x["win_probability"], reverse=True)

                # Update predicted positions after sorting
                for i, pred in enumerate(predictions):
                    pred["predicted_position"] = i + 1

                return predictions

            else:
                # Return placeholder predictions if model not available
                logger.warning("Model not available, returning placeholder predictions")
                return self._generate_placeholder_predictions(participant_data)

        except Exception as e:
            logger.error(f"Error predicting race {race_id}: {e}")
            return []
        finally:
            if db:
                db.close()

    def _get_jockey_statistics(self, db) -> Dict[int, Dict[str, Any]]:
        """Get jockey statistics from database."""
        stats = {}

        try:
            jockey_stats = db.query(database.JockeyStatistics).all()
            for stat in jockey_stats:
                stats[stat.jockey_id] = {
                    "win_rate": stat.win_rate or 0.1,
                    "place_rate": stat.place_rate or 0.3,
                    "strike_rate_30_days": stat.strike_rate_30_days or 0.1,
                    "wet_track_wins": stat.wet_track_wins or 0,
                    "total_rides": stat.total_rides or 0
                }
        except Exception as e:
            logger.error(f"Error getting jockey statistics: {e}")

        return stats

    def _get_trainer_statistics(self, db) -> Dict[int, Dict[str, Any]]:
        """Get trainer statistics from database."""
        stats = {}

        try:
            trainer_stats = db.query(database.TrainerStatistics).all()
            for stat in trainer_stats:
                stats[stat.trainer_id] = {
                    "win_rate": stat.win_rate or 0.1,
                    "place_rate": stat.place_rate or 0.3,
                    "strike_rate_30_days": stat.strike_rate_30_days or 0.1,
                    "wet_track_wins": stat.wet_track_wins or 0,
                    "metro_wins": stat.metro_wins or 0,
                    "total_runners": stat.total_runners or 0
                }
        except Exception as e:
            logger.error(f"Error getting trainer statistics: {e}")

        return stats

    def _get_horse_history(
        self,
        db,
        horse_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Get horse race history from database."""
        history = {}

        try:
            # Get all participants for these horses
            participants = db.query(database.Participant).filter(
                database.Participant.horse_id.in_(horse_ids)
            ).all()

            # Get results for these participants
            participant_ids = [p.id for p in participants]
            results = db.query(database.RaceResult).filter(
                database.RaceResult.participant_id.in_(participant_ids)
            ).all()

            # Create result lookup
            result_lookup = {r.participant_id: r for r in results}

            # Build history by horse
            for participant in participants:
                horse_id = participant.horse_id
                if horse_id not in history:
                    history[horse_id] = []

                result = result_lookup.get(participant.id)
                if result:
                    race = participant.race
                    history[horse_id].append({
                        "position": result.finishing_position,
                        "distance": race.distance if race else 0,
                        "track_rating": race.meeting.track_rating if race and race.meeting else "Good 4",
                        "date": race.race_time if race else None
                    })

            # Sort by date (most recent first)
            for horse_id in history:
                history[horse_id].sort(
                    key=lambda x: x.get("date", datetime.min),
                    reverse=True
                )

        except Exception as e:
            logger.error(f"Error getting horse history: {e}")

        return history

    def _generate_factors(
        self,
        participant: Dict[str, Any],
        features: Dict[str, Any],
        probability: float
    ) -> Dict[str, Any]:
        """Generate explanatory factors for the prediction."""
        factors = {
            "positive": [],
            "negative": []
        }

        try:
            # Positive factors
            if features.get("form_score", 0) > 7:
                factors["positive"].append("Strong recent form")

            if features.get("jockey_win_rate", 0) > 0.15:
                factors["positive"].append("High-performing jockey")

            if features.get("trainer_win_rate", 0) > 0.15:
                factors["positive"].append("Successful trainer")

            if features.get("horse_win_rate", 0) > 0.2:
                factors["positive"].append("Good winning record")

            if features.get("distance_suitable", 0) == 1:
                factors["positive"].append("Suited to distance")

            if features.get("barrier_advantage", 0) > 0.7:
                factors["positive"].append("Favorable barrier draw")

            # Negative factors
            if features.get("days_since_last_run", 0) > 90:
                factors["negative"].append("No recent runs")

            if features.get("first_up", 0) == 1 and features.get("horse_total_races", 0) == 0:
                factors["negative"].append("First-up runner")

            if features.get("jockey_win_rate", 0) < 0.05:
                factors["negative"].append("Inexperienced jockey")

            if features.get("distance_delta", 0) > 400:
                factors["negative"].append("Unsuitable distance")

        except Exception as e:
            logger.error(f"Error generating factors: {e}")

        return factors

    def _generate_placeholder_predictions(
        self,
        participants: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate placeholder predictions when model is unavailable."""
        predictions = []

        # Simple random but somewhat realistic predictions
        base_probs = np.random.dirichlet(np.ones(len(participants)))

        for i, (participant, prob) in enumerate(zip(participants, base_probs)):
            prediction = {
                "participant_id": participant["id"],
                "horse_name": participant["horse_name"],
                "jockey_name": participant["jockey_name"],
                "trainer_name": participant["trainer_name"],
                "barrier": participant["barrier"],
                "weight": participant["carried_weight"],
                "form": participant["form_string"],
                "win_probability": round(prob * 100, 2),
                "place_probability": round(min(prob * 3, 1) * 100, 2),
                "predicted_position": i + 1,
                "confidence_score": round(prob * 100, 2),
                "factors": {"positive": [], "negative": []}
            }
            predictions.append(prediction)

        predictions.sort(key=lambda x: x["win_probability"], reverse=True)

        for i, pred in enumerate(predictions):
            pred["predicted_position"] = i + 1

        return predictions


# Create singleton instance
predictor = Predictor()
