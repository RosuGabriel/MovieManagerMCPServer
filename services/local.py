import logging
import os
from helpers import DOWNLOAD_DIR
import subprocess
from pathlib import Path
import re
from datetime import timedelta
import time
from threading import Lock, Thread
from typing import Optional



_COMPRESSION_JOBS = {}
_COMPRESSION_JOBS_LOCK = Lock()


def _get_media_duration_seconds(media_path: Path) -> Optional[float]:
    process = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        return None

    try:
        value = process.stdout.strip()
        return float(value) if value else None
    except ValueError:
        return None


def _parse_ffmpeg_progress(progress_file: Path) -> dict:
    if not progress_file.exists():
        return {}

    content = progress_file.read_text(encoding="utf-8", errors="ignore")
    if not content.strip():
        return {}

    snapshot = {}
    for line in content.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        snapshot[key.strip()] = value.strip()

    return snapshot


def _run_compression_job(media_path: Path, media_key: str) -> None:
    output_file = media_path.with_name(f"{media_path.stem}_temp.mp4")
    progress_file = media_path.with_name(f"{media_path.stem}_compress.progress")

    process = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-progress",
            str(progress_file),
            "-i",
            str(media_path),
            "-c:v",
            "hevc_nvenc",
            "-c:a",
            "aac",
            "-ac",
            "2",
            "-b:a",
            "192k",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        with _COMPRESSION_JOBS_LOCK:
            _COMPRESSION_JOBS[media_key]["status"] = "failed"
            _COMPRESSION_JOBS[media_key]["error"] = process.stderr.strip() or process.stdout.strip()
            _COMPRESSION_JOBS[media_key]["stdout"] = process.stdout.strip()
            _COMPRESSION_JOBS[media_key]["stderr"] = process.stderr.strip()
            _COMPRESSION_JOBS[media_key]["exit_code"] = process.returncode
        return

    final_path = media_path.with_suffix(".mp4")

    try:
        media_path.unlink()
    except OSError as exc:
        with _COMPRESSION_JOBS_LOCK:
            _COMPRESSION_JOBS[media_key]["status"] = "failed"
            _COMPRESSION_JOBS[media_key]["error"] = (
                "Error deleting the original file. It might be in use or you might not have permission."
            )
            _COMPRESSION_JOBS[media_key]["stderr"] = str(exc)
            _COMPRESSION_JOBS[media_key]["exit_code"] = 1
        return

    try:
        output_file.replace(final_path)
    except OSError as exc:
        with _COMPRESSION_JOBS_LOCK:
            _COMPRESSION_JOBS[media_key]["status"] = "failed"
            _COMPRESSION_JOBS[media_key]["error"] = (
                "Error renaming the output file. The file might be in use or you might not have permission."
            )
            _COMPRESSION_JOBS[media_key]["stderr"] = str(exc)
            _COMPRESSION_JOBS[media_key]["exit_code"] = 1
        return

    with _COMPRESSION_JOBS_LOCK:
        _COMPRESSION_JOBS[media_key]["status"] = "completed"
        _COMPRESSION_JOBS[media_key]["output_file"] = str(final_path)
        _COMPRESSION_JOBS[media_key]["stdout"] = process.stdout.strip()
        _COMPRESSION_JOBS[media_key]["stderr"] = process.stderr.strip()
        _COMPRESSION_JOBS[media_key]["exit_code"] = process.returncode



def compress_media(file_path: str) -> dict:
    """
    Compress media using ffmpeg and replace the original file with an .mp4 output.
    """
    media_path = Path(file_path)
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found: {file_path}")

    media_key = str(media_path.resolve()).lower()
    output_file = media_path.with_name(f"{media_path.stem}_temp.mp4")
    progress_file = media_path.with_name(f"{media_path.stem}_compress.progress")
    duration_seconds = _get_media_duration_seconds(media_path)

    if progress_file.exists():
        try:
            progress_file.unlink()
        except OSError as exc:
            logging.warning("Unable to remove stale progress file %s: %s", progress_file, exc)

    with _COMPRESSION_JOBS_LOCK:
        existing_job = _COMPRESSION_JOBS.get(media_key)
        if existing_job and existing_job.get("status") == "running":
            return {
                "status": "already_running",
                "input_file": existing_job.get("input_file", str(media_path)),
                "output_file": existing_job.get("output_file", str(output_file)),
                "progress_file": existing_job.get("progress_file", str(progress_file)),
            }

        _COMPRESSION_JOBS[media_key] = {
            "status": "running",
            "input_file": str(media_path),
            "output_file": str(output_file),
            "progress_file": str(progress_file),
            "duration_seconds": duration_seconds,
            "error": "",
            "stdout": "",
            "stderr": "",
            "exit_code": None,
        }

    Thread(target=_run_compression_job, args=(media_path, media_key), daemon=True).start()

    return {
        "status": "started",
        "input_file": str(media_path),
        "output_file": str(output_file),
        "progress_file": str(progress_file),
    }


def delete_file(file_path: str) -> dict:
    """Delete a specified file from the local storage."""
    target_path = Path(file_path)
    if not target_path.exists():
        return {
            "status": "not found",
            "file_path": str(target_path),
        }

    try:
        target_path.unlink()
        return {
            "status": "deleted",
            "file_path": str(target_path),
        }
    except OSError as exc:
        raise RuntimeError(f"Error deleting file: {exc}") from exc


def check_preparation_progress(file_path: str) -> dict:
    media_path = Path(file_path)
    media_key = str(media_path.resolve()).lower()
    progress_file = media_path.with_name(f"{media_path.stem}_compress.progress")
    temp_output = media_path.with_name(f"{media_path.stem}_temp.mp4")
    final_output = media_path.with_suffix(".mp4")

    with _COMPRESSION_JOBS_LOCK:
        job = _COMPRESSION_JOBS.get(media_key, {}).copy()

    if not job:
        if final_output.exists() and not media_path.exists():
            time.sleep(3)
            return {
                "status": "completed",
                "input_file": str(media_path),
                "output_file": str(final_output),
                "progress_percent": 100.0,
                "progress file": _delete_file_safely(progress_file),
                "original file": _delete_file_safely(media_path),
            }

        if temp_output.exists() or progress_file.exists():
            job = {
                "status": "running",
                "input_file": str(media_path),
                "output_file": str(temp_output),
                "progress_file": str(progress_file),
                "duration_seconds": _get_media_duration_seconds(media_path) if media_path.exists() else None,
                "error": "",
            }
        else:
            return {
                "status": "not_started",
                "input_file": str(media_path),
                "output_file": str(final_output),
                "progress_percent": 0.0,
            }

    parsed = _parse_ffmpeg_progress(progress_file)
    out_time_ms_raw = parsed.get("out_time_ms")
    duration_seconds = job.get("duration_seconds")

    progress_percent = 0.0
    if out_time_ms_raw and duration_seconds and duration_seconds > 0:
        try:
            out_time_seconds = int(out_time_ms_raw) / 1_000_000
            progress_percent = max(0.0, min(100.0, (out_time_seconds / duration_seconds) * 100.0))
        except ValueError:
            progress_percent = 0.0

    if job.get("status") == "completed":
        progress_percent = 100.0

    return {
        "status": job.get("status", "unknown"),
        "input_file": job.get("input_file", str(media_path)),
        "output_file": job.get("output_file", str(final_output)),
        "progress_file": str(progress_file),
        "progress_percent": round(progress_percent, 2),
        "exit_code": job.get("exit_code"),
        "ffmpeg": {
            "speed": parsed.get("speed", ""),
            "fps": parsed.get("fps", ""),
            "bitrate": parsed.get("bitrate", ""),
            "out_time": parsed.get("out_time", ""),
            "progress": parsed.get("progress", ""),
        },
        "stdout": job.get("stdout", ""),
        "stderr": job.get("stderr", ""),
        "error": job.get("error", ""),
    }


def search_locally():
    files = []
    for root, _, filenames in os.walk(DOWNLOAD_DIR):
        for name in filenames:
            full_path = Path(root) / name
            files.append(str(full_path.relative_to(DOWNLOAD_DIR)))

    return {
        "path": DOWNLOAD_DIR,
        "files": files,
    }


def crop_poster(file_path: str) -> dict:
    """Crop the poster image to a 2:3 aspect ratio (centered)."""
    from PIL import Image

    img_path = Path(file_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")

    with Image.open(img_path) as img:
        w, h = img.size
        target_ratio = 2 / 3

        if w / h > target_ratio:
            # Too wide — crop width
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            box = (left, 0, left + new_w, h)
        else:
            # Too tall — crop height
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            box = (0, top, w, top + new_h)

        cropped = img.crop(box)
        cropped.save(img_path)

    return {
        "file_path": str(img_path),
        "original_size": f"{w}x{h}",
        "cropped_size": f"{cropped.width}x{cropped.height}",
        "status": "cropped",
    }


def process_subtitles(input_file: str, output_file: str=None, offset_seconds: float=0) -> None:
    """
    Converts subtitle file from SRT to VTT format and applies a time offset if specified.
    Shift all timestamps in an SRT file by offset_seconds.
    Positive = add, negative = subtract.
    """
    if not offset_seconds and input_file.lower().endswith(".vtt"):
        logging.info(f"No offset specified and file is already in VTT format. Skipping processing for {input_file}.")
        return
    
    srt_path = Path(input_file)
    if not srt_path.exists():
        raise FileNotFoundError(f"{input_file} not found.")

    srt_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
    vtt_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2}).(\d{3})")

    def process_timestamp(match):
        h, m, s, ms = map(int, match.groups())

        if offset_seconds == 0:
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"

        td = timedelta(hours=h, minutes=m, seconds=s, milliseconds=ms)
        td += timedelta(seconds=offset_seconds)

        if td.total_seconds() < 0:
            td = timedelta(0)

        total_ms = int(td.total_seconds() * 1000 + td.microseconds / 1000)
        h2 = total_ms // (3600*1000)
        total_ms %= 3600*1000
        m2 = total_ms // (60*1000)
        total_ms %= 60*1000
        s2 = total_ms // 1000
        return f"{h2:02}:{m2:02}:{s2:02}.{ms:03}"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "WEBVTT" not in content[:20]:
        new_content = srt_pattern.sub(process_timestamp, content)
        new_content = f"WEBVTT\n\n{new_content.lstrip()}"
    else:
        new_content = vtt_pattern.sub(process_timestamp, content)


    if output_file is None:
        output_file = input_file

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)
        f.flush()

    logging.info(f"Processed subtitles saved to {output_file}")


def _delete_file_safely(target_path: Path) -> dict:
    if not target_path.exists():
        return {
            "status": "not found",
            "file_path": str(target_path),
        }

    try:
        target_path.unlink()
        return {
            "status": "deleted",
            "file_path": str(target_path),
        }
    except OSError as exc:
        logging.warning("Unable to delete file %s: %s", target_path, exc)
        return {
            "status": "locked",
            "file_path": str(target_path),
            "error": str(exc),
        }
