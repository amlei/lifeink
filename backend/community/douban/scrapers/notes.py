from bs4 import BeautifulSoup

from ..models.note import Note
from .base import BaseScraper, clean


class NotesScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        return "https://www.douban.com/mine/notes"

    def _parse_page(self, soup: BeautifulSoup) -> list[Note]:
        elements = soup.select(".note-container")
        notes: list[Note] = []
        for el in elements:
            a = el.select_one("a")
            title = clean(a.get_text()).split("/")[0] if a else None
            url = a.get("href") if a else None
            notes.append(Note(title=title, url=url))
        return notes
