import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List

from config import ET_ETHIOJOBS_URL
from scrapers.base import BaseScraper, VacancyItem
from matcher.pilot_filter import PilotFilter

logger = logging.getLogger(__name__)

class EthiojobsScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="Ethiojobs (Ethiopian Airlines Official)")
        self.url = ET_ETHIOJOBS_URL
        self.filter = PilotFilter()

    def scrape(self) -> List[VacancyItem]:
        logger.info(f"[{self.name}] Fetching Ethiopian Airlines group jobs from {self.url}...")
        results: List[VacancyItem] = []

        try:
            resp = self.fetch(self.url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Ethiojobs job listings
            job_blocks = soup.select(".single_item, .job-listing, .listing-item, .jobs-list, [class*='job'], table tr")
            if not job_blocks:
                job_blocks = soup.find_all(["div", "article", "li"], class_=True)

            for block in job_blocks:
                block_text = block.get_text(" ", strip=True)
                if not block_text or len(block_text) < 10:
                    continue

                # Look for anchor tag inside
                link_tag = block.find("a", href=True)
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                if not title:
                    title_elem = block.find(["h2", "h3", "h4", "h5", "strong"])
                    if title_elem:
                        title = title_elem.get_text(strip=True)

                if title and self.filter.is_pilot_trainee_vacancy(title, block_text):
                    link = urljoin(self.url, link_tag["href"])
                    meta = self.filter.extract_metadata(block_text)

                    if not any(r.title.lower() == title.lower() and r.url == link for r in results):
                        results.append(
                            VacancyItem(
                                title=title,
                                source=self.name,
                                url=link,
                                deadline=meta.get("deadline"),
                                summary=block_text[:400],
                                is_pilot=True
                            )
                        )

            # Global anchor search on Ethiojobs page
            for a in soup.find_all("a", href=True):
                a_text = a.get_text(strip=True)
                if a_text and self.filter.is_pilot_trainee_vacancy(a_text):
                    link = urljoin(self.url, a["href"])
                    if not any(r.url == link for r in results):
                        results.append(
                            VacancyItem(
                                title=a_text,
                                source=self.name,
                                url=link,
                                deadline=None,
                                summary=f"Found on Ethiojobs Ethiopian Airlines portal ({link})",
                                is_pilot=True
                            )
                        )

            logger.info(f"[{self.name}] Finished scan. Found {len(results)} pilot trainee vacancies.")
        except Exception as e:
            logger.error(f"[{self.name}] Error scraping Ethiojobs: {e}", exc_info=True)
            raise

        return results
