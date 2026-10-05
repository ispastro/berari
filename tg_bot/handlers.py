import logging
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

from database.db import Database
from tg_bot.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class TelegramBotHandlers:
    def __init__(self, db: Database, notifier: TelegramNotifier, manual_check_callback: Callable[[], Any]):
        self.db = db
        self.notifier = notifier
        self.manual_check_callback = manual_check_callback

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - registers user for alerts."""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)

        self.db.add_subscriber(
            chat_id=chat_id,
            username=user.username,
            first_name=user.first_name,
        )

        welcome_text = (
            f"👋 Hello <b>{user.first_name or 'there'}</b>!\n\n"
            "✈️ Welcome to <b>Avaitor</b> — your automated Ethiopian Airlines Pilot Trainee Vacancy Monitor.\n\n"
            "🔔 You are now <b>subscribed</b> to instant push alerts! When Ethiopian Airlines or Ethiopian Aviation "
            "University posts an opening for Pilot Trainee, Cadet, or Ab-Initio programs, you will get notified immediately.\n\n"
            "<b>Available Commands:</b>\n"
            "🔍 /check - Run an instant live scan across all Ethiopian portals right now\n"
            "📊 /status - View monitor status, uptime, and stats\n"
            "📜 /latest - View the latest tracked pilot openings\n"
            "🧪 /test - Send a test alert to verify notification sounds\n"
            "❓ /help - View command list"
        )
        await update.message.reply_text(welcome_text, parse_mode="HTML")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "✈️ <b>Avaitor Command Menu</b>\n\n"
            "• /check - Trigger a real-time scan of Ethiopian Airlines portals\n"
            "• /status - Check bot health, last scan time, and tracked listings\n"
            "• /latest - Display recently discovered pilot vacancies\n"
            "• /test - Test notification card and sound\n"
            "• /stop - Unsubscribe from automatic alerts"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        stats = self.db.get_stats()
        text = (
            "📊 <b>Avaitor Monitor Status</b>\n\n"
            f"🟢 <b>Bot Status:</b> Operational & Monitoring 24/7\n"
            f"🎯 <b>Target:</b> Ethiopian Airlines & Ethiopian Aviation University\n"
            f"👥 <b>Subscribers:</b> {stats['subscribers_count']}\n"
            f"💼 <b>Active Pilot Vacancies:</b> {stats['active_vacancies']}\n"
            f"📦 <b>Total Vacancies Logged:</b> {stats['total_vacancies']}\n\n"
            f"⏱️ <b>Last Scan:</b> <code>{stats['last_scrape_time']}</code>\n"
            f"📡 <b>Last Source Checked:</b> {stats['last_scrape_source']}\n"
            f"🚦 <b>Last Scan Status:</b> {stats['last_scrape_status']}"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command - on-demand scan."""
        await update.message.reply_text("🔄 Initiating live scan of Ethiopian Airlines and University portals... Please wait a few seconds.")
        try:
            new_items = self.manual_check_callback()
            if new_items:
                await update.message.reply_text(f"✅ Scan complete! Found {len(new_items)} active pilot trainee vacancies.")
            else:
                await update.message.reply_text("✅ Scan complete. No newly posted pilot trainee openings at this exact moment. All sources are being monitored continuously.")
        except Exception as e:
            logger.error(f"Error during on-demand check: {e}")
            await update.message.reply_text(f"⚠️ Scan encountered an error: {e}")

    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /latest command."""
        recent = self.db.get_recent_vacancies(limit=5)
        if not recent:
            await update.message.reply_text("ℹ️ No pilot trainee vacancies currently logged in the database. Run /check to scan.")
            return

        text = "📜 <b>Recent Pilot Announcements:</b>\n\n"
        for idx, vac in enumerate(recent, 1):
            text += (
                f"<b>{idx}. {vac['title']}</b>\n"
                f"🏛️ Source: {vac['source']}\n"
                f"⏰ Deadline: {vac.get('deadline') or 'Check portal'}\n"
                f"🔗 <a href=\"{vac['url']}\">View Details</a>\n\n"
            )
        await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)

    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command."""
        chat_id = str(update.effective_chat.id)
        success = self.notifier.send_test_alert(chat_id)
        if not success:
            await update.message.reply_text("⚠️ Could not dispatch test alert. Please verify your TELEGRAM_BOT_TOKEN in .env.")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command - unsubscribe."""
        chat_id = str(update.effective_chat.id)
        self.db.remove_subscriber(chat_id)
        await update.message.reply_text("🔕 You have been unsubscribed from automatic alerts. Send /start anytime to reactivate.")
