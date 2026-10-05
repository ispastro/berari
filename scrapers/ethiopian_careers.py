import logging
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
        logger.info(f"[{self.name}] Fetching vacancies from {self.url}...")
        results: List[VacancyItem] = []

        try:
            resp = self.fetch(self.url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. Check table rows
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) >= 2:
                    text_parts = [c.get_text(" ", strip=True) for c in cols]
                    row_text = " | ".join(text_parts)
                    
                    link_tag = row.find("a", href=True)
                    link = urljoin(self.url, link_tag["href"]) if link_tag else self.url
                    
                    title = text_parts[0] if len(text_parts[0]) > 3 else (text_parts[1] if len(text_parts) > 1 else "")
                    
                    category, meta = self.filter.classify_vacancy(title, row_text)
                    if category:
                        results.append(
                            VacancyItem(
                                title=title,
                                source=self.name,
                                url=link,
                                category=category,
                                deadline=meta.get("deadline"),
                                summary=row_text[:400],
                                is_pilot=(category == "PILOT")
                            )
                        )

            # 2. Check cards, job list items, accordions
            job_cards = soup.select(".vacancy, .job-item, .card, .accordion-item, .career-item, li, article")
            for card in job_cards:
                card_text = card.get_text(" ", strip=True)
                title_tag = card.find(["h2", "h3", "h4", "h5", "strong", "a"])
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                if not title or len(title) < 4:
                    continue

                category, meta = self.filter.classify_vacancy(title, card_text)
                if category:
                    link_tag = card.find("a", href=True)
                    link = urljoin(self.url, link_tag["href"]) if link_tag else self.url

                    if not any(r.title.lower() == title.lower() and r.url == link for r in results):
                        results.append(
                            VacancyItem(
                                title=title,
                                source=self.name,
                                url=link,
                                category=category,
                                deadline=meta.get("deadline"),
                                summary=card_text[:400],
                                is_pilot=(category == "PILOT")
                            )
                        )

            # 3. Direct anchor scan
            for a in soup.find_all("a", href=True):
                anchor_text = a.get_text(strip=True)
                if anchor_text:
                    category, _ = self.filter.classify_vacancy(anchor_text)
                    if category:
                        link = urljoin(self.url, a["href"])
                        if not any(r.url == link for r in results):
                            results.append(
                                VacancyItem(
                                    title=anchor_text,
                                    source=self.name,
                                    url=link,
                                    category=category,
                                    deadline=None,
                                    summary=f"Direct link found on {self.url}",
                                    is_pilot=(category == "PILOT")
                                )
                            )

            logger.info(f"[{self.name}] Finished scan. Found {len(results)} aviation vacancies.")
        except Exception as e:
            logger.error(f"[{self.name}] Error scraping vacancies: {e}", exc_info=True)
            raise

        return results
