from typing import Optional
from mcp_instance import mcp
from pydantic import Field
from services.redpanda import (
    upload_episode,
    upload_media,
    upload_subtitle
)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    },
    description = "Upload the processed media file to the website. (both movies and series)"
)
async def uploadMedia(
    mediaType: str = Field(description="Type of the media: 'movie' or 'series'."),
    title: str = Field(description="Title of the media."),
    video_path: str = Field(description="Path to the media file (only for movies)."),
    poster_path: str = Field(description="Path to the poster file."),
    description: Optional[str] = Field(description="Description of the media (optional)."),
    release_date: Optional[str] = Field(description="Release date (YYYY-MM-DD) of the media (optional)."),
    seasonsNumber: str = Field(description="Number of seasons (only for series).")
    ) -> dict:
    return await upload_media(mediaType=mediaType, title=title, video_path=video_path, poster_path=poster_path, description=description, release_date=release_date, seasonsNumber=seasonsNumber)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    },
    description = "Upload the processed episode file of a series to the website."
)
async def uploadEpisode(
    seriesTitle: str = Field(description="Title of the series."),
    seasonNumber: str = Field(description="Number of the season."),
    episodeNumber: str = Field(description="Number of the episode."),
    episodeTitle: Optional[str] = Field(description="Title of the episode. (preffered but optional)"),
    video_path: str = Field(description="Path to the episode file."),
    poster_path: Optional[str] = Field(description="Path to the poster file. (optional - usually not needed for episodes)"),
    description: Optional[str] = Field(description="Description of the episode (optional)."),
    release_date: Optional[str] = Field(description="Release date (YYYY-MM-DD) of the episode (optional).")
    ) -> dict:
    return await upload_episode(series_title=seriesTitle, season_number=seasonNumber, episode_number=episodeNumber, episode_title=episodeTitle, video_path=video_path, poster_path=poster_path, description=description, release_date=release_date)


@mcp.tool(
    annotations = {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    },
    description = "Upload a subtitle file to the website."
)
async def uploadSubtitle(
    subtitlePath: str = Field(description="Path to the subtitle file."),
    mediaTitle: str = Field(description="Title of the media the subtitle belongs to."),
    language: str = Field(description="Language of the subtitle (default is English - fill only if different with the language in its translation)."),
    seasonNumber: str = Field(description="Season number (only for series episodes)."),
    episodeNumber: str = Field(description="Episode number (only for series episodes).")
    ) -> dict:
    return await upload_subtitle(subtitle_path=subtitlePath, media_title=mediaTitle, language=language, season_number=seasonNumber, episode_number=episodeNumber)
