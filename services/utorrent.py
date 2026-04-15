import logging
import requests
import re
import subprocess
from pathlib import Path
from requests.auth import HTTPBasicAuth
from utils.helpers import (
    DOWNLOAD_DIR,
    TORRENT_CLIENT,
    UT_LOCATION,
    UTORRENT_URL,
    UTORRENT_USERNAME,
    UTORRENT_PASSWORD,
)
import os



session = None


def _resolve_client_mode() -> str:
    if TORRENT_CLIENT in {"utorrent", "utserver"}:
        return TORRENT_CLIENT
    return "utorrent" if os.name == "nt" else "utserver"


def start_utorrent():
    """Start torrent client (uTorrent on Windows, utserver on Linux by default)."""
    client_mode = _resolve_client_mode()

    if client_mode == "utorrent":
        if not UT_LOCATION:
            return "Failed to start uTorrent: UTORRENT_LOCATION is not configured."
        if os.name != "nt":
            return "Failed to start uTorrent: this client mode is supported only on Windows."

        try:
            os.startfile(UT_LOCATION)
            return "uTorrent started successfully."
        except Exception as exc:
            return f"Failed to start uTorrent: {exc}"

    client_binary = UT_LOCATION
    if not client_binary:
        return "Failed to start utserver: set UT_LOCATION."

    try:
        subprocess.Popen(
            [client_binary],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"utserver started successfully using {client_binary}."
    except Exception as exc:
        return f"Failed to start utserver: {exc}"


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
        "download_dir": DOWNLOAD_DIR,
        "response": response.json() if response.content else {}
    }

def stop_torrent(torrent_hash: str) -> dict:
    """Stop a torrent by its hash."""
    session = _create_session()
    token = _get_token()
    if not token:
        return {
            "status": "error",
            "message": "Failed to retrieve uTorrent token.",
            "torrent_hash": torrent_hash
        }
    
    try:
        logging.info(f"Attempting to stop torrent with hash: {torrent_hash}")
        session.get(UTORRENT_URL, params={
            "token": token,
            "action": "stop",
            "hash": torrent_hash
        }).raise_for_status()

        logging.info(f"Successfully stopped torrent with hash: {torrent_hash}")
        
        return {
            "status": "stopped",
            "torrent_hash": torrent_hash
        }
    except Exception as exc:
        logging.exception(f"Failed to stop torrent {torrent_hash}")
        return {
            "status": "error",
            "message": f"Failed to stop torrent: {exc}",
            "torrent_hash": torrent_hash
        }


def remove_torrent_data(torrent_hash: str) -> dict:
    """Remove data for a torrent by its hash."""
    session = _create_session()
    token = _get_token()
    if not token:
        return {
            "status": "error",
            "message": "Failed to retrieve uTorrent token.",
            "torrent_hash": torrent_hash
        }
    
    try:
        logging.info(f"Attempting to remove data for torrent with hash: {torrent_hash}")
        session.get(UTORRENT_URL, params={
            "token": token,
            "action": "removedata",
            "hash": torrent_hash
        }).raise_for_status()

        logging.info(f"Successfully removed data for torrent with hash: {torrent_hash}")
        
        return {
            "status": "removed",
            "torrent_hash": torrent_hash
        }
    except Exception as exc:
        logging.exception(f"Failed to remove data for torrent {torrent_hash}")
        return {
            "status": "error",
            "message": f"Failed to remove data: {exc}",
            "torrent_hash": torrent_hash
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

        target = torrent_identifier.strip().lower().replace(".torrent", "").replace(".mkv", "")
        selected = None
        for torrent in torrents:
            if torrent["hash"].lower() == target or torrent["name"].lower().replace(".torrent", "").replace(".mkv", "") == target:
                selected = torrent
                break

        if not selected:
            return {
                "status": "not_found",
                "message": f"Torrent not found: {torrent_identifier}",
                "torrent_identifier": torrent_identifier,
            }

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


def stop_and_cleanup_torrent(torrent_hash: str) -> dict:
    stop_result = stop_torrent(torrent_hash)
    if stop_result.get("status") == "error":
        return stop_result

    remove_result = remove_torrent_data(torrent_hash)
    if remove_result.get("status") == "error":
        return remove_result

    return {
        "status": "stopped_and_removed",
        "torrent_hash": torrent_hash,
    }
