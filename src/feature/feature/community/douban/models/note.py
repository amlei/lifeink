from pydantic import BaseModel


class Note(BaseModel):
    title: str
    url: str | None = None
