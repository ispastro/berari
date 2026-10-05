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
logger = logging.getLogger("Avaitor")

class AvaitorApp:
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.notifier = TelegramNotifier()
        self.scrapers = [
            EthiopianCareersScraper(),
            EAUScraper(),
            EthiojobsScraper(),
        ]
        # Auto-subscribe default chat id if configured in .env
        if TELEGRAM_CHAT_ID:
            self.db.add_subscriber(TELEGRAM_CHAT_ID, username="Admin", first_name="Admin")

    def run_check_cycle(self) -> List[Dict[str, Any]]:
        """
        Execute a full scrape cycle across all portals,
        store new vacancies in database, and trigger alerts.
        """
        logger.info("==================================================")
        logger.info("Starting scan for Ethiopian Airlines Pilot Trainee openings...")
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
                        deadline=item.deadline,
                        summary=item.summary,
                    )
                    
                    if result["is_new"] or not result["already_notified"]:
                        logger.info(f"✨ NEW PILOT VACANCY DISCOVERED: {item.title} ({item.source})")
                        vacancy_data = {
                            "title": item.title,
                            "source": item.source,
                            "url": item.url,
                            "deadline": item.deadline,
                            "summary": item.summary,
                            "job_hash": result["job_hash"],
                        }
                        new_vacancies_found.append(vacancy_data)

            except Exception as e:
                logger.error(f"Error while running {scraper.name}: {e}")
                self.db.record_scrape(source=scraper.name, status="ERROR", items_found=0, error=str(e))

        # Broadcast alerts for any new vacancies
        if new_vacancies_found:
            subscribers = self.db.get_active_subscribers()
            logger.info(f"Broadcasting {len(new_vacancies_found)} new vacancy alert(s) to {len(subscribers)} subscriber(s)...")

            for vac in new_vacancies_found:
                sent = self.notifier.broadcast_vacancy(vac, subscribers)
                if sent > 0 or not self.notifier.is_configured:
                    self.db.mark_notified(vac["job_hash"])
        else:
            logger.info("Scan finished: No new pilot trainee vacancies detected.")

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

        from telegram.ext import ApplicationBuilder, CommandHandler

        handlers = TelegramBotHandlers(
            db=self.db,
            notifier=self.notifier,
            manual_check_callback=self.run_check_cycle,
        )

        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", handlers.start))
        app.add_handler(CommandHandler("help", handlers.help_command))
        app.add_handler(CommandHandler("status", handlers.status))
        app.add_handler(CommandHandler("check", handlers.check))
        app.add_handler(CommandHandler("latest", handlers.latest))
        app.add_handler(CommandHandler("test", handlers.test))
        app.add_handler(CommandHandler("stop", handlers.stop))

        logger.info("Telegram interactive bot polling started. You can now chat with your bot!")
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
                logger.info("Avaitor monitor stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Avaitor - Ethiopian Airlines Pilot Trainee Vacancy Monitor")
    parser.add_argument("--check-once", action="store_true", help="Run a single scan right now and exit")
    parser.add_argument("--test-alert", action="store_true", help="Send a test notification card to your Telegram")
    parser.add_argument("--status", action="store_true", help="Display database and monitoring statistics")

    args = parser.parse_args()
    app = AvaitorApp()

    if args.status:
        stats = app.db.get_stats()
        print("\n--- AVAITOR MONITOR STATUS ---")
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
            print("ERROR: No TELEGRAM_CHAT_ID found in .env and no subscribers registered in database.")
            sys.exit(1)
        print(f"Sending test alert to {target}...")
        ok = app.notifier.send_test_alert(target)
        print("Success!" if ok else "Failed.")
        sys.exit(0)

    if args.check_once:
        print("Running one-time check across all Ethiopian Airlines portals...")
        results = app.run_check_cycle()
        print(f"\nDone! Found {len(results)} new pilot trainee opening(s).")
        sys.exit(0)

    # Default: Run full 24/7 daemon
    app.start()

if __name__ == "__main__":
    main()
