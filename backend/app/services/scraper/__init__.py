"""
Scraper services for Australian horse racing data.
Provides tools to scrape data from various racing websites.
"""

from app.services.scraper.base_scraper import BaseScraper
from app.services.scraper.racing_com_scraper import RacingComScraper
from app.services.scraper.punters_scraper import PuntersScraper
from app.services.scraper.weather_api import WeatherAPI, weather_api, VENUE_COORDINATES
from app.services.scraper.historical_loader import HistoricalDataLoader, load_historical_data, add_upcoming_events
from app.services.scraper.live_update import LiveUpdateService

__all__ = [
    "BaseScraper",
    "RacingComScraper",
    "PuntersScraper",
    "WeatherAPI",
    "weather_api",
    "VENUE_COORDINATES",
    "HistoricalDataLoader",
    "load_historical_data",
    "add_upcoming_events",
    "LiveUpdateService"
]
