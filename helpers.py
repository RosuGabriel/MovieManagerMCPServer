import os
from pathlib import Path
from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

FILELIST_URL = "https://filelist.io/"
FILELIST_LOGIN_URL = FILELIST_URL + "login.php"
FILELIST_BROWSE_URL = FILELIST_URL + "browse.php"
FILELIST_DOWNLOAD_URL = FILELIST_URL + "download.php"

FILELIST_USERNAME = os.getenv("FILELIST_USERNAME")
FILELIST_PASSWORD = os.getenv("FILELIST_PASSWORD")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
DOWNLOAD_DIR = Path(DOWNLOAD_DIR)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

UTORRENT_LOCATION = os.getenv("UTORRENT_LOCATION")
UTORRENT_URL = os.getenv("UTORRENT_URL")
UTORRENT_USERNAME = os.getenv("UTORRENT_USERNAME")
UTORRENT_PASSWORD = os.getenv("UTORRENT_PASSWORD")
UTORRENT_DESTINATION_DIR = os.getenv("UTORRENT_DESTINATION_DIR")

REDPANDA_URL = "https://red-panda.go.ro/mymdb/"
REDPANDA_LOGIN_URL = REDPANDA_URL + "login"
REDPANDA_MEDIA_URL = REDPANDA_URL + "media"
REDPANDA_CREATE_URL = REDPANDA_URL + "create"

REDPANDA_USERNAME = os.getenv("REDPANDA_USERNAME")
REDPANDA_PASSWORD = os.getenv("REDPANDA_PASSWORD")
