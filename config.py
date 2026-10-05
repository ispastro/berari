import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Bot Name & Identity
BOT_NAME = "Berari (በራሪ) - EtwingBot"
BOT_USERNAME = "EtwingBot"

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Monitoring Interval (in minutes)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Storage
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "avaitor.db"

# Scraper Endpoints
ET_CAREERS_URL = "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies"
ET_UNIVERSITY_URL = "https://eau.edu.et"
ET_ETHIOJOBS_URL = "https://www.ethiojobs.net/jobs-in-ethiopia/ethiopian-airlines-group/"

# Scraper Enable Toggles (Default: Corporate Careers Only)
ENABLE_CORPORATE_CAREERS = os.getenv("ENABLE_CORPORATE_CAREERS", "true").lower() == "true"
ENABLE_UNIVERSITY = os.getenv("ENABLE_UNIVERSITY", "false").lower() == "true"
ENABLE_ETHIOJOBS = os.getenv("ENABLE_ETHIOJOBS", "false").lower() == "true"

# HTTP Headers to mimic regular browser navigation
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Categorized Matching Keywords
PILOT_KEYWORDS = [
    "pilot trainee",
    "trainee pilot",
    "cadet pilot",
    "student pilot",
    "commercial pilot license",
    "commercial pilot",
    "ab-initio pilot",
    "ab-initio",
    "pilot training",
    "first officer trainee",
    "trainee first officer",
    "cpl",
]

CABIN_CREW_KEYWORDS = [
    "cabin crew",
    "flight attendant",
    "air hostess",
    "cabin crew trainee",
    "trainee cabin crew",
]

MAINTENANCE_KEYWORDS = [
    "aircraft technician",
    "aircraft mechanic",
    "aircraft maintenance",
    "avionics",
    "technician trainee",
    "maintenance trainee",
    "junior technician",
    "powerplant",
    "airframe",
    "aviation maintenance",
]

# Irrelevant non-aviation roles to exclude
EXCLUDED_KEYWORDS = [
    "call center",
    "ticketing",
    "customer service agent",
    "catering",
    "cargo handler",
    "baggage handler",
    "cleaner",
    "driver",
    "security officer",
    "cook",
    "waiter",
    "gardener",
]
