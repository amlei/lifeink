import re

from ..models.review import Review
from .base import BaseScraper, clean

_ITEMS_PER_PAGE = 10


class ReviewsScraper(BaseScraper):

    def _url(self, page_num: int) -> str:
        start = (page_num - 1) * _ITEMS_PER_PAGE
        return f"https://www.douban.com/people/{self.user_id}/reviews?start={start}"

    def _parse_page(self) -> list[Review]:
        elements = self.page.query_selector_all(".review-item")
        reviews: list[Review] = []
        for el in elements:
            subject_img = el.query_selector(".subject-img img")
            subject_title = subject_img.get_attribute("title") if subject_img else None
            subject_a = el.query_selector(".subject-img")
            subject_url = subject_a.get_attribute("href") if subject_a else None
            subject_img_url = subject_img.get_attribute("src") if subject_img else None
            h2a = el.query_selector("h2 a")
            review_title = clean(h2a.text_content()) if h2a else None
            review_url = h2a.get_attribute("href") if h2a else None
            all_text = el.text_content() or ""
            m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", all_text)
            date = m.group(1) if m else None

            reviews.append(Review(
                subject_title=subject_title,
                subject_url=subject_url,
                subject_img_url=subject_img_url,
                review_title=review_title,
                review_url=review_url,
                date=date,
            ))
        return reviews
