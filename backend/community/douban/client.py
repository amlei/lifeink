from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from .models.book import Book
from .models.game import Game
from .models.movie import Movie
from .models.note import Note
from .models.profile import Profile
from .models.review import Review
from .login import DoubanLogin
from .scrapers.books import BooksScraper
from .scrapers.games import GamesScraper
from .scrapers.movies import MoviesScraper
from .scrapers.notes import NotesScraper
from .scrapers.profile import ProfileScraper
from .scrapers.reviews import ReviewsScraper
from .session import SessionManager


class DoubanClient:
    """Playwright-based Douban data client.

    Usage::

        with DoubanClient(user_id="215871379") as client:
            profile = client.scrape_profile()
            books = client.scrape_books()
    """

    def __init__(
        self,
        user_id: str | None = None,
        headless: bool = True,
        state_path: Path | None = None,
        channel: str = "msedge",
    ):
        self._user_id = user_id
        self._headless = headless
        self._channel = channel
        self._session = SessionManager(state_path)
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def __enter__(self) -> "DoubanClient":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self._headless, channel=self._channel
        )
        storage_state = self._session.get_storage_state()
        self._context = self._browser.new_context(storage_state=storage_state)
        self._page = self._context.new_page()
        return self

    def __exit__(self, *exc) -> None:
        if self._context:
            self._session.save_state(self._context)
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    @property
    def page(self) -> Page:
        return self._page

    @property
    def user_id(self) -> str:
        return self._user_id

    def _ensure_user_id(self) -> None:
        """Auto-detect user_id by visiting /mine/ which redirects to /people/{id}/."""
        if self._user_id:
            return
        self._page.goto("https://www.douban.com/mine/")
        self._page.wait_for_load_state("domcontentloaded")
        import re
        m = re.search(r"/people/(\d+)", self._page.url)
        if not m:
            raise RuntimeError(f"Cannot extract user_id from URL: {self._page.url}")
        self._user_id = m.group(1)

    def ensure_ready(self, qr_output_dir: Path | None = None) -> None:
        """Ensure session is valid. Skip login if auth cookie is still valid."""
        if self._session.has_valid_session:
            self._ensure_user_id()
            return

        self._page.goto("https://www.douban.com/")
        self._page.wait_for_load_state("domcontentloaded")
        login = DoubanLogin(self._page, qr_output_dir)
        if login.is_logged_in(self._page):
            self._ensure_user_id()
            return
        qr_path = login.initiate_qr_login()
        print(f"Scan QR code: {qr_path}")
        ok = login.wait_for_login()
        if ok:
            self._ensure_user_id()
        else:
            raise RuntimeError("Login failed")

    def scrape_profile(self) -> Profile:
        return ProfileScraper(self._page, self._user_id).scrape()

    def scrape_books(self, max_pages: int = 1) -> list[Book]:
        return BooksScraper(self._page, self._user_id).scrape(max_pages)

    def scrape_movies(self, max_pages: int = 1) -> list[Movie]:
        return MoviesScraper(self._page, self._user_id).scrape(max_pages)

    def scrape_games(self, max_pages: int = 1) -> list[Game]:
        return GamesScraper(self._page, self._user_id).scrape(max_pages)

    def scrape_reviews(self, max_pages: int = 1) -> list[Review]:
        return ReviewsScraper(self._page, self._user_id).scrape(max_pages)

    def scrape_notes(self) -> list[Note]:
        return NotesScraper(self._page, self._user_id).scrape()
