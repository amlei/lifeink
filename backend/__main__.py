import argparse
import json
import sys

from community.douban import DoubanClient

TYPES = ("profile", "books", "movies", "games", "reviews", "notes")


def main():
    parser = argparse.ArgumentParser(prog="backend", description="Community data scraper")
    parser.add_argument("--type", required=True, choices=TYPES, help="Data type to scrape")
    parser.add_argument("--pages", type=int, default=1, help="Max pages to scrape")
    args = parser.parse_args()

    with DoubanClient(headless=False) as client:
        client.ensure_ready()
        print(f"Logged in as user: {client.user_id}")

        result = getattr(client, f"scrape_{args.type}")(max_pages=args.pages)
        if isinstance(result, list):
            print(json.dumps([r.model_dump() for r in result], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
