"""Small client for the Couchside HTTP API (/api/v1)."""

from __future__ import annotations

from typing import Any

import aiohttp


class CouchsideError(Exception):
    """Couchside could not be reached or gave an unexpected answer."""


class CouchsideAuthError(CouchsideError):
    """The sign-in was refused or the saved session has ended."""


class CouchsideNotAdminError(CouchsideError):
    """The account is not a Couchside administrator."""


class CouchsideOutsideNetworkError(CouchsideError):
    """Couchside only answers its local network and Home Assistant is not on it."""


class CouchsideClient:
    """Talks to one Couchside server."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str | None = None,
    ) -> None:
        self._session = session
        self._base = f"{base_url(host, port)}/api/v1"
        self.token = token

    async def login(self, username: str, password: str) -> str:
        """Signs in as an administrator and returns the session token."""
        data = await self._request(
            "post", "/auth/login", json={"username": username, "password": password}
        )
        self.token = data["token"]
        if not data.get("user", {}).get("is_admin", False):
            raise CouchsideNotAdminError
        return self.token

    async def activity(self) -> dict[str, Any]:
        """Library totals and what is playing now."""
        return await self._request("get", "/activity")

    async def item_image(self, item_id: int, kind: str) -> tuple[bytes, str] | None:
        """`poster` or `backdrop` art of an item and its content type; None if it has none."""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            async with self._session.get(
                f"{self._base}/items/{item_id}/image/{kind}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 404:
                    return None
                if resp.status == 401:
                    raise CouchsideAuthError
                if resp.status >= 400:
                    raise CouchsideError(f"Couchside answered {resp.status}")
                return await resp.read(), resp.content_type or "image/jpeg"
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CouchsideError(str(err)) from err

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            async with self._session.request(
                method,
                self._base + path,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
                **kwargs,
            ) as resp:
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise CouchsideError(str(err)) from err
        if resp.status == 401:
            raise CouchsideAuthError
        if resp.status == 403:
            if isinstance(body, dict) and body.get("error") == "outside_local_network":
                raise CouchsideOutsideNetworkError
            raise CouchsideNotAdminError
        if resp.status >= 400 or not isinstance(body, dict):
            raise CouchsideError(f"Couchside answered {resp.status}")
        return body


def base_url(host: str, port: int) -> str:
    """`http://host:port`, with IPv6 addresses in brackets."""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{port}"
