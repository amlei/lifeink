from ..models.profile import Profile
from .base import BaseScraper


class ProfileScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        return f"https://www.douban.com/people/{self.user_id}/"

    def scrape(self, max_pages: int = 1) -> Profile:
        url = self._url(1)
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

        infobox = self.page.query_selector(".infobox")
        avatar = None
        bio = None
        if infobox:
            img = infobox.query_selector("img")
            avatar = img.get_attribute("src") if img else None
            bio = infobox.text_content().strip()

        sig_el = self.page.query_selector("#edit_signature")
        signature = sig_el.text_content().strip() if sig_el else None

        return Profile(user_id=self.user_id, avatar=avatar, bio=bio, signature=signature)
