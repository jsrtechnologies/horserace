"""
Ladbrokes scraper for Australian horse racing data.
Uses the official Ladbrokes Affiliate API.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class LadbrokesScraper:
    """Scraper for Ladbrokes.com.au using their Affiliate API"""
    
    def __init__(self):
        # Use the correct API endpoint
        self.base_url = "https://api-affiliates.ladbrokes.com.au/affiliates/v1"
        self.api_base = "https://api-affiliates.ladbrokes.com.au/affiliates/v1"
        
        # Required headers for API authentication
        self.headers = {
            "From": "ausrace-predictor@example.com",
            "X-Partner": "AusRace Predictor",
            "Accept": "application/json"
        }
    
    def get_upcoming_meetings(self, date: Optional[datetime] = None, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming race meetings from Ladbrokes.
        
        Args:
            date: Start date (defaults to today)
            days: Number of days to look ahead
            
        Returns:
            List of meeting dictionaries with race information
        """
        if date is None:
            date = datetime.now()
        
        meetings = []
        
        try:
            # Format dates for API
            date_from = date.strftime("%Y-%m-%d")
            date_to = (date + timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Get all meetings for the date range (Thoroughbreds only)
            url = f"{self.api_base}/racing/meetings"
            params = {
                "enc": "json",
                "date_from": date_from,
                "date_to": date_to,
                "category": "T",  # Thoroughbred
                "country": "AUS",  # Australia
                "limit": 100
            }
            
            logger.info(f"Fetching Ladbrokes meetings from {date_from} to {date_to}")
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                meetings = self._parse_meetings_response(data)
                logger.info(f"Found {len(meetings)} meetings from Ladbrokes API")
            elif response.status_code == 429:
                logger.warning("Rate limited by Ladbrokes API")
            else:
                logger.error(f"Ladbrokes API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Ladbrokes API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in get_upcoming_meetings: {e}")
        
        return meetings
    
    def _parse_meetings_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse the API response into our meeting format."""
        meetings = []
        
        try:
            # The API returns data in 'data.meetings' structure
            # Handle both response formats
            if "data" in data and "meetings" in data["data"]:
                meetings_data = data["data"]["meetings"]
            elif "meetings" in data:
                meetings_data = data["meetings"]
            else:
                logger.warning(f"Unexpected response structure: {list(data.keys())}")
                return []
            
            for meeting_data in meetings_data:
                try:
                    meeting = {
                        "external_id": meeting_data.get("meeting"),
                        "venue_name": meeting_data.get("name"),
                        "date": meeting_data.get("date"),
                        "category": meeting_data.get("category"),
                        "category_name": meeting_data.get("category_name"),
                        "country": meeting_data.get("country"),
                        "state": meeting_data.get("state"),
                        "track_condition": meeting_data.get("track_condition"),
                        "weather": meeting_data.get("weather"),
                        "races": []
                    }
                    
                    # Parse races
                    races_data = meeting_data.get("races", [])
                    for race_data in races_data:
                        race = {
                            "external_id": race_data.get("id"),
                            "race_number": race_data.get("race_number"),
                            "name": race_data.get("name"),
                            "start_time": race_data.get("start_time"),
                            "track_condition": race_data.get("track_condition"),
                            "distance": race_data.get("distance"),
                            "weather": race_data.get("weather"),
                            "country": race_data.get("country"),
                            "state": race_data.get("state"),
                            "status": race_data.get("status")
                        }
                        meeting["races"].append(race)
                    
                    meetings.append(meeting)
                    
                except Exception as e:
                    logger.warning(f"Error parsing meeting: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing meetings response: {e}")
        
        return meetings
    
    def get_meeting_details(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific meeting.
        
        Args:
            meeting_id: The Ladbrokes meeting UUID
            
        Returns:
            Meeting details with all races and runners
        """
        try:
            url = f"{self.api_base}/racing/meetings/{meeting_id}"
            params = {"enc": "json"}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_meeting_details(data, meeting_id)
            else:
                logger.error(f"Error fetching meeting {meeting_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in get_meeting_details: {e}")
        
        return None
    
    def _parse_meeting_details(self, data: Dict, meeting_id: str) -> Dict[str, Any]:
        """Parse meeting details including runners."""
        # The response structure may vary, handle both formats
        if "meetings" in data and len(data.get("meetings", [])) > 0:
            meeting_data = data["meetings"][0]
        else:
            meeting_data = data
        
        meeting = {
            "external_id": meeting_id,
            "venue_name": meeting_data.get("name"),
            "date": meeting_data.get("date"),
            "state": meeting_data.get("state"),
            "category": meeting_data.get("category"),
            "races": []
        }
        
        # Parse races with runners
        races_data = meeting_data.get("races", [])
        for race_data in races_data:
            race = {
                "external_id": race_data.get("id"),
                "race_number": race_data.get("race_number"),
                "name": race_data.get("name"),
                "start_time": race_data.get("start_time"),
                "track_condition": race_data.get("track_condition"),
                "distance": race_data.get("distance"),
                "weather": race_data.get("weather"),
                "runners": []
            }
            
            # Runners might be in different locations depending on API version
            # Try to get runners from the race
            race_id = race_data.get("id")
            if race_id:
                race["runners"] = self._get_race_runners(race_id)
            
            meeting["races"].append(race)
        
        return meeting
    
    def _get_race_runners(self, race_id: str) -> List[Dict[str, Any]]:
        """Get runners for a specific race."""
        try:
            url = f"{self.api_base}/racing/events/{race_id}"
            params = {"enc": "json"}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_runners(data)
            else:
                logger.warning(f"Could not fetch runners for race {race_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching race runners: {e}")
        
        return []
    
    def _parse_runners(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse runners from race event response."""
        runners = []
        
        try:
            # Try to find runners in the response
            # The structure varies, so we check multiple possible locations
            event_data = data.get("event", data)
            
            # Look for runners in 'runners' or 'entrants' field
            runners_data = event_data.get("runners", []) or event_data.get("entrants", [])
            
            for runner_data in runners_data:
                try:
                    runner = {
                        "name": runner_data.get("name"),
                        "is_scratched": runner_data.get("is_scratched", False),
                        "barrier": runner_data.get("barrier"),
                        "runner_number": runner_data.get("runner_number"),
                        "jockey": runner_data.get("jockey"),
                        "trainer": runner_data.get("trainer_name"),
                        "weight": runner_data.get("weight", {}).get("allocated") if isinstance(runner_data.get("weight"), dict) else runner_data.get("weight"),
                        "odds": runner_data.get("odds", {}),
                        "favourite": runner_data.get("favourite", False)
                    }
                    runners.append(runner)
                except Exception as e:
                    logger.warning(f"Error parsing runner: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing runners: {e}")
        
        return runners
    
    def get_race_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed race event information including all runners and odds.
        
        Args:
            event_id: The Ladbrokes race/event UUID
            
        Returns:
            Race details with runners
        """
        try:
            url = f"{self.api_base}/racing/events/{event_id}"
            params = {"enc": "json"}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_race_event(data)
            else:
                logger.error(f"Error fetching race event {event_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in get_race_event: {e}")
        
        return None
    
    def _parse_race_event(self, data: Dict) -> Dict[str, Any]:
        """Parse race event response."""
        # Handle the response structure - data is in data.data.race
        if "data" in data:
            race_data = data["data"].get("race", {})
            runners_data = data["data"].get("runners", [])
        else:
            race_data = data
            runners_data = []
        
        race = {
            "external_id": race_data.get("event_id"),
            "meeting_name": race_data.get("meeting_name"),
            "meeting_id": race_data.get("meeting_id"),
            "status": race_data.get("status"),
            "description": race_data.get("description"),
            "advertised_start": race_data.get("advertised_start"),
            "actual_start": race_data.get("actual_start"),
            "race_number": race_data.get("race_number"),
            "type": race_data.get("type"),
            "country": race_data.get("country"),
            "state": race_data.get("state"),
            "distance": race_data.get("distance"),
            "weather": race_data.get("weather"),
            "track_condition": race_data.get("track_condition"),
            "runners": []
        }
        
        # Parse runners from the separate runners array
        for runner_data in runners_data:
            runner = {
                "name": runner_data.get("name"),
                "is_scratched": runner_data.get("is_scratched", False),
                "barrier": runner_data.get("barrier"),
                "runner_number": runner_data.get("runner_number"),
                "jockey": runner_data.get("jockey"),
                "trainer": runner_data.get("trainer_name"),
                "weight": runner_data.get("weight", {}).get("allocated") if isinstance(runner_data.get("weight"), dict) else None,
                "fixed_win": runner_data.get("odds", {}).get("fixed_win"),
                "fixed_place": runner_data.get("odds", {}).get("fixed_place"),
                "favourite": runner_data.get("favourite", False),
                "age": runner_data.get("age"),
                "sex": runner_data.get("sex"),
                "colour": runner_data.get("colour"),
                "gear": runner_data.get("gear")
            }
            race["runners"].append(runner)
        
        # Parse dividends/results if available
        if "dividends" in data.get("data", {}):
            race["dividends"] = data["data"]["dividends"]
        
        return race
    
    def get_today_meetings(self) -> List[Dict[str, Any]]:
        """Get today's meetings."""
        return self.get_upcoming_meetings(days=1)
    
    def get_week_meetings(self) -> List[Dict[str, Any]]:
        """Get this week's meetings."""
        return self.get_upcoming_meetings(days=7)
    
    # Required abstract methods for compatibility
    def get_race_details(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific race.
        
        Args:
            race_id: Race identifier (Ladbrokes race UUID)
            
        Returns:
            Race details dictionary or None
        """
        return self.get_race_event(race_id)
    
    def get_race_participants(self, race_id: str) -> List[Dict[str, Any]]:
        """
        Get participants (horses) for a race.
        
        Args:
            race_id: Race identifier
            
        Returns:
            List of participant dictionaries
        """
        race_details = self.get_race_event(race_id)
        if race_details:
            return race_details.get("runners", [])
        return []


def fetch_ladbrokes_data(days: int = 7) -> Dict[str, Any]:
    """
    Convenience function to fetch Ladbrokes data.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        Dictionary with meetings and statistics
    """
    scraper = LadbrokesScraper()
    
    result = {
        "fetched_at": datetime.now().isoformat(),
        "days": days,
        "meetings": [],
        "total_races": 0,
        "total_runners": 0,
        "errors": []
    }
    
    try:
        meetings = scraper.get_upcoming_meetings(days=days)
        
        for meeting in meetings:
            result["meetings"].append(meeting)
            result["total_races"] += len(meeting.get("races", []))
            
            # Fetch runners for each race
            for race in meeting.get("races", []):
                race_id = race.get("external_id")
                if race_id:
                    race_details = scraper.get_race_event(race_id)
                    if race_details:
                        race["runners"] = race_details.get("runners", [])
                        result["total_runners"] += len(race["runners"])
        
        result["status"] = "success"
        
    except Exception as e:
        logger.error(f"Error fetching Ladbrokes data: {e}")
        result["errors"].append(str(e))
        result["status"] = "error"
    
    return result
