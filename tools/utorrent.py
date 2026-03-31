import logging
import requests
import re
from pathlib import Path
from requests.auth import HTTPBasicAuth
from helpers import DOWNLOAD_DIR, UTORRENT_LOCATION, UTORRENT_LOCATION, UTORRENT_LOCATION, UTORRENT_URL, UTORRENT_USERNAME, UTORRENT_PASSWORD
import os
from tools.local import delete_file



session = None


def start_utorrent():
    """Start uTorrent client."""
    try:
        os.startfile(UTORRENT_LOCATION)
        return "uTorrent started successfully."
    except Exception:
        return "Failed to start uTorrent."


def _create_session():
    global session
    if session is not None:
        return session
    session = requests.Session()
    session.auth = HTTPBasicAuth(UTORRENT_USERNAME, UTORRENT_PASSWORD)
    return session


def _get_token():
    session = _create_session()
    r = session.get(UTORRENT_URL + "token.html")
    r.raise_for_status()
    m = re.search(r"<div id='token'[^>]*>([^<]+)</div>", r.text)
    if not m:
        return None
    return m.group(1)


def download_torrent(file_path: str) -> dict:
    torrent_path = Path(file_path)

    if not torrent_path.exists():
        raise FileNotFoundError(f"Torrent file not found: {file_path}")

    session = _create_session()
    token = _get_token()
    if not token:
        return {
            "status": "error",
            "message": "Failed to retrieve uTorrent token.",
            "torrent_file": file_path
        }

    with open(file_path, "rb") as f:
        files = {"torrent_file": f}

        params = {
            "action": "add-file",
            "token": token
        }

        response = session.post(UTORRENT_URL, params=params, files=files)
        response.raise_for_status()

    return {
        "status": "started",
        "torrent_file": file_path,
        "download_dir": DOWNLOAD_DIR
    }


def check_download_progress(torrent_identifier: str) -> dict:
    session = _create_session()
    token = _get_token()
    if not token:
        return {
            "status": "error",
            "message": "Failed to retrieve uTorrent token."
        }

    try:
        # uTorrent WebUI expects list=1 for torrent listing on most versions.
        response = session.get(
            UTORRENT_URL,
            params={"list": 1, "token": token},
        )
        if response.status_code == 400:
            # Compatibility fallback for variants that accept action=list.
            response = session.get(
                UTORRENT_URL,
                params={"action": "list", "token": token},
            )
        response.raise_for_status()
        payload = response.json()

        torrents_raw = payload.get("torrents", [])
        torrents = []

        for item in torrents_raw:
            # uTorrent returns progress in per-mille (0-1000), convert to percent.
            progress_pct = round((item[4] / 10.0), 2)
            torrents.append(
                {
                    "hash": item[0],
                    "name": item[2],
                    "size": item[3],
                    "progress": progress_pct,
                    "status": item[1],
                    "download directory": item[26] if len(item) > 26 else "N/A",
                    "torrent_identifier": torrent_identifier,
                }
            )

        target = torrent_identifier.strip().lower()
        selected = None
        for torrent in torrents:
            if torrent["hash"].lower() == target or torrent["name"].lower() == target:
                selected = torrent
                break

        if not selected:
            return {
                "status": "not_found",
                "message": f"Torrent not found: {torrent_identifier}",
                "torrent_identifier": torrent_identifier,
            }
        
        if selected["progress"] >= 100.0:
            delete_file(str(Path(DOWNLOAD_DIR, selected["name"].with_suffix(".torrent"))))

        return {
            "status": selected["status"],
            "progress": selected["progress"],
            "torrent": selected,
            "torrent_identifier": torrent_identifier,
        }
    
    except Exception as exc:
        logging.exception("Failed to fetch uTorrent download progress")
        return {
            "status": "error",
            "message": f"Failed to fetch progress: {exc}",
            "torrent_identifier": torrent_identifier,
        }
