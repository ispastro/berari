import logging
from typing import Callable, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import Database
from tg_bot.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

TRACK_NAMES = {
    "PILOT": "✈️ Pilot & Cadet Trainee",
    "CABIN_CREW": "🧑‍✈️ Cabin Crew / Flight Attendant",
    "MAINTENANCE": "🔧 Aircraft Maintenance & Tech",
    "ALL": "🌐 All Aviation Vacancies",
}

def get_track_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for track selection."""
    keyboard = [
        [
            InlineKeyboardButton("✈️ Pilot & Cadet", callback_data="set_track:PILOT"),
            InlineKeyboardButton("🧑‍✈️ Cabin Crew", callback_data="set_track:CABIN_CREW"),
        ],
        [
            InlineKeyboardButton("🔧 Maintenance / Tech", callback_data="set_track:MAINTENANCE"),
            InlineKeyboardButton("🌐 All Vacancies", callback_data="set_track:ALL"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

class TelegramBotHandlers:
    def __init__(self, db: Database, notifier: TelegramNotifier, manual_check_callback: Callable[[], Any]):
        self.db = db
        self.notifier = notifier
        self.manual_check_callback = manual_check_callback

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - registers user and offers track selection."""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)

        self.db.add_subscriber(
            chat_id=chat_id,
            username=user.username,
            first_name=user.first_name,
            track="ALL",
        )

        current_track = self.db.get_subscriber_track(chat_id)

        welcome_text = (
            f"👋 Selam <b>{user.first_name or 'there'}</b>!\n\n"
            "🇪🇹 Welcome to <b>Berari (በራሪ) — Ethiopian Airlines Career Monitor</b>!\n\n"
            "🔔 You are subscribed to instant alerts for Ethiopian Airlines & Ethiopian Aviation University.\n\n"
            f"🎯 <b>Current Track:</b> {TRACK_NAMES.get(current_track, current_track)}\n\n"
            "👇 <b>Select the career track you want to receive alerts for:</b>"
        )
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=get_track_keyboard())

    async def track_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /track command - let user change their preferred alerts."""
        chat_id = str(update.effective_chat.id)
        current = self.db.get_subscriber_track(chat_id)
        text = (
            "🎯 <b>Select Your Career Track:</b>\n\n"
            f"Currently receiving alerts for: <b>{TRACK_NAMES.get(current, current)}</b>\n\n"
            "Tap an option below to update your preference:"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_track_keyboard())

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks for track selection."""
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("set_track:"):
            chosen_track = data.split(":", 1)[1]
            chat_id = str(query.message.chat_id)

            self.db.set_subscriber_track(chat_id, chosen_track)
            track_label = TRACK_NAMES.get(chosen_track, chosen_track)

            confirm_text = (
                f"✅ <b>Preferences Updated!</b>\n\n"
                f"You will now receive alerts for: <b>{track_label}</b>.\n\n"
                "Use /track anytime to switch categories or /check to scan right now."
            )
            await query.edit_message_text(confirm_text, parse_mode="HTML")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "✈️ <b>Berari (በራሪ) Commands Menu</b>\n\n"
            "• /track - Choose your role (Pilot, Cabin Crew, Maintenance, or All)\n"
            "• /check - Trigger a real-time scan across all Ethiopian portals right now\n"
            "• /status - Check bot status, last scan timestamp, and vacancy counts\n"
            "• /latest - Display recently discovered aviation vacancies\n"
            "• /test - Send a test alert card to your phone\n"
            "• /stop - Unsubscribe from alerts"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        stats = self.db.get_stats()
        chat_id = str(update.effective_chat.id)
        user_track = self.db.get_subscriber_track(chat_id)

        text = (
            "📊 <b>Berari (በራሪ) Monitor Status</b>\n\n"
            f"🟢 <b>Status:</b> Active & Monitoring 24/7\n"
            f"🎯 <b>Your Alert Track:</b> {TRACK_NAMES.get(user_track, user_track)}\n"
            f"👥 <b>Total Subscribers:</b> {stats['subscribers_count']}\n\n"
            "💼 <b>Active Openings Breakdown:</b>\n"
            f"  ✈️ Pilot Trainee: {stats.get('pilot_vacancies', 0)}\n"
            f"  🧑‍✈️ Cabin Crew Trainee: {stats.get('cabin_vacancies', 0)}\n"
            f"  🔧 Maintenance Trainee: {stats.get('maintenance_vacancies', 0)}\n"
            f"  📦 Total Vacancies: {stats['total_vacancies']}\n\n"
            f"⏱️ <b>Last Scan:</b> <code>{stats['last_scrape_time']}</code>\n"
            f"🚦 <b>Last Scan Result:</b> {stats['last_scrape_status']}"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command - on-demand scan."""
        await update.message.reply_text("🔄 Initiating live scan of Ethiopian Airlines Corporate Careers... Please wait a moment.")
        try:
            new_items = self.manual_check_callback()
            if new_items:
                await update.message.reply_text(f"✅ Scan complete! Found {len(new_items)} newly announced vacancies.")
            else:
                await update.message.reply_text("✅ Scan complete. No newly posted vacancies since last check. All sources are monitored automatically every 15 minutes.")
        except Exception as e:
            logger.error(f"Error during on-demand check: {e}")
            await update.message.reply_text(f"⚠️ Scan encountered an error: {e}")

    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /latest command."""
        chat_id = str(update.effective_chat.id)
        user_track = self.db.get_subscriber_track(chat_id)
        recent = self.db.get_recent_vacancies(category=user_track if user_track != "ALL" else None, limit=5)

        if not recent:
            await update.message.reply_text("ℹ️ No vacancies currently logged for your track in the database. Run /check to scan.")
            return

        text = f"📜 <b>Recent Ethiopian Airlines Vacancies ({TRACK_NAMES.get(user_track, user_track)}):</b>\n\n"
        for idx, vac in enumerate(recent, 1):
            cat = vac.get("category", "PILOT")
            icon = "✈️" if cat == "PILOT" else ("🧑‍✈️" if cat == "CABIN_CREW" else "🔧")
            text += (
                f"<b>{idx}. {icon} {vac['title']}</b>\n"
                f"🏷️ Track: {cat.replace('_', ' ').title()}\n"
                f"🏛️ Portal: {vac['source']}\n"
                f"⏰ Deadline: {vac.get('deadline') or 'Check portal'}\n"
                f"🔗 <a href=\"{vac['url']}\">View Details & Apply</a>\n\n"
            )
        await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)

    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command."""
        chat_id = str(update.effective_chat.id)
        user_track = self.db.get_subscriber_track(chat_id)
        category_to_test = user_track if user_track in ["PILOT", "CABIN_CREW", "MAINTENANCE"] else "PILOT"

        success = self.notifier.send_test_alert(chat_id, category=category_to_test)
        if not success:
            await update.message.reply_text("⚠️ Could not dispatch test alert. Please verify your TELEGRAM_BOT_TOKEN in .env.")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command - unsubscribe."""
        chat_id = str(update.effective_chat.id)
        self.db.remove_subscriber(chat_id)
        await update.message.reply_text("🔕 You have been unsubscribed from alerts. Send /start anytime to reactivate.")
