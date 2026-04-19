# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeInk AI -- a personal data aggregator that scrapes book/movie data from Douban and syncs it to Notion. The project has two generations of code: the original `requests`-based Notion syncer (`main.py`), and a newer Playwright-based scraper module (`src/feature/`).

## Development Commands

### Root project (Notion sync)

```bash
pip install -r requirements.txt
python main.py              # Syncs books to Notion (incremental)
```

No test suite exists. No linter is configured.

### Feature module (Playwright scraper)

```bash
cd src/feature
uv sync
uv run python -m playwright install chromium   # first time only
uv run python -m feature --type books --pages 3
```

Valid `--type` values: `profile`, `books`, `movies`, `games`, `reviews`, `notes`.

## Architecture

### Root: Notion Sync Pipeline

`main.py` -> `function/spider.py` -> `function/glo.py`

1. `Glo` class (`function/glo.py`) loads all config from `.env` at import time via `python-dotenv`.
2. `Book` class (`function/spider.py`) scrapes Douban HTML with `requests` + BeautifulSoup. `Video` extends `Book`, overriding `title()`, `other()`, `cover_link()`.
3. `BookRun`/`VideoRun` (`main.py`) orchestrate: scrape -> create Notion page -> populate properties from JSON templates -> update page.
4. Incremental sync: reads last synced title from `last mark/new_{book,video}.txt`, stops when that title is encountered.
5. JSON templates in `json/` define Notion property schemas -- property names are in Chinese (e.g., "评分", "作者", "类别").
6. `BookRun.update()` processes up to `Glo.MAXNum` (15) items per page with 2-second delays between Notion API calls and 5-second delays between Douban page fetches.

### src/feature/: Playwright Scraper Module

Independent `uv`-managed project with its own `pyproject.toml` and `.venv`.

- `DoubanClient` (`client.py`): context manager wrapping Playwright browser lifecycle. Auto-detects `user_id` from `/mine/` redirect. Handles QR login when session expires.
- `SessionManager` (`session.py`): persists browser storage state to `.playwright/douban-state.json`.
- `BaseScraper` (`scrapers/base.py`): pagination base class. Subclasses implement `_url()` and `_parse_page()`. Uses `clean()` helper to strip whitespace.
- Each data type has a Pydantic model (`models/`) and a scraper (`scrapers/`). Models: `Book`, `Movie`, `Game`, `Review`, `Note`, `Profile`.
- `weread/` and `flomo/` packages are stubs (not yet implemented).
- Default browser channel is `msedge`.

### Key conventions

- All Notion property names in JSON templates and code are Chinese.
- The root scraper uses `requests`; the feature module uses Playwright. They do not share code.
- `last mark/` directory and `.playwright/` are gitignored (contain user-specific session data).
- Strictly prohibited from using emojis.
- All files created for temporary use shall be placed in the `tmp/` directory.

## Required Configuration

`.env` file at project root (gitignored):

- `TOKEN` -- Notion integration token
- `BOOK_DATABASE_ID`, `VIDEO_DATABASE_ID` -- Notion database IDs
- `COOKIE` -- Douban session cookie (root scraper only)
- `DOUBANID` -- Douban user ID
- `USER_AGENT`, `ACCEPT` -- HTTP headers for Douban requests
- `BOOK_ICON`, `VIDEO_ICON` -- icon URLs for Notion pages
- `STAR` -- character used to display ratings (e.g., a star symbol repeated for rating level)

## CI/CD

- `.github/workflows/pages.yml` -- deploys a GitHub Pages site
- `.github/workflows/auto-merge.yml` -- auto-merge for dependabot PRs
