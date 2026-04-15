from utils.mcp_instance import mcp
import asyncio
from pydantic import Field
from services.utorrent import (
    start_utorrent,
    download_torrent,
    check_download_progress,
    stop_and_cleanup_torrent
)



@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    },
    description="Start the uTorrent client."
)
async def startUTorrent() -> str:
    return await asyncio.to_thread(start_utorrent)


@mcp.tool(
        annotations = {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        },
        description = "Use the torrent file to extract media (usually .mkv)."
    )
async def downloadTorrent(
    file_path: str = Field(description="Path to the torrent file to be downloaded.")
    ) -> dict:
    return await asyncio.to_thread(download_torrent, file_path)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    },
    description = "Check the status of a specific torrent download using torrent identifier."
)
async def checkTorrent(
    torrent_identifier: str = Field(description="Hash or exact local torrent file name with or without extension (a total of 3 options).")
    ) -> dict:
    return await asyncio.to_thread(check_download_progress, torrent_identifier)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    },
    description = "Stop the torrent and cleanup associated data."
)
async def stopTorrent(
    torrent_identifier: str = Field(description="Hash or exact local torrent file name with or without extension (a total of 3 options).")
    ) -> dict:
    return await asyncio.to_thread(stop_and_cleanup_torrent, torrent_identifier)
