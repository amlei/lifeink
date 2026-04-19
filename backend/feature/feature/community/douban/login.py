from pathlib import Path

from playwright.sync_api import Page

from .session import _resolve_project_root

_LOGIN_URL = "https://accounts.douban.com/passport/login"


class DoubanLogin:
    """Handles QR code login flow for Douban."""

    def __init__(self, page: Page, qr_output_dir: Path | None = None):
        self._page = page
        self._qr_output_dir = qr_output_dir or _resolve_project_root() / "tmp"

    def initiate_qr_login(self) -> Path:
        """Navigate to login, switch to QR mode, screenshot QR code."""
        self._page.goto(_LOGIN_URL)
        self._page.wait_for_load_state("domcontentloaded")

        # Switch to QR code mode
        self._page.click(".quick.icon-switch")
        qr_img = self._page.wait_for_selector('img[alt="QR Code"]')

        # Wait for the QR image to fully load before screenshot
        qr_img.wait_for_element_state("stable")
        self._page.wait_for_function(
            "el => el.complete && el.naturalHeight > 0",
            arg=qr_img,
        )

        # Screenshot the QR code
        self._qr_output_dir.mkdir(parents=True, exist_ok=True)
        qr_path = self._qr_output_dir / "douban-login-qr.png"
        qr_img.screenshot(path=str(qr_path))
        return qr_path

    def wait_for_login(self, timeout: float = 120.0) -> bool:
        """Wait for user to scan QR and complete login."""
        try:
            self._page.wait_for_url("https://www.douban.com/**", timeout=timeout * 1000)
            return True
        except Exception:
            return False

    def is_logged_in(self, page: Page) -> bool:
        """Check if the page shows authenticated state."""
        return bool(page.query_selector('a[href*="/mine/"]'))
