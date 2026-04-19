import re

from ..models.movie import Movie
from .base import BaseScraper, clean
from .books import _parse_rating

_ITEMS_PER_PAGE = 15


class MoviesScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        start = (page_num - 1) * _ITEMS_PER_PAGE
        return f"https://movie.douban.com/people/{self.user_id}/collect?start={start}"

    def _parse_page(self) -> list[Movie]:
        elements = self.page.query_selector_all(".item")
        movies: list[Movie] = []
        for el in elements:
            title_el = el.query_selector(".title a")
            title = clean(title_el.text_content()).split("/")[0] if title_el else None
            url = title_el.get_attribute("href") if title_el else None
            cover = (img.get_attribute("src") if (img := el.query_selector(".pic img")) else None)
            intro_el = el.query_selector(".intro")
            intro_text = clean(intro_el.text_content()) if intro_el else None
            date_info = intro_text.split("/")[0].split("(")[0] if intro_text else None
            rating_el = el.query_selector("[class*=rating]")
            rating_cls = rating_el.get_attribute("class") if rating_el else None
            date_el = el.query_selector(".date")
            date = clean(date_el.text_content()) if date_el else None
            tags_el = el.query_selector(".tags")
            tags = tags_el.text_content().replace("标签: ", "").split() if tags_el else None
            comment_el = el.query_selector(".comment")
            comment = clean(comment_el.text_content()) if comment_el else None

            movies.append(Movie(
                title=title, url=url, cover=cover,
                release_date=date_info,
                rating=_parse_rating(rating_cls),
                watch_date=date, tags=tags, comment=comment,
            ))
        return movies
