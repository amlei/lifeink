# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeInk AI -- a personal data aggregator that scrapes book/movie data from Douban (and eventually WeRead, Flomo) and provides an AI chat interface. The project has two main subsystems: a legacy `requests`-based Notion syncer at the root, and a newer backend + frontend stack in `backend/` and `frontend/`.

## Development Commands

### Backend (FastAPI + Playwright scraper)

```bash
cd backend
uv sync
uv run python -m playwright install chromium   # first time only
uv run python __main__.py --type books --pages 3   # CLI scraper
uv run python __main__.py --type browser           # open interactive browser with saved session
uv run python src/api.py                           # start API server (port 8000)
uv run pytest tests/ -v -s                         # run tests
```

Valid `--type` values: `profile`, `books`, `movies`, `games`, `reviews`, `notes`, `browser`.

### Frontend (React + Vite + Bun)

```bash
cd frontend
bun install           # install dependencies
bun run dev           # start dev server (http://localhost:5173)
bun run build         # production build
bun run lint          # run ESLint
bun run preview       # preview production build
```

### One-command startup

```bash
./start.sh            # starts backend (uv) + frontend (bun run dev) concurrently
```

### Root project (legacy Notion sync)

```bash
pip install -r requirements.txt
python main.py              # Syncs books to Notion (incremental)
```

No test suite or linter for the root project.

## Architecture

### Backend (`backend/`)

Independent `uv`-managed project (Python >=3.12). Three layers:

**API layer** (`src/api.py`, `src/api/douban.py`):
- FastAPI app with CORS middleware. Started via `uvicorn` on port 8000.
- `POST /api/chat` -- streaming text response (mock LLM, character-by-character).
- `POST /api/community/bind` -- platform bind/unbind/status/refresh (query params: `action`, `platform`).
- `POST /api/community/sync` -- trigger data sync for a bound platform.
- `WS /api/community/ws` -- WebSocket push of binding/sync progress (QR code, status transitions, profile).
- `GET /api/community/data` -- retrieve books, movies, notes for a platform.
- `AsyncBindManager` (in `src/api/douban.py`) runs Playwright login in a thread pool, notifying the WebSocket via `asyncio.Event`.

**Scraper layer** (`src/community/`):
- `DoubanClient` (`src/community/douban/client.py`): context manager that uses Playwright for login (QR code) and `requests` for data scraping. Auto-detects `user_id` from `/mine/` redirect.
- `SessionManager` (`src/community/douban/session.py`): builds `requests.Session` from saved Playwright storage state cookies.
- `BaseScraper` (`src/community/douban/scrapers/base.py`): pagination base class. Subclasses implement `_url()` and `_parse_page()`.
- Each data type has a Pydantic model (`src/community/douban/models/`) and a scraper (`src/community/douban/scrapers/`): Book, Movie, Game, Review, Note, Profile.
- `weread/` and `flomo/` packages are stubs.
- Default browser channel is `msedge`.

**Database layer** (`db/`):
- SQLAlchemy async ORM over SQLite (`aiosqlite`). DB file: `backend/db/data/lifeink.db`.
- `engine.py`: async engine, session factory, `get_default_user()`, `init_db()`.
- `models.py`: ORM models -- `User`, `CommunityMeta` (platform binding + session state), `BookRow`, `MovieRow`, `GameRow`, `ReviewRow`, `NoteRow`. Each row model has a `to_api_dict()` method.
- `repository.py`: `CommunityMetaRepo` (binding/session CRUD) and `DataRepo` (upsert + get for each data type, using SQLite `ON CONFLICT DO UPDATE`).
- Auto-creates a default user (`amlei`) on `init_db()`.

### Frontend (`frontend/`)

Bun-managed React 19 + TypeScript + Vite.

- `App.tsx` renders `Sidebar`, `ChatPanel`/`WelcomeScreen`, and a right panel placeholder. `ProfileModal` for settings.
- `useChatStore` hook manages chat state (messages, history, active chat) with in-memory `Map` cache.
- `ChatPanel` uses `@ai-sdk/react`'s `useChat` hook with `TextStreamChatTransport` for streaming.
- `api/douban.ts` provides REST and WebSocket functions for platform binding and data access.
- `community/types/bind.ts` defines shared types: `BindStatus`, `PollResult`, `BookItem`, `MovieItem`, `NoteItem`, `CommunityData`.
- Vite dev server proxies `/api` (including WebSocket) to `http://localhost:8000`.
- UI is in Chinese.

### Root: Legacy Notion Sync Pipeline

`main.py` -> `function/spider.py` -> `function/glo.py`

1. `Glo` class (`function/glo.py`) loads all config from `.env` at import time via `python-dotenv`.
2. `Book` class (`function/spider.py`) scrapes Douban HTML with `requests` + BeautifulSoup. `Video` extends `Book`, overriding `title()`, `other()`, `cover_link()`.
3. `BookRun`/`VideoRun` (`main.py`) orchestrate: scrape -> create Notion page -> populate properties from JSON templates -> update page.
4. Incremental sync: reads last synced title from `last mark/new_{book,video}.txt`, stops when that title is encountered.

## Key Conventions

- All Notion property names in JSON templates and code are Chinese.
- The root scraper uses `requests`; the backend uses Playwright (for login) + `requests` (for scraping). They do not share code.
- `last mark/`, `.playwright/`, `.playwright-cli/`, `backend/db/data/`, and `tmp/` are gitignored (contain user-specific session data and databases).
- Strictly prohibited from using emojis in code or comments.
- All files created for temporary use shall be placed in the `tmp/` directory.
- Creating .sh and other script files is prohibited.

## Required Configuration

`.env` file at project root (gitignored):

- `TOKEN` -- Notion integration token
- `BOOK_DATABASE_ID`, `VIDEO_DATABASE_ID` -- Notion database IDs
- `COOKIE` -- Douban session cookie (root scraper only)
- `DOUBANID` -- Douban user ID
- `USER_AGENT`, `ACCEPT` -- HTTP headers for Douban requests
- `BOOK_ICON`, `VIDEO_ICON` -- icon URLs for Notion pages
- `STAR` -- character used to display ratings

## CI/CD

- `.github/workflows/pages.yml` -- deploys a GitHub Pages site
- `.github/workflows/auto-merge.yml` -- auto-merge for dependabot PRs
