import json
import time
from http.cookiejar import Cookie
from pathlib import Path

from playwright.sync_api import BrowserContext

import requests


_STATE_FILENAME = "douban-state.json"
_PLAYWRIGHT_DIR = ".playwright"
_AUTH_COOKIE = "dbcl2"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
)


def _resolve_project_root() -> Path:
    """Walk up from this file to find the project root (directory with .git/ or .playwright/)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir() or (parent / _PLAYWRIGHT_DIR).is_dir():
            return parent
    return current.parents[5]


class SessionManager:
    """Manages Douban Playwright session state (cookies + localStorage)."""

    def __init__(self, state_path: Path | None = None):
        if state_path is not None:
            self._state_path = state_path
        else:
            self._state_path = _resolve_project_root() / _PLAYWRIGHT_DIR / _STATE_FILENAME

    @property
    def state_path(self) -> Path:
        return self._state_path

    @property
    def has_valid_session(self) -> bool:
        """Check if state file exists and the auth cookie has not expired."""
        if not self._state_path.is_file() or self._state_path.stat().st_size == 0:
            return False
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        now = time.time()
        for cookie in data.get("cookies", []):
            if cookie.get("name") == _AUTH_COOKIE:
                expires = cookie.get("expires", -1)
                return expires > now
        return False

    def get_storage_state(self) -> str | None:
        """Return path string for browser.new_context(storage_state=...), or None."""
        if self._state_path.is_file() and self._state_path.stat().st_size > 0:
            return str(self._state_path)
        return None

    def save_state(self, context: BrowserContext) -> None:
        """Persist browser context state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(self._state_path))

    def build_http_session(self) -> requests.Session:
        """Build a requests.Session with cookies and headers from saved state."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        if not self._state_path.is_file():
            return session

        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return session

        for c in data.get("cookies", []):
            jar_cookie = Cookie(
                version=0,
                name=c["name"],
                value=c["value"],
                port=None,
                port_specified=False,
                domain=c.get("domain", ""),
                domain_specified=bool(c.get("domain")),
                domain_initial_dot=c.get("domain", "").startswith("."),
                path=c.get("path", "/"),
                path_specified=True,
                secure=c.get("secure", False),
                expires=int(c.get("expires", -1)),
                discard=False,
                comment=None,
                comment_url=None,
                rest={},
            )
            session.cookies.set_cookie(jar_cookie)

        return session
