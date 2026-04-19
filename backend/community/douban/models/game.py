from pydantic import BaseModel


class Game(BaseModel):
    title: str
    url: str
    cover: str | None = None
    desc: str | None = None
    rating: int | None = None
    date: str | None = None
    tags: str | None = None
    comment: str | None = None
