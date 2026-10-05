import sys
import time
import logging
import argparse
import threading
from typing import List, Dict, Any

from config import (
    DATABASE_PATH,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    CHECK_INTERVAL_MINUTES,
    LOG_LEVEL,
    BOT_NAME,
    ENABLE_CORPORATE_CAREERS,
    ENABLE_UNIVERSITY,
    ENABLE_ETHIOJOBS,
)
from database.db import Database
from scrapers.base import VacancyItem
from scrapers.ethiopian_careers import EthiopianCareersScraper
from scrapers.eau_scraper import EAUScraper
from scrapers.ethiojobs_scraper import EthiojobsScraper
from tg_bot.notifier import TelegramNotifier
from tg_bot.handlers import TelegramBotHandlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Berari")

class AvaitorApp:
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.notifier = TelegramNotifier()
        self.scrapers = []
        if ENABLE_CORPORATE_CAREERS:
            self.scrapers.append(EthiopianCareersScraper())
        if ENABLE_UNIVERSITY:
            self.scrapers.append(EAUScraper())
        if ENABLE_ETHIOJOBS:
            self.scrapers.append(EthiojobsScraper())
        # Auto-subscribe default chat id if configured in .env
        if TELEGRAM_CHAT_ID:
            self.db.add_subscriber(TELEGRAM_CHAT_ID, username="Admin", first_name="Admin", track="ALL")

    def run_check_cycle(self) -> List[Dict[str, Any]]:
        """
        Execute a full scrape cycle across all portals,
        store new vacancies in database, and trigger targeted alerts.
        """
        logger.info("==================================================")
        logger.info("Starting scan for Ethiopian Airlines career openings (Pilot / Cabin Crew / Maintenance)...")
        new_vacancies_found: List[Dict[str, Any]] = []

        for scraper in self.scrapers:
            try:
                items: List[VacancyItem] = scraper.scrape()
                self.db.record_scrape(source=scraper.name, status="SUCCESS", items_found=len(items))

                for item in items:
                    result = self.db.upsert_vacancy(
                        title=item.title,
                        source=item.source,
                        url=item.url,
                        category=item.category,
                        deadline=item.deadline,
                        summary=item.summary,
                    )
                    
                    if result["is_new"] or not result["already_notified"]:
                        logger.info(f"✨ NEW VACANCY DISCOVERED: [{item.category}] {item.title} ({item.source})")
                        vacancy_data = {
                            "title": item.title,
                            "source": item.source,
                            "url": item.url,
                            "category": item.category,
                            "deadline": item.deadline,
                            "summary": item.summary,
                            "job_hash": result["job_hash"],
                        }
                        new_vacancies_found.append(vacancy_data)

            except Exception as e:
                logger.error(f"Error while running {scraper.name}: {e}")
                self.db.record_scrape(source=scraper.name, status="ERROR", items_found=0, error=str(e))

        # Broadcast alerts for any new vacancies to matching track subscribers
        if new_vacancies_found:
            for vac in new_vacancies_found:
                category = vac.get("category", "PILOT")
                target_subscribers = self.db.get_subscribers_for_category(category)

                logger.info(
                    f"Broadcasting [{category}] '{vac['title']}' to {len(target_subscribers)} subscriber(s)..."
                )
                sent = self.notifier.broadcast_vacancy(vac, target_subscribers)
                if sent > 0 or not self.notifier.is_configured:
                    self.db.mark_notified(vac["job_hash"])
        else:
            logger.info("Scan finished: No new aviation vacancies detected.")

        logger.info("==================================================")
        return new_vacancies_found

    def scheduler_loop(self):
        """Background loop executing periodically."""
        interval_seconds = CHECK_INTERVAL_MINUTES * 60
        logger.info(f"Scheduler active: checking every {CHECK_INTERVAL_MINUTES} minutes.")
        
        while True:
            try:
                self.run_check_cycle()
            except Exception as e:
                logger.error(f"Unexpected exception in scheduled check: {e}", exc_info=True)
            
            time.sleep(interval_seconds)

    def start_telegram_bot(self):
        """Initialize and run the Telegram interactive bot polling."""
        if not self.notifier.is_configured:
            logger.warning("Telegram Bot Token is not set in .env! Interactive Telegram commands disabled.")
            logger.info("To enable Telegram, edit .env and set TELEGRAM_BOT_TOKEN.")
            return

        from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

        handlers = TelegramBotHandlers(
            db=self.db,
            notifier=self.notifier,
            manual_check_callback=self.run_check_cycle,
        )

        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", handlers.start))
        app.add_handler(CommandHandler("track", handlers.track_command))
        app.add_handler(CommandHandler("settings", handlers.track_command))
        app.add_handler(CommandHandler("help", handlers.help_command))
        app.add_handler(CommandHandler("status", handlers.status))
        app.add_handler(CommandHandler("check", handlers.check))
        app.add_handler(CommandHandler("latest", handlers.latest))
        app.add_handler(CommandHandler("test", handlers.test))
        app.add_handler(CommandHandler("stop", handlers.stop))
        app.add_handler(CallbackQueryHandler(handlers.handle_callback_query))

        logger.info(f"Telegram bot ({BOT_NAME}) is online and polling! Search @EtwingBot on Telegram.")
        app.run_polling()

    def start(self):
        """Run daemon: start background scheduler and Telegram bot."""
        # 1. Run first check cycle immediately upon startup
        logger.info("Running initial startup check...")
        self.run_check_cycle()

        # 2. Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        scheduler_thread.start()

        # 3. If Telegram is configured, run Telegram bot polling in main thread
        if self.notifier.is_configured:
            self.start_telegram_bot()
        else:
            logger.info("Running in background scheduler mode. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user.")


def main():
    parser = argparse.ArgumentParser(description=f"{BOT_NAME} - Ethiopian Airlines Career Monitor")
    parser.add_argument("--check-once", action="store_true", help="Run a single scan right now and exit")
    parser.add_argument("--test-alert", action="store_true", help="Send a test notification card to your Telegram")
    parser.add_argument("--status", action="store_true", help="Display database and monitoring statistics")

    args = parser.parse_args()
    app = AvaitorApp()

    if args.status:
        stats = app.db.get_stats()
        print(f"\n--- {BOT_NAME.upper()} STATUS ---")
        for k, v in stats.items():
            print(f"{k}: {v}")
        print("------------------------------\n")
        sys.exit(0)

    if args.test_alert:
        if not app.notifier.is_configured:
            print("ERROR: TELEGRAM_BOT_TOKEN is not configured in .env.")
            sys.exit(1)
        target = TELEGRAM_CHAT_ID or (app.db.get_active_subscribers() and app.db.get_active_subscribers()[0])
        if not target:
            print("ERROR: No chat ID found. Start the bot on Telegram (@EtwingBot) first with /start.")
            sys.exit(1)
        print(f"Sending test alert to {target}...")
        ok = app.notifier.send_test_alert(target)
        print("Success!" if ok else "Failed.")
        sys.exit(0)

    if args.check_once:
        print("Running one-time check across all Ethiopian Airlines portals...")
        results = app.run_check_cycle()
        print(f"\nDone! Found {len(results)} new opening(s).")
        sys.exit(0)

    # Default: Run full 24/7 daemon
    app.start()

if __name__ == "__main__":
    main()
