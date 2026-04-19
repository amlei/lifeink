# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraper that syncs personal book and movie data from Douban (Chinese media database) to Notion databases. The application performs incremental updates by tracking the last synced item and only processing new content.

## Architecture

### Core Components

- **main.py**: Entry point containing `BookRun` and `VideoRun` classes that orchestrate the sync process
- **function/glo.py**: Global configuration and constants management (loads from .env)
- **function/spider.py**: Web scraping classes `Book` and `Video` for Douban data extraction
- **json/**: Template files defining Notion database property structures

### Data Flow

1. **Configuration**: Environment variables loaded via `python-dotenv` in `function/glo.py`
2. **Web Scraping**: `Book` and `Video` classes extract data from Douban user pages using BeautifulSoup
3. **Incremental Detection**: Compares scraped titles against last sync records in `last mark/` folder
4. **Notion Integration**: Creates and updates Notion pages using `notion-client` library with JSON templates
5. **Logging**: Comprehensive logging via `loguru` with daily rotation files

### Key Design Patterns

- **Inheritance**: `Video` extends `Book` class sharing common scraping logic
- **Template Method**: Database properties populated from JSON templates (`json/book.json`, `json/video.json`)
- **Rate Limiting**: Built-in delays between requests to avoid overwhelming Douban servers
- **Error Handling**: Graceful handling of missing data (dates, publishers) with fallbacks

## Development Commands

### Environment Setup
```bash
# Install dependencies (note: requirements.txt has encoding issues in current repo)
pip install -r requirements.txt

# Core dependencies that should be installed:
pip install python-dotenv notion-client beautifulsoup4 requests loguru
```

### Running the Application
```bash
# Sync books (default mode)
python main.py

# The application automatically handles both books and videos based on configuration
```

### Configuration Required

Before running, the following must be configured in `.env` file:

1. **Notion Integration**:
   - `TOKEN`: Notion API integration token
   - `BOOK_DATABASE_ID`: Notion database ID for books
   - `VIDEO_DATABASE_ID`: Notion database ID for videos

2. **Douban Authentication**:
   - `COOKIE`: Douban session cookie for accessing personal data
   - `DOUBANID`: User's Douban ID
   - `USER_AGENT`: Browser user agent string
   - `ACCEPT`: HTTP accept header

3. **Sync Configuration**:
   - `BOOK_ICON`: URL for book page icons
   - `VIDEO_ICON`: URL for video page icons
   - `STAR`: Character pattern for rating display

4. **State Tracking**:
   - Update `last mark/new_book.txt` with latest synced book title
   - Update `last mark/new_video.txt` with latest synced video title

## Important Notes

- The application processes 15 items per page (configurable via `Glo.MAXNum`)
- Incremental sync stops when encountering a title that matches the last sync record
- Logging files are created in `log/` directory with daily rotation
- The app includes 5-second delays between pages to respect rate limits
- JSON templates in `json/` folder define the Notion database schema - modify these to match your database structure
- The current `requirements.txt` has encoding issues and may need manual recreation
- Strictly prohibited from using emojis.
- All files created for temporary use shall be placed in the tmp/ directory.