from utils.mcp_instance import mcp
from pydantic import Field
from services.sourcing import (
    download_subtitle,
    get_poster,
    get_torrent_source,
    search_subtitles,
    search_torrents
)



@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    },
    description = "Search for movies or series or season of a series files based on a query (simple title)."
)
async def searchMedia(
    query: str = Field(description="The title of the movie or series to search for (no metadata).")
    ) -> dict:
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
    },
    description = "Download the media file from the specified link obtained with the searchMedia tool."
)
async def getTorrent(
    link: str = Field(description="The URL obtained with the searchMedia tool.")
    ) -> dict:
    return await get_torrent_source(link)


@mcp.tool(
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    },
    description = "Search for a poster for the specified title over the web."
)
async def downloadPoster(
    title: str = Field(description="The title of the media for which to search for a poster.")
    ) -> dict:
    return await get_poster(title)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    },
    description = "Search for subtitles matching the query."
)
async def searchSubtitles(
    query: str = Field(description="The title of the movie or series + season/episode + quality and format if possible.")
    ) -> dict:
    return await search_subtitles(query)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    },
    description = "Download the subtitle file from the specified link obtained with the searchSubtitles tool."
)
async def downloadSubtitle(
    link: str = Field(description="Subtitle page URL obtained from searchSubtitles.")
    ) -> dict:
    return await download_subtitle(link)
