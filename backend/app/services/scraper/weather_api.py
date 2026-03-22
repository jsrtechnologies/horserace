"""
Weather API integration for Australian race tracks.
Uses OpenWeatherMap API to get weather data for race venues.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


# Australian race track coordinates (Venues)
VENUE_COORDINATES = {
    "Flemington": {"lat": -37.9128, "lon": 144.4286},
    "Randwick": {"lat": -33.8978, "lon": 151.2246},
    "Royal Randwick": {"lat": -33.8978, "lon": 151.2246},
    "Doomben": {"lat": -27.3089, "lon": 153.2372},
    "Eagle Farm": {"lat": -27.4017, "lon": 153.2183},
    "Morphettville": {"lat": -34.9825, "lon": 138.5312},
    "Morphettville Parks": {"lat": -34.9825, "lon": 138.5312},
    "Ascot": {"lat": -31.9505, "lon": 115.8945},
    "Belmont Park": {"lat": -31.9505, "lon": 115.8945},
    "Hobart": {"lat": -42.8821, "lon": 147.3272},
    "Launceston": {"lat": -41.4388, "lon": 147.1415},
    "Sandown": {"lat": -37.9292, "lon": 145.1736},
    "Caulfield": {"lat": -37.8756, "lon": 145.0453},
    "Moonee Valley": {"lat": -37.7567, "lon": 144.9244},
    "Rosehill": {"lat": -33.8267, "lon": 151.0061},
    "Warwick Farm": {"lat": -33.8722, "lon": 150.9611},
    "Hawkesbury": {"lat": -33.6094, "lon": 150.8167},
    "Newcastle": {"lat": -32.9267, "lon": 151.7794},
    "Canterbury": {"lat": -33.9112, "lon": 151.1161},
    "Wyong": {"lat": -33.2808, "lon": 151.4222},
    "Gold Coast": {"lat": -28.0106, "lon": 153.3761},
    "Sunshine Coast": {"lat": -26.6500, "lon": 153.0667},
    "Toowoomba": {"lat": -27.5608, "lon": 151.9536},
    "Rockhampton": {"lat": -23.3747, "lon": 150.5119},
    "Townsville": {"lat": -19.2590, "lon": 146.8169},
    "Cairns": {"lat": -16.9186, "lon": 145.7781},
    "Darwin": {"lat": -12.4634, "lon": 130.8456},
    "Alice Springs": {"lat": -23.6980, "lon": 133.8812},
    "Port Lincoln": {"lat": -34.7250, "lon": 135.8561},
    "Murray Bridge": {"lat": -35.1194, "lon": 139.2556},
    "Geelong": {"lat": -38.1553, "lon": 144.3617},
    "Ballarat": {"lat": -37.5622, "lon": 143.8500},
    "Bendigo": {"lat": -36.7589, "lon": 144.2826},
    "Wagga Wagga": {"lat": -35.1152, "lon": 147.3678},
    "Dubbo": {"lat": -32.2569, "lon": 148.6012},
    "Bathurst": {"lat": -33.4158, "lon": 149.5806},
    "Orange": {"lat": -33.2830, "lon": 149.0992},
    "Tamworth": {"lat": -31.0905, "lon": 150.9186},
    "Coffs Harbour": {"lat": -30.2965, "lon": 153.1145},
    "Grafton": {"lat": -29.6913, "lon": 152.9339},
    "Lismore": {"lat": -28.8147, "lon": 153.2900},
    "Port Macquarie": {"lat": -31.4355, "lon": 152.9089},
    "Wollongong": {"lat": -34.4278, "lon": 150.8931},
    "Kembla Grange": {"lat": -34.4508, "lon": 150.8511},
    "Scone": {"lat": -32.0472, "lon": 150.9125},
    "Muswellbrook": {"lat": -32.2658, "lon": 150.8914},
    "Mudgee": {"lat": -32.5908, "lon": 149.5886},
    "Penrith": {"lat": -33.7511, "lon": 150.6942},
    "Richmond": {"lat": -33.5978, "lon": 150.7528},
    "Goulburn": {"lat": -34.7486, "lon": 149.7233},
    "Queanbeyan": {"lat": -35.3534, "lon": 149.2358},
}


class WeatherAPI:
    """Weather API integration for Australian race tracks."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather API.

        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key or settings.weather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = requests.Session()

    def get_weather_for_venue(self, venue_name: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a race venue.

        Args:
            venue_name: Name of the race venue

        Returns:
            Weather data dictionary or None
        """
        coords = VENUE_COORDINATES.get(venue_name)
        if not coords:
            logger.warning(f"No coordinates found for venue: {venue_name}")
            return self._get_default_weather(venue_name)

        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": self.api_key,
                "units": "metric"
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return self._parse_weather_response(response.json())

        except requests.RequestException as e:
            logger.error(f"Error fetching weather for {venue_name}: {e}")
            return self._get_default_weather(venue_name)

    def get_forecast_for_venue(self, venue_name: str, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a venue on a specific date.

        Args:
            venue_name: Name of the race venue
            date: Date to get forecast for

        Returns:
            Forecast data dictionary or None
        """
        coords = VENUE_COORDINATES.get(venue_name)
        if not coords:
            return None

        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": self.api_key,
                "units": "metric"
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return self._parse_forecast_response(response.json(), date)

        except requests.RequestException as e:
            logger.error(f"Error fetching forecast for {venue_name}: {e}")
            return None

    def _parse_weather_response(self, data: Dict) -> Dict[str, Any]:
        """Parse OpenWeatherMap API response."""
        return {
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "wind_direction": data.get("wind", {}).get("deg"),
            "weather": data.get("weather", [{}])[0].get("main"),
            "description": data.get("weather", [{}])[0].get("description"),
            "icon": data.get("weather", [{}])[0].get("icon"),
            "clouds": data.get("clouds", {}).get("all"),
            "rain": data.get("rain", {}).get("1h", 0),
            "timestamp": datetime.fromtimestamp(data.get("dt", 0))
        }

    def _parse_forecast_response(self, data: Dict, target_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse forecast response and find closest forecast to target date."""
        forecasts = data.get("list", [])

        if not forecasts:
            return None

        # Find forecast closest to target date
        closest = None
        min_diff = float("inf")

        for forecast in forecasts:
            forecast_time = datetime.fromtimestamp(forecast.get("dt", 0))
            diff = abs((forecast_time - target_date).total_seconds())

            if diff < min_diff:
                min_diff = diff
                closest = forecast

        if closest:
            return self._parse_weather_response(closest)

        return None

    def _get_default_weather(self, venue_name: str) -> Dict[str, Any]:
        """Return default weather data when API is unavailable."""
        return {
            "temperature": 22.0,
            "feels_like": 21.0,
            "humidity": 65.0,
            "pressure": 1013.0,
            "wind_speed": 15.0,
            "wind_direction": 270,
            "weather": "Clear",
            "description": "clear sky",
            "icon": "01d",
            "clouds": 10,
            "rain": 0.0,
            "timestamp": datetime.now()
        }

    def get_track_condition(self, venue_name: str, weather_data: Dict[str, Any]) -> str:
        """
        Estimate track condition based on weather and recent rainfall.

        Args:
            venue_name: Name of the race venue
            weather_data: Weather data dictionary

        Returns:
            Estimated track condition string
        """
        rain = weather_data.get("rain", 0)
        humidity = weather_data.get("humidity", 0)
        clouds = weather_data.get("clouds", 0)

        # Simple heuristic for track condition
        if rain > 10 or humidity > 90:
            return "Heavy 10"
        elif rain > 5 or humidity > 80:
            return "Heavy 8"
        elif rain > 2 or humidity > 70:
            return "Soft 6"
        elif clouds > 70:
            return "Soft 5"
        elif clouds > 40:
            return "Good 4"
        else:
            return "Good 3"

    def close(self):
        """Close the session."""
        self.session.close()


# Create a singleton instance
weather_api = WeatherAPI()
