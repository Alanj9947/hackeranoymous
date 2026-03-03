"""
Simple health ping to a custom AI server (e.g., Ollama VPS).
Usage:
    python -m app.scripts.ping_custom_server --endpoint https://your-vps:8000 --api-key YOUR_KEY --timeout 10
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ping a custom AI server health endpoint")
    parser.add_argument("--endpoint", required=True, help="Base URL of the custom server (no trailing slash)")
    parser.add_argument("--api-key", required=False, default=None, help="Bearer token for the custom server")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    return parser.parse_args()


async def ping(endpoint: str, api_key: Optional[str], timeout: float) -> int:
    url = endpoint.rstrip("/") + "/health"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
        resp = await client.get(url, headers=headers)
    print(f"GET {url} -> {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text[:400])
    return resp.status_code


def main() -> int:
    args = parse_args()
    try:
        status = asyncio.run(ping(args.endpoint, args.api_key, args.timeout))
        return 0 if status == 200 else 1
    except httpx.RequestError as e:
        print(f"Request error: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
