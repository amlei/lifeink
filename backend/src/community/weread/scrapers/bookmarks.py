from __future__ import annotations

from playwright.sync_api import Page

from ..models.bookmark import Bookmark


def scrape_bookmarks(page: Page, book_id: str) -> list[Bookmark]:
    """Fetch bookmarks/notes for a book via /web/book/bookmarklist API."""
    data = page.evaluate(
        """async (bookId) => {
            const r = await fetch('/web/book/bookmarklist?bookId=' + bookId + '&synckey=0');
            if (!r.ok) return null;
            return await r.json();
        }""",
        book_id,
    )

    if not data:
        return []

    updated = data.get("updated")
    if not isinstance(updated, list):
        return []

    bookmarks: list[Bookmark] = []
    for item in updated:
        bm = _parse_bookmark(item)
        if bm:
            bookmarks.append(bm)

    return bookmarks


def scrape_all_bookmarks(page: Page, book_ids: list[str]) -> list[Bookmark]:
    """Fetch bookmarks for multiple books."""
    all_bookmarks: list[Bookmark] = []
    for book_id in book_ids:
        bms = scrape_bookmarks(page, book_id)
        all_bookmarks.extend(bms)
    return all_bookmarks


def _parse_bookmark(item: dict) -> Bookmark | None:
    """Parse a bookmark dict into Bookmark model."""
    book_id = item.get("bookId")
    mark_text = item.get("markText")
    if not book_id or not mark_text:
        return None

    return Bookmark(
        book_id=str(book_id),
        book_title=item.get("chapterName"),
        mark_text=mark_text,
        chapter_name=item.get("chapterName"),
        chapter_idx=item.get("chapterIdx"),
        style=item.get("style"),
        create_time=item.get("createTime"),
        bookmark_id=item.get("bookmarkId"),
    )
