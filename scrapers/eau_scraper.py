import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List

from config import ET_UNIVERSITY_URL
from scrapers.base import BaseScraper, VacancyItem
from matcher.pilot_filter import PilotFilter

logger = logging.getLogger(__name__)

class EAUScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="Ethiopian Aviation University")
        self.base_url = ET_UNIVERSITY_URL
        self.endpoints = [
            self.base_url,
            urljoin(self.base_url, "/programs"),
            urljoin(self.base_url, "/admission"),
        ]
        self.filter = PilotFilter()

    def scrape(self) -> List[VacancyItem]:
        logger.info(f"[{self.name}] Checking Ethiopian Aviation University portals...")
        results: List[VacancyItem] = []

        for url in self.endpoints:
            try:
                resp = self.fetch(url)
                soup = BeautifulSoup(resp.text, "html.parser")

                elements = soup.select(".card, .program-item, .post, .news-item, li, article, .item, tr")
                for elem in elements:
                    elem_text = elem.get_text(" ", strip=True)
                    if not elem_text:
                        continue

                    title_tag = elem.find(["h1", "h2", "h3", "h4", "h5", "a", "strong"])
                    title = title_tag.get_text(strip=True) if title_tag else elem_text[:80]

                    category, meta = self.filter.classify_vacancy(title, elem_text)
                    if category:
                        link_tag = elem.find("a", href=True)
                        link = urljoin(url, link_tag["href"]) if link_tag else url

                        if not any(r.title.lower() == title.lower() and r.url == link for r in results):
                            results.append(
                                VacancyItem(
                                    title=title,
                                    source=self.name,
                                    url=link,
                                    category=category,
                                    deadline=meta.get("deadline"),
                                    summary=elem_text[:400],
                                    is_pilot=(category == "PILOT")
                                )
                            )

                # Direct anchor scan
                for a in soup.find_all("a", href=True):
                    a_text = a.get_text(strip=True)
                    if a_text:
                        category, _ = self.filter.classify_vacancy(a_text)
                        if category:
                            link = urljoin(url, a["href"])
                            if not any(r.url == link for r in results):
                                results.append(
                                    VacancyItem(
                                        title=a_text,
                                        source=self.name,
                                        url=link,
                                        category=category,
                                        deadline=None,
                                        summary=f"Found on Ethiopian Aviation University portal ({url})",
                                        is_pilot=(category == "PILOT")
                                    )
                                )

            except Exception as e:
                logger.warning(f"[{self.name}] Could not scrape endpoint {url}: {e}")
                continue

        logger.info(f"[{self.name}] Finished scan. Found {len(results)} items.")
        return results
