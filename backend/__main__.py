import argparse
import asyncio
import json
import sys

from src.community.douban import DoubanClient
from db.engine import async_session_factory, get_default_user
from db.repository import CommunityMetaRepo

TYPES = ("profile", "books", "movies", "games", "reviews", "notes")


def main():
    parser = argparse.ArgumentParser(prog="backend", description="Community data scraper")
    parser.add_argument("--type", required=True, choices=TYPES, help="Data type to scrape")
    parser.add_argument("--pages", type=int, default=1, help="Max pages to scrape")
    args = parser.parse_args()

    state_json = _load_session_state()

    with DoubanClient(headless=False, state_json=state_json) as client:
        client.ensure_ready()
        print(f"Logged in as user: {client.user_id}")

        result = getattr(client, f"scrape_{args.type}")(max_pages=args.pages)
        if isinstance(result, list):
            print(json.dumps([r.model_dump() for r in result], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


def _load_session_state() -> str | None:
    async def _get():
        async with async_session_factory() as db:
            user = await get_default_user(db)
            state, _ = await CommunityMetaRepo.get_session_state(db, user.id, "douban")
            return state
    return asyncio.run(_get())


if __name__ == "__main__":
    main()
