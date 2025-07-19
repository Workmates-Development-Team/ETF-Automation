import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
DB_URL = os.environ.get("DB_URL")

if not CLIENT_ID or not ACCESS_TOKEN or not DB_URL:
    raise RuntimeError("CLIENT_ID, ACCESS_TOKEN, and DB_URL must be set in the environment or .env file")

# Set up IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)