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

                # 1. Position Title (e.g. 'TRAINEE - INDUSTRIAL ELECTRICIAN', 'TRAINEE - PILOT')
                pos_match = re.search(
                    r'Position(?:\s*Title)?\s*:\s*(.+?)(?=\s*(?:Location|Registration\s*Date|Closing\s*Date|Deadline|Qualification|$))',
                    table_text,
                    re.I | re.DOTALL
                )
                if not pos_match:
                    continue

                raw_title = pos_match.group(1).strip()
                clean_title = re.sub(r'[\r\n\t]+', ' ', raw_title).strip()
                # Clean up any trailing labels like 'Qualification Requirement'
                clean_title = re.split(r'qualification|registration|closing|deadline', clean_title, flags=re.I)[0].strip()

                if not clean_title or len(clean_title) < 3:
                    continue

                # 2. Location (e.g. 'Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)')
                loc_match = re.search(
                    r'Location\s*:\s*(.+?)(?=\s*(?:Registration\s*Date|Closing\s*Date|Deadline|Qualification|Position|$))',
                    table_text,
                    re.I | re.DOTALL
                )
                clean_location = re.sub(r'[\r\n\t]+', ' ', loc_match.group(1)).strip() if loc_match else "Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)"

                # 3. Registration Date (e.g. 'From September 21, 2026, to September 25, 2026.')
                reg_match = re.search(
                    r'(?:Registration\s*Date|Closing\s*Date|Deadline)\s*:\s*(.+?)(?=\s*(?:Qualification|Position|Location|Experience|Language|$))',
                    table_text,
                    re.I | re.DOTALL
                )

                # Check if this vacancy matches Pilot, Cabin Crew, or Maintenance Trainee
                category, meta = self.filter.classify_vacancy(clean_title, table_text)
                if category:
                    clean_deadline = re.sub(r'[\r\n\t]+', ' ', reg_match.group(1)).strip() if reg_match else meta.get("deadline")
                    link_tag = table.find("a", href=True)
                    link = urljoin(self.url, link_tag["href"]) if link_tag else self.url

                    if not any(r.title.lower() == clean_title.lower() for r in results):
                        results.append(
                            VacancyItem(
                                title=clean_title,
                                source=self.name,
                                url=link,
                                category=category,
                                location=clean_location,
                                deadline=clean_deadline,
                                summary=table_text[:400],
                                is_pilot=(category == "PILOT")
                            )
                        )

            logger.info(f"[{self.name}] Finished scan. Found {len(results)} active aviation vacancies.")
        except Exception as e:
            logger.error(f"[{self.name}] Error scraping vacancies: {e}", exc_info=True)
            raise

        return results
