from pydantic import BaseModel


class Profile(BaseModel):
    user_id: str
    avatar: str | None = None
    signature: str | None = None
    bio: str | None = None
