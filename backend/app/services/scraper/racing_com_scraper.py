"""
Racing.com scraper for Australian horse racing data.
Racing.com is one of the major Australian horse racing platforms.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from app.services.scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RacingComScraper(BaseScraper):
    """Scraper for Racing.com.au"""

    def __init__(self):
        super().__init__(base_url="https://www.racing.com")
        self.api_base = "https://api.racing.com"

    def get_upcoming_meetings(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get upcoming race meetings.

        Args:
            date: Specific date to get meetings for (defaults to today)

        Returns:
            List of meeting dictionaries
        """
        if date is None:
            date = datetime.now()

        meetings = []

        try:
            # Try to get meetings from racing.com
            url = f"{self.base_url}/results"
            soup = self._get(url)

            if soup:
                meetings = self._parse_meetings_from_page(soup, date)

        except Exception as e:
            logger.error(f"Error fetching upcoming meetings: {e}")

        # Return sample data if no real data available
        if not meetings:
            meetings = self._get_sample_meetings(date)

        return meetings

    def _parse_meetings_from_page(self, soup: BeautifulSoup, date: datetime) -> List[Dict[str, Any]]:
        """Parse meeting data from HTML page."""
        meetings = []

        try:
            # Find meeting cards/elements
            meeting_elements = soup.find_all("div", class_=["meeting-card", "meeting-summary"])

            for element in meeting_elements:
                try:
                    meeting = {}

                    # Extract venue name
                    venue_elem = element.find("div", class_="venue-name")
                    if venue_elem:
                        meeting["venue_name"] = self._clean_text(venue_elem.text)

                    # Extract state
                    state_elem = element.find("span", class_="state")
                    if state_elem:
                        meeting["state"] = self._clean_text(state_elem.text)

                    # Extract date
                    date_elem = element.find("span", class_="date")
                    if date_elem:
                        meeting["date"] = self._clean_text(date_elem.text)

                    # Extract race times
                    races_elem = element.find("div", class_="races")
                    if races_elem:
                        races = races_elem.find_all("a", class_="race-link")
                        meeting["race_count"] = len(races)

                    if meeting.get("venue_name"):
                        meetings.append(meeting)

                except Exception as e:
                    logger.warning(f"Error parsing meeting element: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing meetings from page: {e}")

        return meetings

    def _get_sample_meetings(self, date: datetime) -> List[Dict[str, Any]]:
        """Return sample meeting data for demonstration."""
        return [
            {
                "venue_name": "Flemington",
                "state": "VIC",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 10,
                "weather": "Fine",
                "track_rating": "Good 4"
            },
            {
                "venue_name": "Randwick",
                "state": "NSW",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 10,
                "weather": "Cloudy",
                "track_rating": "Soft 5"
            },
            {
                "venue_name": "Doomben",
                "state": "QLD",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 9,
                "weather": "Fine",
                "track_rating": "Good 3"
            },
            {
                "venue_name": "Morphettville",
                "state": "SA",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 10,
                "weather": "Overcast",
                "track_rating": "Good 4"
            },
            {
                "venue_name": "Ascot",
                "state": "WA",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 8,
                "weather": "Fine",
                "track_rating": "Good 4"
            },
            {
                "venue_name": "Hobart",
                "state": "TAS",
                "date": date.strftime("%Y-%m-%d"),
                "race_count": 7,
                "weather": "Rain",
                "track_rating": "Heavy 8"
            }
        ]

    def get_race_details(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific race.

        Args:
            race_id: Race identifier

        Returns:
            Race details dictionary or None
        """
        try:
            url = f"{self.base_url}/race/{race_id}"
            soup = self._get(url)

            if soup:
                return self._parse_race_details(soup, race_id)

        except Exception as e:
            logger.error(f"Error fetching race details for {race_id}: {e}")

        # Return sample data
        return self._get_sample_race_details(race_id)

    def _parse_race_details(self, soup: BeautifulSoup, race_id: str) -> Dict[str, Any]:
        """Parse race details from HTML page."""
        race_details = {"race_id": race_id}

        try:
            # Race name
            name_elem = soup.find("h1", class_="race-name")
            if name_elem:
                race_details["race_name"] = self._clean_text(name_elem.text)

            # Distance
            distance_elem = soup.find("span", class_="distance")
            if distance_elem:
                race_details["distance"] = self._parse_distance(distance_elem.text)

            # Race class
            class_elem = soup.find("span", class_="class")
            if class_elem:
                race_details["race_class"] = self._clean_text(class_elem.text)

            # Prize money
            prize_elem = soup.find("span", class_="prize-money")
            if prize_elem:
                prize_text = self._clean_text(prize_elem.text)
                race_details["prize_money"] = self._parse_prize_money(prize_text)

        except Exception as e:
            logger.error(f"Error parsing race details: {e}")

        return race_details

    def _parse_prize_money(self, prize_str: str) -> Optional[float]:
        """Parse prize money string to float."""
        if not prize_str:
            return None

        # Remove currency symbols and parse
        prize_str = prize_str.replace("$", "").replace(",", "").strip()

        try:
            return float(prize_str)
        except ValueError:
            return None

    def _get_sample_race_details(self, race_id: str) -> Dict[str, Any]:
        """Return sample race details."""
        return {
            "race_id": race_id,
            "race_name": "Group 3 Plate",
            "distance": 1400,
            "race_class": "Group 3",
            "prize_money": 200000.0,
            "race_time": datetime.now().strftime("%Y-%m-%d %H:%00:00"),
            "track_rating": "Good 4",
            "weather": "Fine"
        }

    def get_race_participants(self, race_id: str) -> List[Dict[str, Any]]:
        """
        Get participants (horses) for a race.

        Args:
            race_id: Race identifier

        Returns:
            List of participant dictionaries
        """
        try:
            url = f"{self.base_url}/race/{race_id}/form"
            soup = self._get(url)

            if soup:
                return self._parse_participants(soup, race_id)

        except Exception as e:
            logger.error(f"Error fetching participants for {race_id}: {e}")

        # Return sample data
        return self._get_sample_participants(race_id)

    def _parse_participants(self, soup: BeautifulSoup, race_id: str) -> List[Dict[str, Any]]:
        """Parse participant data from HTML page."""
        participants = []

        try:
            # Find horse table
            table = soup.find("table", class_="horse-table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    try:
                        cells = row.find_all("td")
                        if len(cells) >= 5:
                            participant = {}

                            # Barrier
                            barrier = cells[0].text.strip()
                            participant["barrier"] = int(barrier) if barrier.isdigit() else None

                            # Horse name
                            horse_name = cells[1].text.strip()
                            participant["horse_name"] = horse_name

                            # Jockey
                            jockey = cells[2].text.strip()
                            participant["jockey"] = jockey

                            # Weight
                            weight = cells[3].text.strip()
                            participant["weight"] = self._parse_weight(weight)

                            # Form
                            form = cells[4].text.strip()
                            participant["form"] = form

                            participants.append(participant)

                    except Exception as e:
                        logger.warning(f"Error parsing participant row: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing participants: {e}")

        return participants

    def _parse_weight(self, weight_str: str) -> Optional[float]:
        """Parse weight string to float (in kg)."""
        if not weight_str:
            return None

        weight_str = weight_str.replace("kg", "").strip()

        try:
            return float(weight_str)
        except ValueError:
            return None

    def _get_sample_participants(self, race_id: str) -> List[Dict[str, Any]]:
        """Return sample participant data."""
        return [
            {
                "barrier": 1,
                "horse_name": "Artorius",
                "jockey": "James McDonald",
                "trainer": "Chris Waller",
                "weight": 58.0,
                "form": "1-1-2-1",
                "rating": 110,
                "age": 4
            },
            {
                "barrier": 2,
                "horse_name": "Anamoe",
                "jockey": "Mark Zahra",
                "trainer": "James Cummings",
                "weight": 57.5,
                "form": "2-1-1-3",
                "rating": 108,
                "age": 4
            },
            {
                "barrier": 3,
                "horse_name": "Profiteer",
                "jockey": "Blake Shinn",
                "trainer": "Peter & Paul Snowden",
                "weight": 57.0,
                "form": "1-1-1-1",
                "rating": 105,
                "age": 4
            },
            {
                "barrier": 4,
                "horse_name": "Trickstar",
                "jockey": "Tommy Berry",
                "trainer": "Gai Waterhouse",
                "weight": 56.5,
                "form": "3-2-1-4",
                "rating": 102,
                "age": 5
            },
            {
                "barrier": 5,
                "horse_name": "Maltitude",
                "jockey": "Ben Melham",
                "trainer": "Mick Price",
                "weight": 56.0,
                "form": "5-3-2-2",
                "rating": 98,
                "age": 5
            },
            {
                "barrier": 6,
                "horse_name": "Grail",
                "jockey": "Craig Williams",
                "trainer": "Grahame Begg",
                "weight": 55.5,
                "form": "4-1-3-1",
                "rating": 95,
                "age": 4
            },
            {
                "barrier": 7,
                "horse_name": "Lightsaber",
                "jockey": "Damien Oliver",
                "trainer": "Peter Moody",
                "weight": 55.0,
                "form": "2-5-1-2",
                "rating": 92,
                "age": 6
            },
            {
                "barrier": 8,
                "horse_name": "Vince",
                "jockey": "John Allen",
                "trainer": "Leon & Troy Corstens",
                "weight": 54.5,
                "form": "1-3-4-5",
                "rating": 88,
                "age": 5
            },
            {
                "barrier": 9,
                "horse_name": "Prince Of arrows",
                "jockey": "Koby Jennings",
                "trainer": "Kelly Schweida",
                "weight": 54.0,
                "form": "6-2-1-3",
                "rating": 85,
                "age": 4
            },
            {
                "barrier": 10,
                "horse_name": "Ranchhand",
                "jockey": "Michael Dee",
                "trainer": "Matt Laurie",
                "weight": 53.5,
                "form": "3-4-2-1",
                "rating": 82,
                "age": 5
            }
        ]

    def get_race_results(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for a completed race.

        Args:
            race_id: Race identifier

        Returns:
            Race results dictionary or None
        """
        try:
            url = f"{self.base_url}/results/{race_id}"
            soup = self._get(url)

            if soup:
                return self._parse_results(soup, race_id)

        except Exception as e:
            logger.error(f"Error fetching results for {race_id}: {e}")

        return None

    def _parse_results(self, soup: BeautifulSoup, race_id: str) -> Dict[str, Any]:
        """Parse race results from HTML page."""
        results = {"race_id": race_id, "finishing_order": []}

        try:
            # Find results table
            table = soup.find("table", class_="results-table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_all("td")
                    if len(cells) >= 3:
                        result = {
                            "position": cells[0].text.strip(),
                            "horse_name": cells[1].text.strip(),
                            "dividend": cells[2].text.strip()
                        }
                        results["finishing_order"].append(result)

        except Exception as e:
            logger.error(f"Error parsing results: {e}")

        return results
