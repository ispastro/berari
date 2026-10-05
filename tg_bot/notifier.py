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
        """Format vacancy alert using the exact official Ethiopian Airlines format."""
        title = vacancy.get("title", "TRAINEE")
        location = vacancy.get("location") or "Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)"
        registration_date = vacancy.get("deadline") or "Check portal immediately"
        url = vacancy.get("url", "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies")

        text = (
            f"🚨 <b>ETHIOPIAN AIRLINES TRAINEE ALERT!</b> 🚨\n\n"
            f"<b>Position :</b>  <code>{title}</code>\n"
            f"<b>Location :</b>  {location}\n"
            f"<b>Registration Date :</b>  {registration_date}\n\n"
            f"🔗 <a href=\"{url}\">Tap here to view official posting and apply</a>"
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
        markup = self.build_action_buttons(vacancy.get("url", "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies"))

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
                "title": "TRAINEE - PILOT",
                "location": "Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)",
                "category": "PILOT",
                "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
                "deadline": "From October 10, 2026, to October 25, 2026",
            },
            "CABIN_CREW": {
                "title": "TRAINEE - CABIN CREW",
                "location": "Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)",
                "category": "CABIN_CREW",
                "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
                "deadline": "From October 10, 2026, to October 20, 2026",
            },
            "MAINTENANCE": {
                "title": "TRAINEE - INDUSTRIAL MECHANIC",
                "location": "Ethiopian Airlines Head Quarter, Ethiopian Airport Building (Recruitment & Placement Office)",
                "category": "MAINTENANCE",
                "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
                "deadline": "From September 21, 2026, to September 25, 2026",
            }
        }
        mock = mock_vacancies.get(category.upper(), mock_vacancies["PILOT"])
        text = "🧪 <b>[TEST ALERT - BERARI SYSTEM CHECK]</b>\n\n" + self.format_vacancy_alert(mock)
        markup = self.build_action_buttons(mock["url"])
        return self.send_message(chat_id, text, reply_markup=markup)
