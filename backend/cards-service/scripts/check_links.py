"""
Check which affiliate links in the database are reachable vs. broken.

Usage:
    cd backend/cards-service
    python scripts/check_links.py

Requires DATABASE_URL in .env (same as seed.py).
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://", "postgresql://"
)

PLACEHOLDER_PREFIX = "https://example.com"
TIMEOUT = 10  # seconds per request


async def check_url(client: httpx.AsyncClient, card_name: str, url: str) -> dict:
    if url.startswith(PLACEHOLDER_PREFIX):
        return {"card": card_name, "url": url, "status": "PLACEHOLDER", "code": None}
    try:
        r = await client.head(url, follow_redirects=True, timeout=TIMEOUT)
        ok = r.status_code < 400
        return {
            "card": card_name,
            "url": url,
            "status": "OK" if ok else "BROKEN",
            "code": r.status_code,
        }
    except Exception as exc:
        return {"card": card_name, "url": url, "status": "ERROR", "code": str(exc)}


async def main() -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT card_name, affiliate_link FROM cards ORDER BY card_name"
        )
    finally:
        await conn.close()

    print(f"Checking {len(rows)} affiliate links...\n")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [check_url(client, r["card_name"], r["affiliate_link"]) for r in rows]
        results = await asyncio.gather(*tasks)

    ok = [r for r in results if r["status"] == "OK"]
    broken = [r for r in results if r["status"] == "BROKEN"]
    placeholder = [r for r in results if r["status"] == "PLACEHOLDER"]
    error = [r for r in results if r["status"] == "ERROR"]

    def _print_group(label: str, items: list) -> None:
        if not items:
            return
        print(f"── {label} ({len(items)}) " + "─" * max(0, 50 - len(label)))
        for r in items:
            code = f"  [{r['code']}]" if r["code"] is not None else ""
            print(f"  {r['card']:<50}{code}")
            print(f"    {r['url']}")
        print()

    _print_group("PLACEHOLDER (example.com — definitely broken)", placeholder)
    _print_group("BROKEN (real URL but bad status)", broken)
    _print_group("ERROR (connection failed)", error)
    _print_group("OK", ok)

    print(
        f"Summary: {len(ok)} OK  |  {len(placeholder)} placeholder  "
        f"|  {len(broken)} broken  |  {len(error)} error"
    )


if __name__ == "__main__":
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    asyncio.run(main())
