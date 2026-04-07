"""Security helpers — URL validation, safe fetch, path guards."""
from __future__ import annotations

import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ALLOWED_SCHEMES = {"http", "https"}
_MAX_FETCH_BYTES = 52_428_800   # 50 MB hard cap for binary downloads
_MAX_TEXT_BYTES = 10_485_760    # 10 MB hard cap for HTML / text

_BLOCKED_HOSTS = {"metadata.google.internal", "metadata.google.com"}


def validate_url(url: str) -> str:
    """Raise ValueError if *url* is not http/https or targets a private IP.

    Blocks file://, ftp://, data:, SSRF to private ranges and cloud metadata.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"Blocked URL scheme '{parsed.scheme}' — only http and https are allowed. "
            f"Got: {url!r}"
        )

    hostname = parsed.hostname
    if hostname:
        if hostname.lower() in _BLOCKED_HOSTS:
            raise ValueError(f"Blocked cloud metadata endpoint '{hostname}'. Got: {url!r}")

        try:
            infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for info in infos:
                addr = info[4][0]
                ip = ipaddress.ip_address(addr)
                if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                    raise ValueError(
                        f"Blocked private/internal IP {addr} (resolved from '{hostname}'). "
                        f"Got: {url!r}"
                    )
        except socket.gaierror:
            pass  # DNS failure surfaces later during fetch

    return url


class _NoFileRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that re-validates every redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_NoFileRedirectHandler)


def safe_fetch(url: str, max_bytes: int = _MAX_FETCH_BYTES, timeout: int = 30) -> bytes:
    """Fetch *url* and return raw bytes with size cap and redirect validation."""
    validate_url(url)
    opener = _build_opener()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 oh-my-wiki/0.1"})

    with opener.open(req, timeout=timeout) as resp:
        status = getattr(resp, "status", None) or getattr(resp, "code", None)
        if status is not None and not (200 <= status < 300):
            raise urllib.error.HTTPError(url, status, f"HTTP {status}", {}, None)

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = resp.read(65_536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise OSError(
                    f"Response from {url!r} exceeds size limit "
                    f"({max_bytes // 1_048_576} MB). Aborting download."
                )
            chunks.append(chunk)

    return b"".join(chunks)


def safe_fetch_text(url: str, max_bytes: int = _MAX_TEXT_BYTES, timeout: int = 15) -> str:
    """Fetch *url* and return decoded text (UTF-8, replacing bad bytes)."""
    raw = safe_fetch(url, max_bytes=max_bytes, timeout=timeout)
    return raw.decode("utf-8", errors="replace")


def validate_wiki_path(path: str | Path, base: Path | None = None) -> Path:
    """Resolve *path* and verify it stays inside *base* (defaults to wiki/)."""
    if base is None:
        base = Path("wiki").resolve()

    base = base.resolve()
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise ValueError(
            f"Path {path!r} escapes the allowed directory {base}. "
            "Only paths inside wiki/ are permitted."
        )
    return resolved


_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_label(text: str, max_len: int = 256) -> str:
    """Strip control characters and cap length."""
    text = _CONTROL_CHAR_RE.sub("", text)
    if len(text) > max_len:
        text = text[:max_len]
    return text
