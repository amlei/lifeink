from bs4 import BeautifulSoup

from ..models.profile import Profile
from .base import BaseScraper, clean


class ProfileScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        return f"https://www.douban.com/people/{self.user_id}/"

    def scrape(self, max_pages: int = 1) -> Profile:
        url = self._url(1)
        soup = self._fetch_soup(url)

        infobox = soup.select_one(".infobox")
        avatar = None
        bio = None
        if infobox:
            img = infobox.select_one("img")
            avatar = img.get("src") if img else None
            bio = clean(infobox.get_text())

        sig_el = soup.select_one("#edit_signature")
        signature = clean(sig_el.get_text()) if sig_el else None

        return Profile(user_id=self.user_id, avatar=avatar, bio=bio, signature=signature)
