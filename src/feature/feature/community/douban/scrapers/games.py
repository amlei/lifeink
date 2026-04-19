import re

from ..models.game import Game
from .base import BaseScraper, clean


def _parse_game_rating(class_name: str | None) -> int | None:
    if not class_name:
        return None
    m = re.search(r"allstar(\d)0", class_name)
    return int(m.group(1)) if m else None


class GamesScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        return f"https://www.douban.com/people/{self.user_id}/games?action=collect"

    def _parse_page(self) -> list[Game]:
        elements = self.page.query_selector_all(".common-item")
        games: list[Game] = []
        for el in elements:
            title_el = el.query_selector(".title a")
            title = clean(title_el.text_content()) if title_el else None
            url = title_el.get_attribute("href") if title_el else None
            cover = (img.get_attribute("src") if (img := el.query_selector(".pic img")) else None)
            desc_el = el.query_selector(".desc")
            desc = clean(desc_el.text_content()) if desc_el else None
            rating_el = el.query_selector(".rating-star")
            rating_cls = rating_el.get_attribute("class") if rating_el else None
            date_el = el.query_selector(".date")
            date = clean(date_el.text_content()) if date_el else None
            tags_el = el.query_selector(".tags")
            tags = clean(tags_el.text_content().replace("标签: ", "")) if tags_el else None
            comment = self._extract_game_comment(el)

            games.append(Game(
                title=title, url=url, cover=cover,
                desc=desc, rating=_parse_game_rating(rating_cls),
                date=date, tags=tags, comment=comment,
            ))
        return games

    @staticmethod
    def _extract_game_comment(el) -> str | None:
        content = el.query_selector(".content")
        if not content:
            return None
        for child in content.query_selector_all(":scope > div"):
            cls = child.get_attribute("class") or ""
            if "title" not in cls and "desc" not in cls and "user-operation" not in cls:
                text = child.text_content().strip()
                if text:
                    return text
        return None
