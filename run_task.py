#!/usr/bin/env python3
"""
PythonAnywhere Scheduled Task Runner for Berari (@EtwingBot).
Use this in the PythonAnywhere 'Tasks' tab to periodically check
Ethiopian Airlines portals and dispatch Telegram alerts.
"""
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from bot import AvaitorApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PythonAnywhereTask")

def main():
    logger.info("--- Starting PythonAnywhere Scheduled Check ---")
    app = AvaitorApp()
    try:
        new_vacancies = app.run_check_cycle()
        logger.info(f"Task finished successfully. {len(new_vacancies)} new vacancy alerts processed.")
    except Exception as e:
        logger.error(f"Error during scheduled execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
