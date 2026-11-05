"""URL safety helpers (prevent open redirects)."""

from urllib.parse import urljoin, urlparse

from flask import request


def is_safe_url(target: str | None) -> bool:
    if not target:
        return False
    host_url = urlparse(request.host_url)
    target_url = urlparse(urljoin(request.host_url, target))
    return target_url.scheme in {"http", "https"} and host_url.netloc == target_url.netloc
