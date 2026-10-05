import logging
from typing import Dict, Any, List, Optional
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

CATEGORY_HEADERS = {
    "PILOT": ("✈️", "PILOT & CADET VACANCY"),
    "CABIN_CREW": ("🧑‍✈️", "CABIN CREW / FLIGHT ATTENDANT VACANCY"),
    "MAINTENANCE": ("🔧", "AIRCRAFT MAINTENANCE & TECH VACANCY"),
}

class TelegramNotifier:
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.bot_token.strip() and not self.bot_token.startswith("your_"))

    def send_message(self, chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """Send message via Telegram Bot HTTP API."""
        if not self.is_configured:
            logger.warning("Telegram Bot Token is not configured. Alert suppressed.")
            return False

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Telegram notification sent successfully to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram message to {chat_id}: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error dispatching Telegram message to {chat_id}: {e}")
            return False

    def format_vacancy_alert(self, vacancy: Dict[str, Any]) -> str:
        """Format rich HTML card for aviation vacancy alert."""
        title = vacancy.get("title", "Aviation Position")
        source = vacancy.get("source", "Ethiopian Airlines")
        category = vacancy.get("category", "PILOT").upper()
        url = vacancy.get("url", "")
        deadline = vacancy.get("deadline") or "Not specified / Check portal immediately"
        summary = vacancy.get("summary") or "New vacancy detected on the official Ethiopian Airlines recruitment portal."

        emoji, cat_title = CATEGORY_HEADERS.get(category, ("✈️", "AVIATION VACANCY"))

        if len(summary) > 280:
            summary = summary[:277] + "..."

        text = (
            f"🚨 <b>ETHIOPIAN AIRLINES {cat_title}!</b> 🚨\n\n"
            f"{emoji} <b>Position:</b> <code>{title}</code>\n"
            f"🏷️ <b>Category:</b> {category.replace('_', ' ').title()}\n"
            f"🏛️ <b>Portal:</b> {source}\n"
            f"⏰ <b>Deadline:</b> {deadline}\n\n"
            f"📋 <b>Summary / Requirements:</b>\n"
            f"<i>{summary}</i>\n\n"
            f"🔗 <a href=\"{url}\">Tap below to view full requirements and apply</a>"
        )
        return text

    def build_action_buttons(self, url: str) -> Dict[str, Any]:
        """Create inline keyboard with direct apply button."""
        return {
            "inline_keyboard": [
                [
                    {"text": "✈️ Open Application Page", "url": url}
                ]
            ]
        }

    def broadcast_vacancy(self, vacancy: Dict[str, Any], chat_ids: List[str]) -> int:
        """Send vacancy alert to target subscribers."""
        if not chat_ids and TELEGRAM_CHAT_ID:
            chat_ids = [TELEGRAM_CHAT_ID]

        message = self.format_vacancy_alert(vacancy)
        markup = self.build_action_buttons(vacancy.get("url", "https://corporate.ethiopianairlines.com"))

        sent_count = 0
        for cid in set(chat_ids):
            if cid:
                if self.send_message(cid, message, reply_markup=markup):
                    sent_count += 1

        return sent_count

    def send_test_alert(self, chat_id: str, category: str = "PILOT") -> bool:
        """Send a test vacancy alert card to verify notifications."""
        mock_vacancies = {
            "PILOT": {
                "title": "Trainee Pilot - Ethiopian Aviation University (TEST ALERT)",
                "source": "Ethiopian Airlines Group / EAU",
                "category": "PILOT",
                "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
                "deadline": "31 October 2026",
                "summary": "Educational requirement: BSc in Engineering or Science with CGPA >= 2.75. Age: 18 - 25 years. Height: minimum 1.62m. English proficiency required.",
            },
            "CABIN_CREW": {
                "title": "Trainee Cabin Crew (TEST ALERT)",
                "source": "Ethiopian Airlines Careers",
                "category": "CABIN_CREW",
                "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
                "deadline": "15 November 2026",
                "summary": "Educational requirement: Minimum 10+2 / Grade 12 completion or Diploma. Age: 18 - 26 years. Height: minimum 1.59m. Good communication and interpersonal skills.",
            },
            "MAINTENANCE": {
                "title": "Aircraft Maintenance Technician Trainee (TEST ALERT)",
                "source": "Ethiopian Aviation University",
                "category": "MAINTENANCE",
                "url": "https://eau.edu.et/programs",
                "deadline": "25 November 2026",
                "summary": "Educational requirement: Diploma or BSc in Electrical, Mechanical, Aeronautical or Automotive Engineering. Age: up to 27 years.",
            }
        }
        mock = mock_vacancies.get(category.upper(), mock_vacancies["PILOT"])
        text = "🧪 <b>[TEST ALERT - BERARI SYSTEM CHECK]</b>\n\n" + self.format_vacancy_alert(mock)
        markup = self.build_action_buttons(mock["url"])
        return self.send_message(chat_id, text, reply_markup=markup)
