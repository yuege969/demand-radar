"""Shared HTTP client factory.

Normalizes proxy environment variables before passing to httpx.
The ALL_PROXY env var may use the unofficial 'socks://' scheme which httpx does
not support; we fall back to HTTP_PROXY / HTTPS_PROXY instead.
"""

from __future__ import annotations

import os

import httpx


def build_http_client(**kwargs) -> httpx.Client:
    """Return an httpx.Client with proxy settings derived from the environment.

    httpx raises ValueError on the unofficial ``socks://`` scheme that tools
    like clash/v2ray emit via ``ALL_PROXY``.  We skip ``ALL_PROXY`` and read
    only the well-formed ``HTTP_PROXY`` / ``HTTPS_PROXY`` variables.
    """
    proxy_url = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    if not proxy_url:
        from app.config import settings

        proxy_url = settings.HTTP_PROXY or None
    return httpx.Client(proxy=proxy_url, trust_env=False, **kwargs)
