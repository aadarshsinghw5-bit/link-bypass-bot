from urllib.parse import urlparse

import aiohttp


class SafeRedirectResolver:
    """Resolve ordinary HTTP redirects only."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def resolve(self, url: str) -> str:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS URLs are supported.")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
            )
        }

        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=headers,
        ) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}")
                return str(response.url)
