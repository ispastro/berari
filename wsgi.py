import os
import sys
from pathlib import Path

# Path to the project root on PythonAnywhere
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Ensure .env is loaded
from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

# Expose WSGI application object for PythonAnywhere
from webhook_app import app as application
