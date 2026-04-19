from pathlib import Path

from playwright.sync_api import BrowserContext


_STATE_FILENAME = "douban-state.json"
_PLAYWRIGHT_DIR = ".playwright"


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
        return self._state_path.is_file() and self._state_path.stat().st_size > 0

    def get_storage_state(self) -> str | None:
        """Return path string for browser.new_context(storage_state=...), or None."""
        if self.has_valid_session:
            return str(self._state_path)
        return None

    def save_state(self, context: BrowserContext) -> None:
        """Persist browser context state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(self._state_path))
