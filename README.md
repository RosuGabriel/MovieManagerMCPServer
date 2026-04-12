# Movie Manager MCP Server

A **Model Context Protocol (MCP) server** for managing a movie and TV series collection. Automates sourcing media files, downloading subtitles, processing metadata, and uploading to a Redpanda media database.

## Features

- **Media Search & Sourcing**
  - Search for torrents on Filelist
  - Download posters from TMDB
  - Search and download subtitles from SubtitleCat
- **Torrent Management**
  - Download torrents via uTorrent integration
  - Track download progress
  - Extract media files

- **Media Processing**
  - Compress and convert videos to MP4
  - Process subtitles (sync, format conversion)
  - Organize and validate files

- **Upload & Publishing**
  - Upload movies and series to Redpanda media database
  - Add episodes with metadata
  - Upload and manage subtitle attributes (language, type)
  - Automatic subtitle format conversion (SRT → VTT)

## Requirements

- **Python 3.10+**
- **uTorrent (Windows) or utserver (Ubuntu/Linux)** (for torrent downloads)
- **FFmpeg** (for video compression)

## Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd MCPServer
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Environment

Copy `example.env` to `.env` and fill in your credentials:

```bash
cp example.env .env
```

Torrent client settings:

- Set `TORRENT_CLIENT=auto` to pick `utorrent` on Windows and `utserver` on Linux.
- Or force a client explicitly with `TORRENT_CLIENT=utorrent` or `TORRENT_CLIENT=utserver`.
- Set `UT_LOCATION` for Windows `utorrent` executable path or for Ubuntu/Linux `utserver` binary path.

### 5. Run the Server

```bash
python server.py
```

The server will start and listen for MCP tool calls.

## Available Tools

### Media Sourcing

- **`searchMedia`** - Search for torrents by title
- **`getTorrent`** - Download torrent file from search result
- **`downloadPoster`** - Fetch poster image from TMDB

### Subtitle Management

- **`searchSubtitles`** - Search for subtitles by title/episode
- **`downloadSubtitle`** - Download subtitle file from SubtitleCat

### Torrent & Download

- **`startUTorrent`** - Launch µTorrent client
- **`downloadTorrent`** - Extract media from torrent file
- **`checkTorrent`** - Check download progress

### Media Processing

- **`prepareMedia`** - Compress video and convert to MP4
- **`checkMediaPreparing`** - Check compression progress

### Upload & Publishing

- **`uploadMedia`** - Upload movie/series to Redpanda
- **`uploadEpisode`** - Add episode to series
- **`uploadSubtitle`** - Add subtitle attribute to media

### Utilities

- **`searchLocally`** - Find media files in download directory
- **`closeSession`** - Close persistent browser session
