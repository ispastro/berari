import logging
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List

from config import ET_CAREERS_URL
from scrapers.base import BaseScraper, VacancyItem
from matcher.pilot_filter import PilotFilter

logger = logging.getLogger(__name__)

class EthiopianCareersScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="Ethiopian Airlines Official Careers")
        self.url = ET_CAREERS_URL
        self.filter = PilotFilter()

    def scrape(self) -> List[VacancyItem]:
        logger.info(f"[{self.name}] Fetching official vacancy tables from {self.url}...")
        results: List[VacancyItem] = []

        try:
            resp = self.fetch(self.url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Ethiopian Airlines posts each official vacancy inside a distinct <table>
            tables = soup.find_all("table")
            for table in tables:
                table_text = table.get_text(" ", strip=True)
                if not table_text or len(table_text) < 15:
                    continue

                # Look for explicit "Position Title : <job title>" pattern
                pos_match = re.search(r'Position(?:\s*Title)?\s*:\s*([^.\n|]{3,80})', table_text, re.I)
                if not pos_match:
                    continue

                raw_title = pos_match.group(1).strip()
                # Clean up any trailing labels like 'Qualification Requirement' or 'Closing Date'
                clean_title = re.split(r'qualification|registration|closing|deadline', raw_title, flags=re.I)[0].strip()

                if not clean_title or len(clean_title) < 3:
                    continue

                # Check if this vacancy matches Pilot, Cabin Crew, or Maintenance
                category, meta = self.filter.classify_vacancy(clean_title, table_text)
                if category:
                    link_tag = table.find("a", href=True)
                    link = urljoin(self.url, link_tag["href"]) if link_tag else self.url

                    if not any(r.title.lower() == clean_title.lower() for r in results):
                        results.append(
                            VacancyItem(
                                title=clean_title,
                                source=self.name,
                                url=link,
                                category=category,
                                deadline=meta.get("deadline"),
                                summary=table_text[:400],
                                is_pilot=(category == "PILOT")
                            )
                        )

            logger.info(f"[{self.name}] Finished scan. Found {len(results)} active aviation vacancies.")
        except Exception as e:
            logger.error(f"[{self.name}] Error scraping vacancies: {e}", exc_info=True)
            raise

        return results
