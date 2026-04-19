# -*- coding: UTF-8 -*-
"""
@Project: Use-API
@File: spider.py
@Date ：2024/3/12 14:43
@Author：Amlei (lixiang.altr@qq.com)
@version：python 3.12
@IDE: PyCharm 2023.2
"""
import re
from time import sleep

import requests
from typing import Any, Tuple, List
from bs4 import BeautifulSoup
from function.glo import douban
from function.glo import Glo
from loguru import logger

class Book:
    def __init__(self, page: int = 0):
        self.url: str = douban(Glo.book, page)
        self.header: dict[str] = Glo.header
        self.MaxBook: int = Glo.MAXNum
        self.valid: bool = True
        self.lasted_book: str = ""
        self.request = None
        self.Titles: list[str | Any] = []
        self.Authors: list[str | Any] = []
        self.Tags: list[str | Any] = []
        self.Dates: list[str | Any] = []
        self.Comments: list[str | Any] = []
        self.CoverLinks: list[str | Any] = []
        self.Ratings: list[str | Any] = []

    def refresh(self) -> None:
        """
        清空栈堆
        :return: None
        """
        self.Titles: list[str | Any] = []
        self.Authors: list[str | Any] = []
        self.Tags: list[str | Any] = []
        self.Dates: list[str | Any] = []
        self.Comments: list[str | Any] = []
        self.CoverLinks: list[str | Any] = []
        self.Ratings: list[str | Any] = []
        logger.info("Clear Stacked.")

    def get(self) -> BeautifulSoup:
        sleep(3)
        logger.info(f"GET {self.url}")
        response = requests.get(self.url, headers=self.header)
        self.request: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        logger.info(f"GET {self.url} Succeed.")
        return self.request

    def title(self, last_book: str) -> list[str]:
        """
        以书名探测新增阅读数量
        :return: 书名
        """
        # Find all the a tags with a "title" attribute and print their text content
        count: int = 0
        logger.info(f"In title.")
        for i in self.request.find_all("a", {"title": True}):
            for span in i.find_all("span"):
                span.extract()
            if i.text.strip() == last_book:
                self.valid = False
                logger.warning(f"Current is invalid.")
                break
            else:
                self.Titles.append(i.text.strip())

                # 仅获取图书数目标题
                count += 1
                if count == self.MaxBook:
                    break
        logger.info(f"Title: {self.Titles}")
        return self.Titles

    def author(self):
        pattern = r"\[[^\]]*\]||（[.*]）"
        logger.info(f"Xpath Rules for Author: {pattern}")
        for div in self.request.find_all("div", {"class": "pub"}):
            text = div.text.strip().replace(" ", "").split("/")

            self.Authors.append([re.sub(pattern, "", text[0]), text[1:-1]])
            logger.info(f"Author: {[re.sub(pattern, "", text[0]), text[1:-1]]}")

        return self.Authors

    def other(self) -> tuple[list[str | Any], list[str | Any], list[str | Any]]:
        for item in self.request.find_all("li", class_="subject-item"):
            tag = item.find("span", {"class": "tags"})
            self.Tags.append(tag.text.split(" ")[1:] if tag else [])

            date = item.find("span", {"class": "date"})
            self.Dates.append(date.text.replace("\n      读过", "") if date else "")

            comment = item.find("p", {"class": "comment"})
            self.Comments.append(comment.text.strip() if comment else "")

        logger.info(f"Other Info: {self.Tags}, {self.Dates}, {self.Comments}")
        return self.Tags, self.Dates, self.Comments

    def cover_link(self) -> list[str]:
        for div in self.request.find_all("img", {"width": "90"}):
            self.CoverLinks.append(div.get("src"))
            logger.info(f"Cover Link: {div.get('src')}")

        return self.CoverLinks

    def rating(self) -> list[str]:
        # 使用正则表达式匹配class包含rating和数字的span标签
        pattern = re.compile(r'rating\d+-t')
        logger.info(f"Xpath Rules for Rating: rating\\d+-t")
        span_tags = self.request.find_all('span', {'class': pattern})

        # 取每个span标签的数字部分
        for span_tag in span_tags:
            rating_class = span_tag.get('class')
            rating = re.search(r'\d+', str(rating_class)).group()
            self.Ratings.append(rating)

        new_stack: list[str] = []
        for i in range(Glo.MAXNum):
            new_stack.append(Glo.star[:(int(self.Ratings.pop()) * 2)])
        new_stack.reverse()
        self.Ratings = new_stack

        return new_stack


class Video(Book):
    def __init__(self, page: int = None):
        super().__init__()
        self.url: str = douban(Glo.video, page)
        self.refresh()
        self.request = None
        self.Release: list[str] = []

    def title(self, last_video) -> list[str]:
        em_tags = self.request.find_all('em')

        for em in em_tags:
            title = em.text.split("/")[0].strip(" ")
            if title == last_video:
                self.valid = False
                break
            else:
                self.Titles.append(title)

        return self.Titles

    def other(self) -> tuple:
        # 上映日期
        self.Release = [i.text.strip().split("/")[0][0:10] for i in self.request.find_all("li", class_="intro")]

        for item in self.request.find_all("div", class_="item"):
            date = item.find('span', {'class': 'date'})
            self.Dates.append(date.text if date else "")

            tag = item.find('span', {'class': 'tags'})
            self.Tags.append(tag.text.strip("标签: ").split(" ") if tag else [])

        return self.Release, self.Dates, self.Tags

    def cover_link(self) -> list[str]:
        # 查找所有包含title属性的a标签
        a_tags = self.request.find_all('a', title=True)

        # 查找每个a标签内包含的img标签
        for a_tag in a_tags:
            img_tag = a_tag.find('img')
            if img_tag:
                self.CoverLinks.append(img_tag.get('src'))

        return self.CoverLinks


if __name__ == '__main__':
    # video = Video()
    # print(video.url)
    # video.title("安妮日记")
    # print(video.Titles)
    # print(video.other())

    book = Book()
    print(book.url)
    # book.title("埃隆·马斯克")

