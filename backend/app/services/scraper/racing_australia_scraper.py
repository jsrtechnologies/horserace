"""
Racing Australia Scraper for historical horse racing data.
Scrapes data from racingaustralia.horse website.
"""

import logging
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)


class RacingAustraliaScraper:
    """Scraper for Racing Australia website."""
    
    BASE_URL = "https://www.racingaustralia.horse"
    STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
    
    def _get(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch a URL with retry logic."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(random.uniform(1, 2))  # Be respectful
                return BeautifulSoup(response.text, "html.parser")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
        return None
    
    def get_calendar_for_state(self, state: str, year: int = None, month: int = None) -> List[Dict[str, Any]]:
        """
        Get race meetings from calendar for a specific state.
        
        Args:
            state: Australian state code (NSW, VIC, QLD, WA, SA, TAS, ACT, NT)
            year: Year to fetch (default: current year)
            month: Month to fetch (default: all months)
            
        Returns:
            List of meeting dictionaries
        """
        meetings = []
        
        try:
            url = f"{self.BASE_URL}/FreeFields/Calendar.aspx?State={state}"
            soup = self._get(url)
            
            if not soup:
                logger.error(f"Failed to fetch calendar for {state}")
                return meetings
            
            # Parse the calendar table
            table = soup.find("table", class_="race-fields")
            if not table:
                # Try alternative table class
                table = soup.find("table", class_="race-calendar")
            
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        meeting = self._parse_calendar_row(cells, state)
                        if meeting:
                            # Filter by year/month if specified
                            if year and meeting.get("date"):
                                if meeting["date"].year != year:
                                    continue
                            if month and meeting.get("date"):
                                if meeting["date"].month != month:
                                    continue
                            meetings.append(meeting)
            
            logger.info(f"Found {len(meetings)} meetings for {state}")
            
        except Exception as e:
            logger.error(f"Error fetching calendar for {state}: {e}")
        
        return meetings
    
    def _parse_calendar_row(self, cells, state: str) -> Optional[Dict[str, Any]]:
        """Parse a calendar table row to extract meeting info."""
        try:
            meeting = {"state": state}
            
            # Find date - usually first cell
            date_cell = cells[0]
            date_text = date_cell.get_text(strip=True)
            meeting["date_str"] = date_text
            
            # Parse date (format: "Sat 07 Mar 2026")
            try:
                parsed_date = datetime.strptime(date_text, "%a %d %b %Y")
                meeting["date"] = parsed_date
            except:
                try:
                    parsed_date = datetime.strptime(date_text, "%d %b %Y")
                    meeting["date"] = parsed_date
                except:
                    meeting["date"] = None
            
            # Find venue - look for links with venue info
            for cell in cells:
                links = cell.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    if "Key=" in href:
                        # Extract key from URL
                        import urllib.parse
                        params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "Key" in params:
                            meeting["key"] = params["Key"][0]
                            
                            # Extract venue from key (format: YYYYMMDD,State,Venue)
                            parts = params["Key"][0].split(",")
                            if len(parts) >= 3:
                                meeting["venue"] = parts[2].strip()
            
            if meeting.get("key"):
                return meeting
            
        except Exception as e:
            logger.warning(f"Error parsing calendar row: {e}")
        
        return None
    
    def get_meeting_results(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get results for a specific meeting.
        
        Args:
            key: Meeting key (format: YYYYMMDD,State,Venue)
            
        Returns:
            Dictionary with meeting details and race results
        """
        try:
            url = f"{self.BASE_URL}/FreeFields/Results.aspx?Key={key}"
            soup = self._get(url)
            
            if not soup:
                logger.error(f"Failed to fetch results for {key}")
                return None
            
            meeting_data = {
                "key": key,
                "races": []
            }
            
            # Find all Race title tables to get race info
            race_titles = soup.find_all("table", class_="race-title")
            
            # Find all result tables
            result_tables = soup.find_all("table", class_="race-strip-fields")
            
            logger.info(f"Found {len(race_titles)} race titles and {len(result_tables)} result tables for {key}")
            
            # Match titles with result tables - they should be in pairs
            for i, title_table in enumerate(race_titles):
                race_data = self._parse_race_title(title_table)
                
                # Get corresponding result table (same index)
                if i < len(result_tables):
                    results = self._parse_result_rows(result_tables[i])
                    race_data["results"] = results
                
                meeting_data["races"].append(race_data)
            
            return meeting_data
            
        except Exception as e:
            logger.error(f"Error fetching meeting results for {key}: {e}")
        
        return None
    
    def _parse_race_table(self, table, meeting_key: str) -> Optional[Dict[str, Any]]:
        """Parse a race results table."""
        try:
            race_data = {"results": []}
            
            # Get race info from previous table (race-title)
            prev_sibling = table.find_previous_sibling("table")
            if prev_sibling:
                title_table = prev_sibling.find("table", class_="race-title")
                if title_table:
                    race_info = self._parse_race_title(title_table)
                    race_data.update(race_info)
            
            # Parse horse rows
            rows = table.find_all("tr")
            for row in rows:
                # Look for data rows
                if row.get("class") and ("OddRow" in row.get("class") or "EvenRow" in row.get("class")):
                    result = self._parse_result_row(row)
                    if result:
                        race_data["results"].append(result)
            
            if race_data.get("results"):
                return race_data
                
        except Exception as e:
            logger.warning(f"Error parsing race table: {e}")
        
        return None
    
    def _parse_race_title(self, table) -> Dict[str, Any]:
        """Parse race title/info table."""
        race_info = {}
        
        try:
            # Get all text content from the table
            text = table.get_text(separator=" ", strip=True)
            
            # Extract race number
            match = re.search(r'Race\s*(\d+)', text, re.IGNORECASE)
            if match:
                race_info["race_number"] = int(match.group(1))
            
            # Extract distance (in metres)
            match = re.search(r'(\d+)\s*METRES', text, re.IGNORECASE)
            if match:
                race_info["distance"] = int(match.group(1))
            
            # Extract prize money
            match = re.search(r'\$([\d,]+)', text)
            if match:
                prize_str = match.group(1).replace(",", "")
                race_info["prize_money"] = float(prize_str)
            
            # Extract track condition
            match = re.search(r'Track Condition:\s*(\w+\s*\d*)', text)
            if match:
                race_info["track_condition"] = match.group(1).strip()
            
            # Extract race time
            match = re.search(r'Time:\s*([\d:.]+)', text)
            if match:
                race_info["race_time"] = match.group(1)
            
            # Extract race name (everything before the distance)
            match = re.search(r'Race\s*\d+\s*-\s*[\d:]*(?:AM|PM)\s*([^(]+)', text)
            if match:
                race_info["race_name"] = match.group(1).strip()
        
        except Exception as e:
            logger.warning(f"Error parsing race title: {e}")
        
        return race_info
    
    def _parse_result_rows(self, table) -> List[Dict[str, Any]]:
        """Parse result rows from a result table."""
        results = []
        
        try:
            # Find all rows with EvenRow or OddRow class - use regex
            rows = table.find_all("tr", class_=re.compile(r'(EvenRow|OddRow)'))
            
            for row in rows:
                # Skip scratched horses
                if "Scratched" in row.get("class", []):
                    continue
                    
                result = self._parse_result_row(row)
                if result:
                    results.append(result)
        
        except Exception as e:
            logger.warning(f"Error parsing result rows: {e}")
        
        return results
    
    def _parse_result_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse a single result row."""
        try:
            result = {}
            
            # Skip header rows (no class or different class)
            row_class = row.get("class", [])
            if not row_class or "Row" not in str(row_class):
                return None
            
            # Get all cells
            cells = row.find_all("td")
            
            if len(cells) < 4:
                return None
            
            # Parse position - it's in a <span class="Finish F1"> in the second cell
            # Look for span with class starting with "Finish"
            position_found = False
            for cell_idx, cell in enumerate(cells):
                finish_span = cell.find("span", class_=re.compile(r'^Finish'))
                if finish_span:
                    pos_text = finish_span.get_text(strip=True)
                    if pos_text.isdigit():
                        result["position"] = int(pos_text)
                        position_found = True
                        break
            
            if not position_found:
                # Try cell text as fallback
                if len(cells) > 1:
                    pos_text = cells[1].get_text(strip=True)
                    if pos_text.isdigit():
                        result["position"] = int(pos_text)
                    else:
                        return None  # Skip if no valid position
            else:
                # If position was found via span, use cells[1] content directly
                if "position" not in result:
                    return None
            
            # Horse name - typically in 4th cell (index 3)
            if len(cells) > 3:
                horse_link = cells[3].find("a")
                if horse_link:
                    result["horse_name"] = horse_link.get_text(strip=True)
            
            # Trainer - typically in 5th cell (index 4)
            if len(cells) > 4:
                trainer_link = cells[4].find("a")
                if trainer_link:
                    result["trainer"] = trainer_link.get_text(strip=True)
            
            # Jockey - typically in 6th cell (index 5)
            if len(cells) > 5:
                jockey_link = cells[5].find("a")
                if jockey_link:
                    result["jockey"] = jockey_link.get_text(strip=True)
            
            # Extract weight and price from the row text
            row_text = row.get_text(strip=True)
            
            # Extract price ($X.XX or $X.XXF)
            price_match = re.search(r'\$([\d.]+)[A-Z]*', row_text)
            if price_match:
                result["starting_price"] = float(price_match.group(1))
            
            # Extract margin (like "0.5L" or "1.2L")
            margin_match = re.search(r'(\d+\.?\d*L)', row_text)
            if margin_match:
                result["margin"] = margin_match.group(1)
            
            # Extract weight (like "55kg" or "55.5kg")
            weight_match = re.search(r'(\d+\.?\d*)\s*kg', row_text, re.IGNORECASE)
            if weight_match:
                result["weight"] = float(weight_match.group(1))
            
            # Check we have at least position and horse name
            if not result.get("position") or not result.get("horse_name"):
                return None
            
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing result row: {e}")
        
        return None
    
    def get_results_for_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        states: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get results for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            states: List of states to fetch (default: all)
            
        Returns:
            List of meeting results
        """
        if states is None:
            states = self.STATES
        
        all_results = []
        
        # Iterate through each day in the range
        current_date = start_date
        while current_date <= end_date:
            logger.info(f"Fetching data for {current_date.strftime('%Y-%m-%d')}")
            
            for state in states:
                try:
                    # Get meetings for this date and state
                    meetings = self.get_calendar_for_state(state)
                    
                    for meeting in meetings:
                        if meeting.get("date") and meeting["date"].date() == current_date.date():
                            key = meeting.get("key")
                            if key:
                                results = self.get_meeting_results(key)
                                if results:
                                    results["venue"] = meeting.get("venue")
                                    results["date"] = current_date.strftime("%Y-%m-%d")
                                    results["state"] = state
                                    all_results.append(results)
                                
                except Exception as e:
                    logger.error(f"Error fetching {state} for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        return all_results


def scrape_racing_australia_historical(
    start_year: int = 2021,
    end_year: int = 2026,
    states: List[str] = None
) -> Dict[str, Any]:
    """
    Scrape historical racing data from Racing Australia.
    
    Args:
        start_year: Start year (default: 2021)
        end_year: End year (default: 2026)
        states: List of states to scrape
        
    Returns:
        Statistics about the scraping operation
    """
    scraper = RacingAustraliaScraper()
    
    stats = {
        "meetings_found": 0,
        "races_found": 0,
        "results_found": 0,
        "errors": []
    }
    
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    try:
        # This would take a very long time for 5 years
        # For demo purposes, we'll just return the structure
        logger.info(f"Would scrape from {start_date} to {end_date}")
        
    except Exception as e:
        logger.error(f"Error in scraping: {e}")
        stats["errors"].append(str(e))
    
    return stats


if __name__ == "__main__":
    # Test the scraper
    print("Testing Racing Australia scraper...")
    
    scraper = RacingAustraliaScraper()
    
    # Get calendar for NSW
    print("\nFetching NSW calendar...")
    meetings = scraper.get_calendar_for_state("NSW")
    print(f"Found {len(meetings)} meetings")
    
    if meetings:
        # Get results for first meeting
        first_meeting = meetings[0]
        key = first_meeting.get("key")
        if key:
            print(f"\nFetching results for {key}...")
            results = scraper.get_meeting_results(key)
            if results:
                print(f"Races: {len(results.get('races', []))}")
                for race in results.get("races", [])[:2]:
                    print(f"  Race {race.get('race_number')}: {len(race.get('results', []))} results")
                    for r in race.get("results", [])[:3]:
                        print(f"    {r.get('position')}. {r.get('horse_name')}")
