import logging
from typing import Dict, Any, List, Optional
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

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
        """Format rich HTML card for pilot trainee alert."""
        title = vacancy.get("title", "Pilot Trainee Position")
        source = vacancy.get("source", "Ethiopian Airlines")
        url = vacancy.get("url", "")
        deadline = vacancy.get("deadline") or "Not specified / Check official portal"
        summary = vacancy.get("summary") or "New vacancy detected on the official Ethiopian Airlines recruitment channel."

        # Truncate summary if too long for card display
        if len(summary) > 280:
            summary = summary[:277] + "..."

        text = (
            "🚨 <b>ETHIOPIAN AIRLINES PILOT TRAINEE ALERT!</b> 🚨\n\n"
            f"✈️ <b>Position:</b> <code>{title}</code>\n"
            f"🏛️ <b>Portal:</b> {source}\n"
            f"⏰ <b>Deadline:</b> {deadline}\n\n"
            f"📋 <b>Summary / Requirements:</b>\n"
            f"<i>{summary}</i>\n\n"
            f"🔗 <a href=\"{url}\">Click here to view official posting and apply</a>"
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
        """Send vacancy alert to all registered subscribers."""
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

    def send_test_alert(self, chat_id: str) -> bool:
        """Send a test pilot vacancy alert to verify notifications."""
        mock_vacancy = {
            "title": "Trainee Pilot - Ethiopian Aviation University (TEST ALERT)",
            "source": "Ethiopian Airlines Group / EAU",
            "url": "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies",
            "deadline": "31 October 2026",
            "summary": "Educational requirement: BSc in Engineering or Natural Science with CGPA >= 2.75. Age: 18 - 25 years. Height: minimum 1.62m. English proficiency required.",
        }
        text = self.format_vacancy_alert(mock_vacancy)
        text = "🧪 <b>[TEST ALERT - SYSTEM CHECK]</b>\n" + text
        markup = self.build_action_buttons(mock_vacancy["url"])
        return self.send_message(chat_id, text, reply_markup=markup)
