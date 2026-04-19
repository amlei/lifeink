from ..models.note import Note
from .base import BaseScraper, clean


class NotesScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        return "https://www.douban.com/mine/notes"

    def _parse_page(self) -> list[Note]:
        elements = self.page.query_selector_all(".note-container")
        notes: list[Note] = []
        for el in elements:
            a = el.query_selector("a")
            title = clean(a.text_content()) if a else None
            url = a.get_attribute("href") if a else None
            notes.append(Note(title=title, url=url))
        return notes
