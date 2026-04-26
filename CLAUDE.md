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

### Backend module (Playwright scraper)

```bash
cd backend
uv sync
uv run python -m playwright install chromium   # first time only
uv run python __main__.py --type books --pages 3
```

Valid `--type` values: `profile`, `books`, `movies`, `games`, `reviews`, `notes`.

### Frontend (React + Vite + Bun)

```bash
cd frontend
bun install           # install dependencies
bun run dev           # start dev server (http://localhost:5173)
bun run build         # production build
bun run lint          # run ESLint
bun run preview       # preview production build
```

Uses Bun as the runtime and package manager. Vite handles building and dev server.

### One-command startup

```bash
./start.sh            # starts backend (uv) + frontend (bun) concurrently
```

## Architecture

### Root: Notion Sync Pipeline

`main.py` -> `function/spider.py` -> `function/glo.py`

1. `Glo` class (`function/glo.py`) loads all config from `.env` at import time via `python-dotenv`.
2. `Book` class (`function/spider.py`) scrapes Douban HTML with `requests` + BeautifulSoup. `Video` extends `Book`, overriding `title()`, `other()`, `cover_link()`.
3. `BookRun`/`VideoRun` (`main.py`) orchestrate: scrape -> create Notion page -> populate properties from JSON templates -> update page.
4. Incremental sync: reads last synced title from `last mark/new_{book,video}.txt`, stops when that title is encountered.
5. JSON templates in `json/` define Notion property schemas -- property names are in Chinese (e.g., "评分", "作者", "类别").
6. `BookRun.update()` processes up to `Glo.MAXNum` (15) items per page with 2-second delays between Notion API calls and 5-second delays between Douban page fetches.

### backend/: Playwright Scraper Module

Independent `uv`-managed project with its own `pyproject.toml` and `.venv`.

- `DoubanClient` (`community/douban/client.py`): context manager wrapping Playwright browser lifecycle. Auto-detects `user_id` from `/mine/` redirect. Handles QR login when session expires.
- `SessionManager` (`community/douban/session.py`): persists browser storage state to `.playwright/douban-state.json`.
- `BaseScraper` (`community/douban/scrapers/base.py`): pagination base class. Subclasses implement `_url()` and `_parse_page()`. Uses `clean()` helper to strip whitespace.
- Each data type has a Pydantic model (`community/douban/models/`) and a scraper (`community/douban/scrapers/`). Models: `Book`, `Movie`, `Game`, `Review`, `Note`, `Profile`.
- `weread/` and `flomo/` packages under `community/` are stubs (not yet implemented).
- Default browser channel is `msedge`.

### Key conventions

- All Notion property names in JSON templates and code are Chinese.
- The root scraper uses `requests`; the backend module uses Playwright. They do not share code.
- `last mark/` directory and `.playwright/` are gitignored (contain user-specific session data).
- Strictly prohibited from using emojis.
- All files created for temporary use shall be placed in the `tmp/` directory.

### frontend/: React Chat Interface

Bun-managed project with Vite as the build tool.

- React 19 + TypeScript, using Vercel AI SDK (`ai`, `@ai-sdk/react`) for streaming chat.
- `App.tsx` renders `Sidebar`, `ChatPanel`, and `WelcomeScreen`.
- `useChatStore` hook manages chat state (messages, history, active chat).
- Vite dev server proxies `/api` requests to backend at `http://localhost:8000`.
- `start.sh` launches both backend (uv) and frontend (bun run dev) concurrently.

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

## Important principles
Creating .sh and other script files is prohibited.