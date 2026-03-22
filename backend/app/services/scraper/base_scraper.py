"""
Base scraper class for Australian horse racing data.
Provides common functionality for all scrapers.
"""

import logging
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all racing data scrapers."""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the scraper.

        Args:
            base_url: Base URL for the racing site
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _get(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """
        Make a GET request with retry logic.

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            BeautifulSoup object or None on failure
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()

                # Add random delay to be respectful
                time.sleep(random.uniform(0.5, 1.5))

                return BeautifulSoup(response.text, "html.parser")

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d-%b-%Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_distance(self, distance_str: str) -> Optional[int]:
        """
        Parse distance string to meters.

        Args:
            distance_str: Distance string like "1200m", "1.2km", etc.

        Returns:
            Distance in meters or None
        """
        if not distance_str:
            return None

        distance_str = distance_str.lower().strip()

        # Handle various formats
        if "km" in distance_str:
            try:
                return int(float(distance_str.replace("km", "").strip()) * 1000)
            except ValueError:
                pass
        elif "m" in distance_str:
            try:
                return int(distance_str.replace("m", "").strip())
            except ValueError:
                pass

        # Try to parse as plain number
        try:
            return int(float(distance_str))
        except ValueError:
            pass

        return None

    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        if not text:
            return ""
        return " ".join(text.split()).strip()

    @abstractmethod
    def get_upcoming_meetings(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get upcoming race meetings.

        Args:
            date: Specific date to get meetings for (defaults to today)

        Returns:
            List of meeting dictionaries
        """
        pass

    @abstractmethod
    def get_race_details(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific race.

        Args:
            race_id: Race identifier

        Returns:
            Race details dictionary or None
        """
        pass

    @abstractmethod
    def get_race_participants(self, race_id: str) -> List[Dict[str, Any]]:
        """
        Get participants (horses) for a race.

        Args:
            race_id: Race identifier

        Returns:
            List of participant dictionaries
        """
        pass

    def close(self):
        """Close the session."""
        self.session.close()
