"""
Machine Learning services for horse racing predictions.
"""

import logging
logger = logging.getLogger(__name__)

# Try to import ML dependencies, but don't fail if not available
try:
    from app.services.ml.feature_engineering import FeatureEngineer
    from app.services.ml.model_trainer import ModelTrainer, model_trainer
    from app.services.ml.predictor import Predictor, predictor
    
    __all__ = [
        "FeatureEngineer",
        "ModelTrainer",
        "model_trainer",
        "Predictor",
        "predictor"
    ]
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML dependencies not available: {e}")
    ML_AVAILABLE = False
    __all__ = []
