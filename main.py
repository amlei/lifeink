# -*- coding: UTF-8 -*-
"""
@Project: Python
@File: main.py
@Date: 2023/3/27 11:55
@Author: Amlei (lixiang.altr@qq.com)
@version: python 3.12
@IDE: PyCharm 2023.1
"""
import pprint

import json
import os
from datetime import datetime
from time import sleep, time
from dotenv import load_dotenv
from notion_client import Client
from function.glo import Glo
from function.spider import Book, Video
from loguru import logger

# 最新记录
newest_mark: str = ""
# 本次增量数
count: int = 0
path: str = "./last mark"


def option(op: int = 0) -> str:
    match op:
        case 0:
            return "book"
        case _:
            return "video"


def last_mark(op: int = 0) -> str:
    """
    上一次书影音标记
    :param op: 0: 书  1: 影视
    :return: None
    """
    with open(f"{path}/new_{option(op)}.txt", "r", encoding="utf-8") as f:
        return f.readlines().pop()


def new_mark(option: str) -> None:
    """
    最新标记
    :param op: 0: 书  1: 影视
    :return: None
    """
    global newest_mark

    with open(f"{path}/new_{option}.txt", "w", encoding="utf-8") as f:
        f.writelines(newest_mark)


class BookRun:
    def __init__(self, page: int = 0):
        """
        :param page: 以 15 为步长增加
        """
        load_dotenv()
        self.client = Client(auth=Glo.Token)
        self.page: int = page
        self.title: str = ""
        self.option: int = Glo.book
        self.classify = Book(page=page)
        self.valid: bool = self.classify.valid

    def create_page(self) -> int:
        """
        创建页面
        :return: 返回页面 ID
        """

        global newest_mark, count
        try:
            self.title: str = self.classify.Titles.pop(0)

            # 当前更新阅读的最后一本书则放入探测文件
            if self.page == 0:
                newest_mark = self.title
                self.page += 1

            match self.option:
                case Glo.book:
                    title = f"《{self.title}》"
                    database_id = Glo.Book_Databases_ID
                case _:
                    title = self.title
                    database_id = Glo.Video_Databases_ID

            new_page: dict = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
            created_page = self.client.pages.create(parent={"database_id": database_id}, properties=new_page)
            # 存储创建的页面 ID
            pageID = created_page['id']
            logger.info(f"《{self.title}》创建成功!")
            count += 1

            return pageID

        except IndexError:
            logger.info(f"增量更新完毕!, 本次共:{count}条数据")

            new_mark(option(self.option))
            exit()
            pass

    def print_all(self) -> None:
        """
        输出全部数据
        :return:
        """
        print(self.classify.Titles)
        print(self.classify.Authors)
        print(self.classify.Comments)
        print(self.classify.CoverLinks)
        print(self.classify.Ratings)
        print(self.classify.Tags)
        print(self.classify.Dates)
        print()

    def progress(self) -> dict:
        """
        参数处理
        :return: 返回页面参数
        """
        # 根据数据长度更新书籍类别
        category: list = []
        # 作者，同上原理
        author: list = []
        date: str = ""
        AuthorContent: list = self.classify.Authors.pop(0)

        match len(AuthorContent[1]):
            # ["化学工业出版社，[]]
            case 0:
                publishingCompany = AuthorContent[0]
            # 存在译者情况['弗朗西斯·苏（FrancisSu）', ['沈吉儿、韩潇潇', '中信出版集团', '2022-6-10', '69']]
            case 3:
                publishingCompany = AuthorContent[1][1]
            # 默认情况
            case _:
                publishingCompany = AuthorContent[1][0]
        try:
            publishingDate = AuthorContent[1][-1].split("-")
            # 忽略日期，且月份必须有两位数（剩下一位由0填充）
            date = "{}-{:0>2}-01".format(publishingDate[0], publishingDate[1])
        except IndexError:
            # 获取日期超过范围，说明该书没有出版日期信息
            today = datetime.now().strftime("%Y-%m-%d")
            logger.warning(f"捕获到{AuthorContent[0]}书籍出现出版日期错误，日期填充已更改为今日({today})请完成数据填充后自行更改")
            date = today

        # 作者
        for j in AuthorContent[0].split("、"):
            author.append(dict(name=j))

        # 书籍分类
        tags = self.classify.Tags.pop(0)
        for j in range(len(tags)):
            category.append(dict(name=tags[j]))

        with open("./json/book.json", "r", encoding="utf-8") as f:
            properties = json.load(f)

            properties["评分"]["select"]["name"] = self.classify.Ratings.pop(0)
            properties["出版社"]["select"]["name"] = str(publishingCompany).replace(",", " ")
            properties["读完时间"]["date"]["start"] = self.classify.Dates.pop(0)
            properties["出版日期"]["date"]["start"] = date
            properties["作者"]["multi_select"] = author
            properties["类别"]["multi_select"] = category
            properties["短评"]["rich_text"][0]["text"]["content"] = self.classify.Comments.pop(0)

        return properties

    def update(self, icon_url: str) -> None:
        """
        :param icon_url: 见 .env 文件
        :return: None
        """
        self.classify.get()
        self.classify.title(last_mark(self.option))
        self.classify.author()
        self.classify.other()
        self.classify.cover_link()
        self.classify.rating()
        # self.print_all()

        # 图标
        icon: dict = {
            "type": "external",
            "external": {
                "url": icon_url
            }
        }

        for i in range(Glo.MAXNum):
            properties: dict = self.progress()
            # 背景图
            cover = {
                "type": "external",
                "external": {
                    "url": self.classify.CoverLinks.pop(0)
                }
            }
            sleep(2)
            self.client.pages.update(page_id=self.create_page(), properties=properties, icon=icon, cover=cover)

class VideoRun(BookRun):
    def __init__(self, page: int = 0):
        super().__init__()
        self.page: int = page
        self.title: str = ""
        self.option: int = Glo.video
        self.classify = Video(page=page)

    def print_all(self) -> None:
        print(self.classify.Titles)
        print(self.classify.Ratings)
        print(self.classify.Release)
        print(self.classify.Dates)
        print(self.classify.Tags)

    def progress(self) -> dict:
        # 影片分类
        # 根据数据长度更新书籍类别
        category: list = []
        tags = self.classify.Tags.pop(0)
        for j in range(len(tags)):
            category.append(dict(name=tags[j]))

        with open("./json/video.json", "r", encoding="utf-8") as f:
            properties: dict = json.load(f)
            properties["评分"]["select"]["name"] = self.classify.Ratings.pop(0)
            properties["观影日期"]["date"]["start"] = self.classify.Dates.pop(0)
            properties["上映日期"]["date"]["start"] = self.classify.Release.pop(0)
            properties["类别"]["multi_select"] = category

        return properties


def main(option: int = 0, page: int = 0) -> None:
    """
    主函数
    :param option: 0-图书 1-影视
    :param page: 页数
    :return:
    """
    while True:
        if option == Glo.book:
            run = BookRun(page=page)
            # print(f"上一次【图书】标记:《{last_mark(Glo.book)}》")
            logger.info(f"last mark of 【book】:《{last_mark(Glo.book)}》")
            run.update(os.environ.get("BOOK_ICON"))

        else:
            run = VideoRun(page=page)
            # print(f"上一次影视标记:{last_mark(Glo.video)}")
            logger.info(f"Last mark of 【video】:{last_mark(Glo.video)}")
            run.update(os.environ.get("VIDEO_ICON"))

        page += 15
        # print("下一页, 等待5秒")
        logger.info("Please wait 5s to next page.")
        sleep(5)


if __name__ == '__main__':
    logger.add(f"./log/{datetime.now().strftime('%Y-%m-%d')}.log")
    logger.info("Start Application.")
    tic = time()
    main(0)
    toc = time()
    logger.info("End task.")
    logger.info(f"执行时间：{toc - tic}")