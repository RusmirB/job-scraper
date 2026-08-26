"""Every source module exposes fetch(...) -> list[Job] and never raises;
on failure it logs and returns []."""
from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

import requests

HEADERS = {"User-Agent": "qa-job-scanner/1.0 (personal job search)"}

# (connect, read). NOTE: requests' read timeout is the gap *between* chunks, not a
# ceiling on the whole download -- a server that trickles bytes forever never trips
# it. MAX_SECONDS / MAX_BYTES below are the actual ceilings.
TIMEOUT = (10, 20)
MAX_SECONDS = 60      # wall-clock budget for one response body
MAX_BYTES = 32_000_000  # Lever boards are ~11 MB uncompressed; leave headroom

# Transient upstream hiccups (Adzuna 503s under load, Lever stalls). Retrying costs
# a couple of seconds and recovers the query instead of losing it for the whole run.
RETRY_STATUS = {429, 500, 502, 503, 504}
RETRIES = 2
BACKOFF = 2.0  # seconds; doubled each attempt

# requests puts the full request URL in its exception text, which would print API
# keys straight into the terminal and any log you paste around.
_SECRET_QS = re.compile(r"(?i)\b(app_id|app_key|api_key|apikey|key|token|secret)=[^&\s]+")

T = TypeVar("T")
R = TypeVar("R")


class ResponseTooSlow(Exception):
    """A source exceeded its byte or time budget; treated like any fetch failure."""


class _Transient(Exception):
    """Retryable upstream status (429/5xx). Never escapes get()."""


def scrub(text: str) -> str:
    """Mask credentials in a URL or error message before it's printed."""
    return _SECRET_QS.sub(lambda m: f"{m.group(1)}=***", text)


def _read_body(resp: requests.Response, max_seconds: float, max_bytes: int) -> bytes:
    deadline = time.monotonic() + max_seconds
    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(65536):
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ResponseTooSlow(f"{scrub(resp.url)}: body exceeded {max_bytes / 1e6:.0f} MB")
        if time.monotonic() > deadline:
            raise ResponseTooSlow(
                f"{scrub(resp.url)}: still downloading after "
                f"{max_seconds:.0f}s ({total / 1e6:.1f} MB)"
            )
    return b"".join(chunks)


def get(
    url: str,
    *,
    max_seconds: float = MAX_SECONDS,
    max_bytes: int = MAX_BYTES,
    retries: int = RETRIES,
    **kwargs,
):
    """GET with a hard ceiling on body size and total download time, plus retries
    on transient upstream errors.

    Returns the response with .content/.text/.json() fully populated, exactly like a
    normal requests.get, but a stalled or unbounded source raises instead of hanging
    the whole run, and error messages never carry credentials.
    """
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", TIMEOUT)
    kwargs["stream"] = True

    for attempt in range(retries + 1):
        last = attempt == retries
        try:
            resp = requests.get(url, **kwargs)
            try:
                # A 4xx is a permanent answer (dead slug, bad key) -- never retry it.
                # Only RETRY_STATUS and transport errors get another attempt.
                if resp.status_code in RETRY_STATUS and not last:
                    raise _Transient(f"{resp.status_code} {resp.reason} for {scrub(url)}")
                resp.raise_for_status()
                # Body budget failures are NOT retried: re-downloading a multi-MB
                # response that already blew its budget just burns the budget again.
                body = _read_body(resp, max_seconds, max_bytes)
            finally:
                resp.close()
        except (_Transient, requests.ConnectionError, requests.Timeout) as exc:
            if last:
                raise requests.RequestException(scrub(str(exc))) from None
            time.sleep(BACKOFF * (2**attempt))
            continue
        except requests.RequestException as exc:  # 4xx and anything else: give up now
            raise requests.RequestException(scrub(str(exc))) from None
        # Hand back a normal, non-streaming response object.
        resp._content = body
        resp._content_consumed = True
        resp.raw = None
        return resp


def parallel(fn: Callable[[T], list[R]], items: Iterable[T], workers: int = 8) -> list[R]:
    """Map fn over items concurrently (I/O-bound); flatten the resulting lists."""
    items = list(items)
    if not items:
        return []
    out: list[R] = []
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as pool:
        for result in pool.map(fn, items):
            out.extend(result)
    return out
