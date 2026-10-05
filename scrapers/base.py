from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests
from config import DEFAULT_HEADERS

@dataclass
class VacancyItem:
    title: str
    source: str
    url: str
    category: str = "PILOT"
    location: Optional[str] = None
    deadline: Optional[str] = None
    summary: Optional[str] = None
    is_pilot: bool = False

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch(self, url: str, timeout: int = 15) -> requests.Response:
        """Fetch URL with timeout and standard browser headers."""
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response

    @abstractmethod
    def scrape(self) -> List[VacancyItem]:
        """Perform scraping and return list of discovered vacancies."""
        pass
