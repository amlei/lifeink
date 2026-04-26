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

Backend config (SMTP for email verification): copy `config-example.yaml` to `config.yaml` and fill in credentials.

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

Independent `uv`-managed project (Python >=3.12). Four layers:

**API layer** (`src/api.py`, `src/api/douban.py`):
- FastAPI app with `AuthMiddleware` + CORS. Started via `uvicorn` on port 8000.
- `POST /api/chat` -- streaming text response (mock LLM, character-by-character).
- `POST /api/community/bind` -- platform bind/unbind/status/refresh (query params: `action`, `platform`). Requires auth.
- `POST /api/community/sync` -- trigger data sync for a bound platform. Requires auth.
- `WS /api/community/ws?token=...` -- WebSocket push of binding/sync progress. Auth via query param.
- `GET /api/community/data` -- retrieve books, movies, notes for a platform. Requires auth.
- `AsyncBindManager` (in `src/api/douban.py`) runs Playwright login in a thread pool, notifying the WebSocket via `asyncio.Event`.

**Auth layer** (`src/core/`):
- JWT (HS256, 24h expiry) with bcrypt password hashing.
- `AuthMiddleware` (`src/core/middleware.py`): validates Bearer token on all routes except whitelist (`/api/auth/*`, `/api/chat`, `/docs`). Injects `User` into `request.state.user`.
- `AuthRepo` (`src/core/auth/repository.py`): user CRUD, verification code storage (6-digit, 10min expiry), soft delete.
- Auth routes (`src/core/auth/routes.py`): register -> email verification code -> verify+create account -> login returns JWT. Also `/me`, `/change-password`, `/delete`.
- Email via `src/core/utils/email.py` using SMTP config from `config.yaml` (presets for qq, outlook, 163, 126, yeah).
- `src/core/utils/config.py`: loads `config.yaml` (Pydantic model with `SmtpConfig`).

**Scraper layer** (`src/community/`):
- `DoubanClient` (`src/community/douban/client.py`): context manager that uses Playwright for login (QR code) and `requests` for data scraping. Auto-detects `user_id` from `/mine/` redirect.
- `SessionManager` (`src/community/douban/session.py`): builds `requests.Session` from saved Playwright storage state cookies.
- `BaseScraper` (`src/community/douban/scrapers/base.py`): pagination base class. Subclasses implement `_url()` and `_parse_page()`.
- Each data type has a Pydantic model (`src/community/douban/models/`) and a scraper (`src/community/douban/scrapers/`): Book, Movie, Game, Review, Note, Profile.
- `weread/` and `flomo/` packages are stubs.
- Default browser channel is `msedge`.

**Database layer** (`db/`):
- SQLAlchemy async ORM over SQLite (`aiosqlite`). DB file: `backend/db/data/lifeink.db`.
- `engine.py`: async engine, session factory, `init_db()`.
- `models.py`: ORM models -- `User` (email, password_hash, name, avatar, bio, status, email_verified), `VerificationCode`, `CommunityMeta` (platform binding + session state), `BookRow`, `MovieRow`, `GameRow`, `ReviewRow`, `NoteRow`. Row models have `to_api_dict()` and `to_pydantic()` methods.
- `repository.py`: `CommunityMetaRepo` (binding/session CRUD), `DataRepo` (upsert + get for each data type, using SQLite `ON CONFLICT DO UPDATE`), `AuthRepo` (user + verification code CRUD).
- All `user_id` foreign keys reference `users.id` with `CASCADE` delete.

### Frontend (`frontend/`)

Bun-managed React 19 + TypeScript + Vite.

- `App.tsx` wraps everything in `AuthProvider`. Renders `Sidebar`, `ChatPanel`/`WelcomeScreen`, and a right panel placeholder. `ProfileModal` for settings.
- `AuthContext` (`contexts/AuthContext.tsx`): global auth state with JWT token storage in localStorage, auto-logout on 401, `authedFetch()` wrapper.
- `AuthModal` (`components/AuthModal.tsx`): login + registration with email verification code flow and password strength indicator.
- `useChatStore` hook manages chat state (messages, history, active chat) with in-memory `Map` cache.
- `ChatPanel` uses `@ai-sdk/react`'s `useChat` hook with `TextStreamChatTransport` for streaming.
- `api/auth.ts` provides auth API calls; `api/douban.ts` provides REST and WebSocket functions for platform binding and data access.
- `types/douban.ts` defines shared types: `BindStatus`, `PollResult`, `BookItem`, `MovieItem`, `NoteItem`, `CommunityData`.
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
- `backend/config.yaml` is gitignored (contains SMTP credentials).
- Strictly prohibited from using emojis in code or comments.
- All files created for temporary use shall be placed in the `tmp/` directory.
- Creating .sh and other script files is prohibited.

## API Design Convention

All API endpoints use a **unified single-endpoint pattern**: one URL per domain, with an `action` field in the request body to distinguish operations. No separate URL paths per action.

**Pattern:**
```
POST /api/{domain}
Body: { "action": "<action-name>", ...params }
```

## Required Configuration

`.env` file at project root (gitignored, for legacy Notion sync only):

- `TOKEN` -- Notion integration token
- `BOOK_DATABASE_ID`, `VIDEO_DATABASE_ID` -- Notion database IDs
- `COOKIE` -- Douban session cookie (root scraper only)
- `DOUBANID` -- Douban user ID
- `USER_AGENT`, `ACCEPT` -- HTTP headers for Douban requests
- `BOOK_ICON`, `VIDEO_ICON` -- icon URLs for Notion pages
- `STAR` -- character used to display ratings

`backend/config.yaml` (gitignored, for auth email):

- `smtp.provider` -- preset name (`qq`, `outlook`, `163`, `126`, `yeah`, `custom`)
- `smtp.username`, `smtp.password` -- SMTP credentials

## CI/CD

- `.github/workflows/pages.yml` -- deploys a GitHub Pages site
- `.github/workflows/auto-merge.yml` -- auto-merge for dependabot PRs
