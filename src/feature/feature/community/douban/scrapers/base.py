from typing import TypeVar

from playwright.sync_api import Page

T = TypeVar("T")


class BaseScraper:
    """Base class for Douban scrapers with pagination support."""

    def __init__(self, page: Page, user_id: str):
        self._page = page
        self._user_id = user_id

    @property
    def page(self) -> Page:
        return self._page

    @property
    def user_id(self) -> str:
        return self._user_id

    def _url(self, page_num: int) -> str:
        raise NotImplementedError

    def _parse_page(self) -> list:
        raise NotImplementedError

    def _get_total_pages(self) -> int:
        """Read total pages from .paginator (last link number)."""
        paginator = self._page.query_selector(".paginator")
        if not paginator:
            return 1
        links = paginator.query_selector_all("a")
        if not links:
            return 1
        last_text = links[-1].inner_text().strip()
        try:
            return int(last_text)
        except ValueError:
            return 1

    def scrape(self, max_pages: int = 1) -> list:
        items: list = []
        for page_num in range(1, max_pages + 1):
            url = self._url(page_num)
            self._page.goto(url)
            self._page.wait_for_load_state("domcontentloaded")
            if page_num == 1:
                total_pages = self._get_total_pages()
                effective_max = min(max_pages, total_pages)
            items.extend(self._parse_page())
            if page_num >= effective_max:
                break
        return items
