from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings and configuration."""

    # Database - Using PostgreSQL for local development
    database_url: str = "postgresql://sreeni.chinthakunta@localhost:5432/horse_racing_db"

    # API
    api_title: str = "AusRace Predictor AI API"
    api_version: str = "1.0.0"
    api_description: str = "Australian Horse Racing Prediction API"

    # Scraping
    scraping_interval_minutes: int = 30
    racing_com_url: str = "https://www.racing.com"
    punters_url: str = "https://www.punters.com.au"

    # Weather API (using OpenWeatherMap or similar)
    weather_api_key: Optional[str] = None
    weather_api_url: str = "https://api.openweathermap.org/data/2.5"

    # ML Model
    model_path: str = "../../data/models/horse_model.pkl"
    model_retrain_days: int = 7

    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
