from utils.mcp_instance import mcp
import asyncio
from pydantic import Field
from typing import Optional
from services.local import (
    compress_media,
    check_preparation_progress,
    search_locally
)



@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    },
    description = "Search for media files in the local downloads directory."
)
async def searchLocally() -> dict:
    return await asyncio.to_thread(search_locally)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    },
    description = "Compress the media file to reduce its size for upload and convert it to mp4."
)
async def prepareMedia(
    file_path: str = Field(description="Path to the media file to be prepared for upload."),
    torrent_hash: Optional[str] = Field(default=None, description="Optional torrent hash to stop and remove after compression."),
    ) -> dict:
    return await asyncio.to_thread(compress_media, file_path, torrent_hash)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    },
    description = "Check the progress of a media preparing job for a given source file path."
)
async def checkMediaPreparing(
    file_path: str = Field(description="Path to the media file for which the preparation progress should be checked.")
    ) -> dict:
    return await asyncio.to_thread(check_preparation_progress, file_path)
