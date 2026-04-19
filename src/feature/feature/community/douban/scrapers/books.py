import re

from ..models.book import Book
from .base import BaseScraper, clean

_ITEMS_PER_PAGE = 15


def _parse_pub(text: str) -> dict:
    parts = [s.strip() for s in text.split(" / ")]
    author = parts[0] if len(parts) >= 1 else None
    translator = parts[1] if len(parts) >= 5 else None
    publisher = parts[2] if len(parts) >= 5 else (parts[1] if len(parts) >= 4 else None)
    pub_date = parts[3] if len(parts) >= 5 else (parts[2] if len(parts) >= 4 else None)
    price = parts[4] if len(parts) >= 5 else (parts[3] if len(parts) >= 4 else None)
    return {"author": author, "translator": translator, "publisher": publisher, "pub_date": pub_date, "price": price}


def _extract_country(author: str | None) -> tuple[str | None, str | None]:
    if not author:
        return None, None
    m = re.match(r"[\[【](.+?)[\]】]\s*(.*)", author)
    if m:
        return m.group(1), m.group(2).strip() or None
    return None, author


def _parse_date_status(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    m = re.search(r"(读过|在读|想读)", text)
    status = m.group(1) if m else None
    date = re.sub(r"\s*(读过|在读|想读)\s*", "", text).strip() or None
    return date, status


def _parse_rating(class_name: str | None) -> int | None:
    if not class_name:
        return None
    m = re.search(r"rating(\d)", class_name)
    return int(m.group(1)) if m else None


class BooksScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        start = (page_num - 1) * _ITEMS_PER_PAGE
        return f"https://book.douban.com/people/{self.user_id}/collect?start={start}"

    def _parse_page(self) -> list[Book]:
        elements = self.page.query_selector_all(".subject-item")
        books: list[Book] = []
        for el in elements:
            title_el = el.query_selector("h2 a")
            title = clean(title_el.text_content()) if title_el else None
            url = title_el.get_attribute("href") if title_el else None
            cover = (img.get_attribute("src") if (img := el.query_selector(".pic img")) else None)
            pub = _parse_pub(clean(el.query_selector(".pub").text_content()) or "") if el.query_selector(".pub") else {}
            country, author = _extract_country(pub.get("author"))
            rating_el = el.query_selector("[class*=rating]")
            rating_cls = rating_el.get_attribute("class") if rating_el else None
            date_text = el.query_selector(".date").text_content() if el.query_selector(".date") else None
            date, status = _parse_date_status(date_text)
            tags_el = el.query_selector(".tags")
            tags = clean(tags_el.text_content().replace("标签: ", "")) if tags_el else None
            comment_el = el.query_selector(".comment")
            comment = clean(comment_el.text_content()) if comment_el else None

            books.append(Book(
                title=title, url=url, cover=cover,
                author=author, country=country,
                translator=pub.get("translator"), publisher=pub.get("publisher"),
                pub_date=pub.get("pub_date"), price=pub.get("price"),
                rating=_parse_rating(rating_cls),
                date=date, status=status,
                tags=tags, comment=comment,
            ))
        return books
