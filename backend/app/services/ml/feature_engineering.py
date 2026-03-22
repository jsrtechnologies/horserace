"""
Feature engineering for horse racing prediction.
Creates features from raw race and horse data for ML model training.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineer features from horse racing data."""

    def __init__(self):
        """Initialize the feature engineer."""
        self.feature_names = []

    def create_features(
        self,
        participants: List[Dict[str, Any]],
        race_info: Dict[str, Any],
        jockey_stats: Dict[int, Dict[str, Any]],
        trainer_stats: Dict[int, Dict[str, Any]],
        horse_history: Dict[int, List[Dict[str, Any]]]
    ) -> pd.DataFrame:
        """
        Create feature matrix from participant data.

        Args:
            participants: List of participant dictionaries
            race_info: Race information dictionary
            jockey_stats: Jockey statistics by jockey_id
            trainer_stats: Trainer statistics by trainer_id
            horse_history: Historical race data by horse_id

        Returns:
            DataFrame with features for each participant
        """
        features = []

        for participant in participants:
            feat = {}

            # Race-level features
            feat["distance"] = race_info.get("distance", 0)
            feat["race_class_numeric"] = self._encode_race_class(race_info.get("race_class"))
            feat["prize_money"] = race_info.get("prize_money", 0)
            feat["track_rating_numeric"] = self._encode_track_rating(race_info.get("track_rating"))
            feat["is_dry_track"] = 1 if self._is_dry_track(race_info.get("track_rating")) else 0
            feat["is_wet_track"] = 1 if self._is_wet_track(race_info.get("track_rating")) else 0

            # Participant-level features
            feat["barrier"] = participant.get("barrier", 0)
            feat["barrier_advantage"] = self._calculate_barrier_advantage(
                participant.get("barrier", 0),
                race_info.get("distance", 0)
            )
            feat["carried_weight"] = participant.get("carried_weight", 0)
            feat["weight_kg"] = participant.get("carried_weight", 55)  # Default weight
            feat["rating"] = participant.get("rating", 0)
            feat["age"] = participant.get("age", 4)

            # Form features
            form_string = participant.get("form_string", "")
            feat["form_score"] = self._calculate_form_score(form_string)
            feat["last_run_position"] = self._get_last_position(form_string)
            feat["days_since_last_run"] = participant.get("days_since_last_run", 30)
            feat["weight_change"] = participant.get("weight_change", 0)
            feat["has_form"] = 1 if form_string else 0
            feat["first_up"] = 1 if participant.get("days_since_last_run", 0) > 60 else 0

            # Jockey features
            jockey_id = participant.get("jockey_id")
            if jockey_id and jockey_id in jockey_stats:
                stats = jockey_stats[jockey_id]
                feat["jockey_win_rate"] = stats.get("win_rate", 0)
                feat["jockey_place_rate"] = stats.get("place_rate", 0)
                feat["jockey_strike_rate_30"] = stats.get("strike_rate_30_days", 0)
                feat["jockey_wet_track_wins"] = stats.get("wet_track_wins", 0)
                feat["jockey_total_rides"] = stats.get("total_rides", 0)
            else:
                feat["jockey_win_rate"] = 0.1
                feat["jockey_place_rate"] = 0.3
                feat["jockey_strike_rate_30"] = 0.1
                feat["jockey_wet_track_wins"] = 0
                feat["jockey_total_rides"] = 0

            # Trainer features
            trainer_id = participant.get("trainer_id")
            if trainer_id and trainer_id in trainer_stats:
                stats = trainer_stats[trainer_id]
                feat["trainer_win_rate"] = stats.get("win_rate", 0)
                feat["trainer_place_rate"] = stats.get("place_rate", 0)
                feat["trainer_strike_rate_30"] = stats.get("strike_rate_30_days", 0)
                feat["trainer_wet_track_wins"] = stats.get("wet_track_wins", 0)
                feat["trainer_metro_wins"] = stats.get("metro_wins", 0)
                feat["trainer_total_runners"] = stats.get("total_runners", 0)
            else:
                feat["trainer_win_rate"] = 0.1
                feat["trainer_place_rate"] = 0.3
                feat["trainer_strike_rate_30"] = 0.1
                feat["trainer_wet_track_wins"] = 0
                feat["trainer_metro_wins"] = 0
                feat["trainer_total_runners"] = 0

            # Horse history features
            horse_id = participant.get("horse_id")
            if horse_id and horse_id in horse_history:
                history = horse_history[horse_id]
                feat["horse_total_races"] = len(history)
                feat["horse_wins"] = sum(1 for h in history if h.get("position") == 1)
                feat["horse_win_rate"] = feat["horse_wins"] / max(len(history), 1)
                feat["horse_places"] = sum(1 for h in history if h.get("position", 0) <= 3)
                feat["horse_place_rate"] = feat["horse_places"] / max(len(history), 1)
                feat["horse_avg_position"] = np.mean([h.get("position", 5) for h in history]) if history else 5

                # Distance suitability
                current_distance = race_info.get("distance", 0)
                avg_winning_distance = np.mean([
                    h.get("distance", 0) for h in history if h.get("position") == 1
                ]) if any(h.get("position") == 1 for h in history) else current_distance
                feat["distance_delta"] = abs(current_distance - avg_winning_distance)
                feat["distance_suitable"] = 1 if abs(current_distance - avg_winning_distance) < 200 else 0

                # Wet/dry track performance
                wet_runs = [h for h in history if self._is_wet_track(h.get("track_rating"))]
                feat["horse_wet_races"] = len(wet_runs)
                feat["horse_wet_wins"] = sum(1 for h in wet_runs if h.get("position") == 1)
                feat["horse_wet_win_rate"] = feat["horse_wet_wins"] / max(len(wet_runs), 1)

                # Recent form
                recent_runs = history[:5]
                feat["recent_form_score"] = self._calculate_form_score_from_history(recent_runs)
            else:
                feat["horse_total_races"] = 0
                feat["horse_wins"] = 0
                feat["horse_win_rate"] = 0
                feat["horse_places"] = 0
                feat["horse_place_rate"] = 0
                feat["horse_avg_position"] = 5
                feat["distance_delta"] = 0
                feat["distance_suitable"] = 0
                feat["horse_wet_races"] = 0
                feat["horse_wet_wins"] = 0
                feat["horse_wet_win_rate"] = 0
                feat["recent_form_score"] = 0

            # Combined/synergy features
            feat["jockey_trainer_combo"] = feat["jockey_win_rate"] * feat["trainer_win_rate"]
            feat["experience_score"] = feat["jockey_total_rides"] + feat["trainer_total_runners"]
            feat["form_and_class"] = feat["form_score"] * feat["race_class_numeric"]

            features.append(feat)

        self.feature_names = list(features[0].keys()) if features else []
        return pd.DataFrame(features)

    def _encode_race_class(self, race_class: Optional[str]) -> float:
        """Encode race class as numeric value."""
        if not race_class:
            return 5.0

        race_class = race_class.lower()

        if "group 1" in race_class or "g1" in race_class:
            return 1.0
        elif "group 2" in race_class or "g2" in race_class:
            return 2.0
        elif "group 3" in race_class or "g3" in race_class:
            return 3.0
        elif "listed" in race_class:
            return 4.0
        else:
            return 5.0

    def _encode_track_rating(self, track_rating: Optional[str]) -> float:
        """Encode track rating (Good 4, Soft 5, Heavy 8, etc.) to numeric."""
        if not track_rating:
            return 4.0

        track_rating = track_rating.lower()

        if "heavy" in track_rating:
            if "10" in track_rating or "9" in track_rating:
                return 9.5
            elif "8" in track_rating:
                return 8.0
            return 7.0
        elif "soft" in track_rating:
            if "6" in track_rating:
                return 6.0
            elif "5" in track_rating:
                return 5.0
            return 5.5
        elif "good" in track_rating:
            if "4" in track_rating:
                return 4.0
            elif "3" in track_rating:
                return 3.0
            return 4.0
        elif "synthetic" in track_rating or "poly" in track_rating:
            return 2.0
        elif "dirt" in track_rating:
            return 3.0

        return 4.0

    def _is_dry_track(self, track_rating: Optional[str]) -> bool:
        """Check if track is dry (Good or Synthetic)."""
        if not track_rating:
            return True

        track_rating = track_rating.lower()
        return "good" in track_rating or "synthetic" in track_rating or "poly" in track_rating

    def _is_wet_track(self, track_rating: Optional[str]) -> bool:
        """Check if track is wet (Soft or Heavy)."""
        if not track_rating:
            return False

        track_rating = track_rating.lower()
        return "soft" in track_rating or "heavy" in track_rating

    def _calculate_barrier_advantage(self, barrier: int, distance: int) -> float:
        """Calculate barrier advantage based on barrier draw and distance."""
        if not barrier:
            return 0.0

        # Inner barriers are advantageous in shorter races
        # Outer barriers are less disadvantageous in longer races
        if distance < 1200:
            return (14 - barrier) / 14  # Inner barrier advantage
        elif distance < 1600:
            return (16 - barrier) / 16
        else:
            return (18 - barrier) / 18

    def _calculate_form_score(self, form_string: str) -> float:
        """Calculate form score from form string (e.g., "1-2-3-1-4")."""
        if not form_string:
            return 0.0

        try:
            positions = [int(x.strip()) for x in form_string.split("-") if x.strip().isdigit()]
            if not positions:
                return 0.0

            # Weight recent runs more heavily
            weights = [1.0, 1.5, 2.0, 2.5, 3.0][:len(positions)]
            weighted_score = sum(w / max(p, 1) for p, w in zip(positions, weights))

            return weighted_score / sum(weights) * 10

        except (ValueError, IndexError):
            return 0.0

    def _get_last_position(self, form_string: str) -> int:
        """Get position from most recent run."""
        if not form_string:
            return 5

        try:
            positions = form_string.split("-")
            if positions:
                return int(positions[0].strip())
        except (ValueError, IndexError):
            pass

        return 5

    def _calculate_form_score_from_history(self, history: List[Dict]) -> float:
        """Calculate form score from horse history."""
        if not history:
            return 0.0

        try:
            positions = [h.get("position", 5) for h in history]
            weights = [3.0, 2.5, 2.0, 1.5, 1.0][:len(positions)]

            weighted_score = sum(w / max(p, 1) for p, w in zip(positions, weights))
            return weighted_score / sum(weights) * 10

        except (ValueError, IndexError):
            return 0.0

    def normalize_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize features for model input.

        Args:
            features_df: Feature DataFrame

        Returns:
            Normalized feature DataFrame
        """
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        normalized = scaler.fit_transform(features_df)

        return pd.DataFrame(normalized, columns=features_df.columns)

    def get_feature_importance(self, model, feature_names: List[str]) -> pd.DataFrame:
        """
        Get feature importance from trained model.

        Args:
            model: Trained model
            feature_names: List of feature names

        Returns:
            DataFrame with feature importance
        """
        try:
            if hasattr(model, "feature_importances_"):
                importance = model.feature_importances_
                return pd.DataFrame({
                    "feature": feature_names,
                    "importance": importance
                }).sort_values("importance", ascending=False)
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")

        return pd.DataFrame()
