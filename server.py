import asyncio
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from utils.browser import close_browser
from tools.sourcing import search_torrents, get_poster, get_torrent_source
from tools.utorrent import start_utorrent, download_torrent, check_download_progress
from tools.local import compress_media, check_preparation_progress, search_locally
from tools.redpanda import upload_episode, upload_media



mcp = FastMCP("Movie Manager Server")


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def searchLocally() -> dict:
    """
    Search for media files in the local downloads directory.
    """
    return await asyncio.to_thread(search_locally)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def searchMedia(
    query: str = Field(description="The title of the movie or series to search for (no metadata).")
    ) -> dict:
    """
    Search for movies or series or season of a series files based on a query (simple title).
    """
    results = await search_torrents(query=query)
    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def getTorrent(
    link: str = Field(description="The URL obtained with the searchMedia tool.")
    ) -> dict:
    """
    Download an official source file from the specified link.
    """
    return await get_torrent_source(link)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def startUTorrent() -> str:
    """
    Start the uTorrent client.
    """
    return await asyncio.to_thread(start_utorrent)


@mcp.tool(
        annotations = {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
async def downloadTorrent(
    file_path: str
    ) -> dict:
    """
    Use the torrent file to extract media (usually .mkv).
    """
    return await asyncio.to_thread(download_torrent, file_path)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def checkTorrent(
    torrent_identifier: str = Field(description="Hash or exact local torrent file name without extension.")
    ) -> dict:
    """
    Check the status of a specific torrent download using torrent identifier.
    """
    return await asyncio.to_thread(check_download_progress, torrent_identifier)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def prepareMedia(
    file_path: str
    ) -> dict:
    """
    Compress the media file to reduce its size for upload and convert it to mp4.
    """
    return await asyncio.to_thread(compress_media, file_path)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def checkMediaPreparing(
    file_path: str
    ) -> dict:
    """
    Check the progress of a media preparing job for a given source file path.
    """
    return await asyncio.to_thread(check_preparation_progress, file_path)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def downloadPoster(
    title: str
    ) -> dict:
    """
    Search for a poster for the specified title.
    """
    return await get_poster(title)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def uploadMedia(  
    mediaType: str = Field(description="Type of the media: 'movie' or 'series'."),
    title: str = Field(description="Title of the media."),
    video_path: str = Field(description="Path to the media file (only for movies)."),
    poster_path: str = Field(description="Path to the poster file."),
    description: str = Field(description="Description of the media (optional)."),
    release_date: str = Field(description="Release date (YYYY-MM-DD) of the media (optional)."),
    seasonsNumber: str = Field(description="Number of seasons (only for series).")
    ) -> dict:
    """
    Upload the processed media file to the website.
    """
    return await upload_media(mediaType=mediaType, title=title, video_path=video_path, poster_path=poster_path, description=description, release_date=release_date, seasonsNumber=seasonsNumber)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def uploadEpisode(
    seriesTitle: str = Field(description="Title of the series."),
    seasonNumber: str = Field(description="Number of the season."),
    episodeNumber: str = Field(description="Number of the episode."),
    episodeTitle: str = Field(description="Title of the episode. (preffered but optional)"),
    video_path: str = Field(description="Path to the episode file."),
    poster_path: str = Field(description="Path to the poster file. (optional - usually not needed for episodes)"),
    description: str = Field(description="Description of the episode (optional)."),
    release_date: str = Field(description="Release date (YYYY-MM-DD) of the episode (optional).")
    ) -> dict:
    """
    Upload the processed episode file of a series to the website.
    """
    return await upload_episode(series_title=seriesTitle, season_number=seasonNumber, episode_number=episodeNumber, episode_title=episodeTitle, video_path=video_path, poster_path=poster_path, description=description, release_date=release_date)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def closeSession() -> str:
    """
    Close the persistent browser session manually.
    """
    await close_browser()
    return "Session closed"


if __name__ == "__main__":
    mcp.run()
