"""
Model trainer for horse racing predictions.
Handles training, validation, and model persistence.
"""

import logging
import os
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None

from app.services.ml.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Trainer for horse racing prediction model."""

    def __init__(self, model_path: str = "../../data/models/horse_model.pkl"):
        """
        Initialize the model trainer.

        Args:
            model_path: Path to save/load the model
        """
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_engineer = FeatureEngineer()
        self.feature_names = []
        self.is_trained = False
        self.model_version = "1.0.0"

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Train the prediction model.

        Args:
            X: Feature DataFrame
            y: Target variable (win = 1, lose = 0)
            test_size: Test set proportion
            validate: Whether to validate the model

        Returns:
            Dictionary with training results
        """
        try:
            # Prepare data
            self.feature_names = X.columns.tolist()

            # Handle missing values
            X = X.fillna(0)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Define model parameters
            params = {
                "objective": "binary:logistic",
                "eval_metric": "logloss",
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "min_child_weight": 3,
                "seed": 42,
                "n_jobs": -1
            }

            # Train XGBoost model
            self.model = xgb.XGBClassifier(**params, n_estimators=100)
            self.model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_test_scaled, y_test)],
                verbose=False
            )

            # Evaluate
            results = {
                "status": "success",
                "model_version": self.model_version,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "features_used": len(self.feature_names)
            }

            if validate:
                # Predictions
                y_pred = self.model.predict(X_test_scaled)
                y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

                # Metrics
                results["accuracy"] = accuracy_score(y_test, y_pred)
                results["log_loss"] = log_loss(y_test, y_pred_proba)

                # Top-1, Top-3 accuracy for race-level predictions
                results["top_1_accuracy"] = self._calculate_top_k_accuracy(
                    X_test_scaled, y_test, k=1
                )
                results["top_3_accuracy"] = self._calculate_top_k_accuracy(
                    X_test_scaled, y_test, k=3
                )

                # Cross-validation
                cv_scores = cross_val_score(
                    self.model, X_train_scaled, y_train, cv=5, scoring="accuracy"
                )
                results["cv_accuracy_mean"] = cv_scores.mean()
                results["cv_accuracy_std"] = cv_scores.std()

            # Save model
            self._save_model()

            self.is_trained = True
            logger.info(f"Model trained successfully. Accuracy: {results.get('accuracy', 'N/A')}")

            return results

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"status": "error", "message": str(e)}

    def _calculate_top_k_accuracy(
        self,
        X_test: np.ndarray,
        y_test: pd.Series,
        k: int
    ) -> float:
        """
        Calculate top-k accuracy (winner's position in top k predictions).

        Args:
            X_test: Test features
            y_test: True labels
            k: Top k predictions

        Returns:
            Top-k accuracy
        """
        try:
            # Get probabilities for winning
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]

            # Sort by probability (descending)
            sorted_indices = np.argsort(y_pred_proba)[::-1]

            # Check if actual winner is in top k
            # Assuming y_test contains binary labels (1 = winner)
            winner_indices = np.where(y_test == 1)[0]

            correct = 0
            for winner_idx in winner_indices:
                if winner_idx in sorted_indices[:k]:
                    correct += 1

            return correct / max(len(winner_indices), 1) if len(winner_indices) > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating top-k accuracy: {e}")
            return 0.0

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict win probabilities.

        Args:
            X: Feature DataFrame

        Returns:
            Array of win probabilities
        """
        if not self.is_trained:
            self._load_model()

        if self.model is None:
            logger.warning("Model not loaded, returning random probabilities")
            return np.random.rand(len(X))

        try:
            X = X.fillna(0)
            X_scaled = self.scaler.transform(X)
            return self.model.predict_proba(X_scaled)[:, 1]

        except Exception as e:
            logger.error(f"Error predicting probabilities: {e}")
            return np.random.rand(len(X))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict winners.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predictions (0 or 1)
        """
        if not self.is_trained:
            self._load_model()

        if self.model is None:
            return np.zeros(len(X))

        try:
            X = X.fillna(0)
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)

        except Exception as e:
            logger.error(f"Error predicting: {e}")
            return np.zeros(len(X))

    def _save_model(self) -> bool:
        """Save the trained model to disk."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "model_version": self.model_version,
                "trained_at": datetime.now().isoformat()
            }

            joblib.dump(model_data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def _load_model(self) -> bool:
        """Load the trained model from disk."""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Model file not found: {self.model_path}")
                return False

            model_data = joblib.load(self.model_path)

            self.model = model_data.get("model")
            self.scaler = model_data.get("scaler")
            self.feature_names = model_data.get("feature_names", [])
            self.model_version = model_data.get("model_version", "1.0.0")

            self.is_trained = self.model is not None
            logger.info(f"Model loaded from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from trained model."""
        if not self.is_trained:
            return pd.DataFrame()

        try:
            importance = self.model.feature_importances_
            return pd.DataFrame({
                "feature": self.feature_names,
                "importance": importance
            }).sort_values("importance", ascending=False)

        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return pd.DataFrame()

    def backtest(
        self,
        historical_data: pd.DataFrame,
        predictions_col: str = "predicted_prob",
        actual_col: str = "won"
    ) -> Dict[str, Any]:
        """
        Backtest the model on historical data.

        Args:
            historical_data: Historical race data
            predictions_col: Column name for predictions
            actual_col: Column name for actual outcomes

        Returns:
            Backtest results
        """
        try:
            # Get predictions
            X = historical_data.drop(columns=[predictions_col, actual_col], errors="ignore")
            y = historical_data[actual_col]

            y_pred_proba = self.predict_proba(X)
            y_pred = (y_pred_proba > 0.5).astype(int)

            # Calculate metrics
            results = {
                "total_races": len(historical_data),
                "accuracy": accuracy_score(y, y_pred),
                "top_1_accuracy": self._calculate_top_k_accuracy(
                    self.scaler.transform(X.fillna(0)), y, k=1
                ),
                "top_3_accuracy": self._calculate_top_k_accuracy(
                    self.scaler.transform(X.fillna(0)), y, k=3
                ),
                "avg_predicted_prob": y_pred_proba.mean(),
                "avg_actual_win_rate": y.mean()
            }

            # ROI calculation (if odds available)
            if "odds" in historical_data.columns:
                roi = self._calculate_roi(y_pred_proba, y, historical_data["odds"])
                results["roi"] = roi

            return results

        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {"status": "error", "message": str(e)}

    def _calculate_roi(
        self,
        predictions: np.ndarray,
        actual: pd.Series,
        odds: pd.Series
    ) -> float:
        """
        Calculate Return on Investment for predictions.

        Args:
            predictions: Predicted probabilities
            actual: Actual outcomes
            odds: Betting odds

        Returns:
            ROI percentage
        """
        try:
            # Only bet on predictions with probability > 0.3
            threshold = 0.3
            bet_mask = predictions > threshold

            if not bet_mask.any():
                return 0.0

            # Calculate returns
            wins = (actual[bet_mask] == 1)
            returns = odds[bet_mask].where(wins, 0) - 1  # Profit for winning bets
            losses = (~wins).sum()  # Loss for losing bets

            total_staked = bet_mask.sum()
            total_returned = returns.sum() + (total_staked - losses)

            roi = (total_returned / total_staked - 1) * 100 if total_staked > 0 else 0.0
            return roi

        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return 0.0


# Create singleton instance
model_trainer = ModelTrainer()
