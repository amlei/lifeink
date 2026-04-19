from pydantic import BaseModel


class Movie(BaseModel):
    title: str
    url: str
    cover: str | None = None
    date_info: str | None = None
    rating: int | None = None
    date: str | None = None
    tags: str | None = None
    comment: str | None = None
