import os
from pathlib import Path
from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SOURCES_SITE_URL = os.getenv("SOURCES_SITE_URL")
if not SOURCES_SITE_URL:
    raise ValueError("SOURCES_SITE_URL must be set in environment variables.")
SOURCES_SITE_LOGIN_URL = SOURCES_SITE_URL + "login.php"
SOURCES_SITE_BROWSE_URL = SOURCES_SITE_URL + "browse.php"
SOURCES_SITE_DOWNLOAD_URL = SOURCES_SITE_URL + "download.php"

SOURCES_SITE_USERNAME = os.getenv("SOURCES_SITE_USERNAME")
SOURCES_SITE_PASSWORD = os.getenv("SOURCES_SITE_PASSWORD")
if not SOURCES_SITE_USERNAME or not SOURCES_SITE_PASSWORD:
    raise ValueError("SOURCES_SITE credentials must be set in environment variables.")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
if not DOWNLOAD_DIR:
    raise ValueError("DOWNLOAD_DIR must be set in environment variables.")
DOWNLOAD_DIR = Path(DOWNLOAD_DIR)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

UT_LOCATION = os.getenv("UT_LOCATION")
if not UT_LOCATION:
    raise ValueError("UT_LOCATION must be set in environment variables.")

TORRENT_CLIENT = os.getenv("TORRENT_CLIENT", "auto").strip().lower()

UTORRENT_URL = os.getenv("UTORRENT_URL")
UTORRENT_USERNAME = os.getenv("UTORRENT_USERNAME")
UTORRENT_PASSWORD = os.getenv("UTORRENT_PASSWORD")
if not UTORRENT_URL or not UTORRENT_USERNAME or not UTORRENT_PASSWORD:
    raise ValueError("uTorrent credentials and URL must be set in environment variables.")

REDPANDA_URL = os.getenv("REDPANDA_URL")
if not REDPANDA_URL:
    raise ValueError("REDPANDA_URL is not set in environment variables.")
REDPANDA_LOGIN_URL = REDPANDA_URL + "login"
REDPANDA_MEDIA_URL = REDPANDA_URL + "media"
REDPANDA_CREATE_URL = REDPANDA_URL + "create"

REDPANDA_USERNAME = os.getenv("REDPANDA_USERNAME")
REDPANDA_PASSWORD = os.getenv("REDPANDA_PASSWORD")
if not REDPANDA_USERNAME or not REDPANDA_PASSWORD:
    raise ValueError("REDPANDA credentials must be set in environment variables.")
