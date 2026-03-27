"""
Low-level HTTP client for FortiSIEM upstream.

Handles:
- Basic Auth (org/user:password)
- XML and JSON response detection
- Retry on 429 / 503
- XML error code 255 detection
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from typing import Any, Dict, Optional

import httpx
import xmltodict

from app.core.config import Settings
from app.core.exceptions import (
    FortiSIEMError,
    QueryStillInProgressError,
    UpstreamSSLError,
    UpstreamTimeoutError,
)

logger = logging.getLogger("fsmapi.client")

_ERROR_MESSAGES: Dict[int, str] = {
    400: "The parameters are invalid.",
    401: "Invalid credentials or request not authorized",
    403: "Access Denied",
    404: "The requested resource was not found",
    422: "Parameters are missing in query/request body.",
    423: "The parameters are invalid in path/query/request body.",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


class FortiSIEMClient:
    """Async HTTP client wrapping FortiSIEM REST endpoints."""

    def __init__(self, settings: Settings):
        base_url = settings.fortisiem_base_url.rstrip("/")
        if not base_url.startswith(("https://", "http://")):
            base_url = f"https://{base_url}"
        self.base_url = base_url
        self._auth_header = self._build_auth_header(settings)
        self._verify_ssl = settings.fortisiem_verify_ssl
        self._max_retries = settings.max_retries
        self._wait_time = settings.wait_time
        self._poll_interval = settings.query_poll_interval_seconds
        self._max_iterations = settings.query_max_iterations

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def _build_auth_header(self, settings: Settings) -> str:
        credential = f"{settings.upstream_username}:{settings.fortisiem_password}"
        encoded = base64.b64encode(credential.encode()).decode()
        return f"Basic {encoded}"

    def _default_headers(self) -> Dict[str, str]:
        return {"Authorization": self._auth_header}

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_body: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Issue an HTTP request to FortiSIEM.

        Returns parsed JSON, parsed XML-as-dict, or raw string depending on
        the response Content-Type.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._default_headers()
        if extra_headers:
            headers.update(extra_headers)

        try:
            async with httpx.AsyncClient(verify=self._verify_ssl) as client:
                logger.debug("%s %s params=%s", method, url, params)
                raw_data: Optional[bytes] = None
                if isinstance(data, str):
                    raw_data = data.encode("utf-8")
                elif isinstance(data, bytes):
                    raw_data = data

                resp = await client.request(
                    method,
                    url,
                    params=params,
                    content=raw_data,
                    json=json_body,
                    headers=headers,
                    timeout=60.0,
                )
        except httpx.ConnectTimeout:
            raise UpstreamTimeoutError()
        except httpx.SSLError as exc:
            raise UpstreamSSLError(str(exc))
        except httpx.ConnectError as exc:
            raise FortiSIEMError(f"Connection error: {exc}", status_code=502)

        return self._handle_response(resp)

    def _handle_response(self, resp: httpx.Response) -> Any:
        body = resp.content.decode("utf-8", errors="replace")
        logger.debug("status=%d body=%s", resp.status_code, body[:300])

        # FortiSIEM XML error code 255 – arrives as HTTP 200
        if 'error code="255"' in body:
            parsed = xmltodict.parse(body)
            desc = (
                parsed.get("response", {}).get("error", {}).get("description")
                or parsed.get("response", {}).get("result", {}).get("error", {}).get("description")
                or "FortiSIEM error code 255"
            )
            raise FortiSIEMError(desc, status_code=502)

        if resp.is_success:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                try:
                    return resp.json()
                except Exception:
                    return body
            # Try XML → dict; fall back to raw string
            try:
                return xmltodict.parse(body)
            except Exception:
                return body

        if resp.status_code in (404, 503):
            # May indicate FSM not ready – return text for caller to decide
            return body

        err = _ERROR_MESSAGES.get(resp.status_code, f"HTTP {resp.status_code}")
        raise FortiSIEMError(f"status {resp.status_code}: {err}\n{body}", status_code=resp.status_code)

    # ------------------------------------------------------------------
    # Retry helper (for 429 rate-limiting)
    # ------------------------------------------------------------------

    async def request_with_retries(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        for attempt in range(1, self._max_retries + 1):
            try:
                return await self.request(method, endpoint, **kwargs)
            except FortiSIEMError as exc:
                if exc.status_code == 429 and attempt < self._max_retries:
                    logger.warning("Rate-limited (429). Retry %d/%d …", attempt, self._max_retries)
                    await asyncio.sleep(self._wait_time)
                    continue
                raise

    # ------------------------------------------------------------------
    # Query polling helper
    # ------------------------------------------------------------------

    async def poll_query_progress(
        self,
        query_id: str,
        progress_endpoint: Optional[str] = None,
    ) -> bool:
        """
        Poll FortiSIEM until a query reaches 100 % progress.

        Returns True when done, raises QueryStillInProgressError on timeout.
        """
        endpoint = progress_endpoint or f"/rest/query/progress/{query_id}"
        iterations = self._max_iterations
        while iterations > 0:
            resp = await self.request_with_retries("GET", endpoint)
            pct = resp.get("progressPct", 0) if isinstance(resp, dict) else resp
            pct = _parse_progress_pct(pct)
            if str(pct) == "100":
                return True
            await asyncio.sleep(self._poll_interval)
            iterations -= 1
        raise QueryStillInProgressError(query_id)


# ------------------------------------------------------------------
# Utility: parse query ID / progress from XML or plain string
# ------------------------------------------------------------------

def parse_query_id(raw: str) -> str:
    """
    FortiSIEM returns either:
      - plain "queryId,expireTime" string
      - XML <response requestId="…"> … <expireTime>…</expireTime>
    Returns canonical "requestId,expireTime" string.
    """
    if re.match(r"^\d+,\d+$", raw) or re.match(r"^\d+$", raw):
        return raw
    try:
        parsed = xmltodict.parse(raw)
        result = parsed.get("response", {}).get("result", {})
        if "progress" in result:
            return result["progress"]
        request_id = parsed["response"].get("@requestId")
        expire_time = result.get("expireTime")
        if request_id and expire_time:
            return f"{request_id},{expire_time}"
        raise FortiSIEMError(f"Cannot parse query ID from: {raw}")
    except FortiSIEMError:
        raise
    except Exception as exc:
        raise FortiSIEMError(f"Cannot parse query ID from response: {exc}") from exc


def _parse_progress_pct(raw: Any) -> str:
    """Extract numeric progress percentage from various response formats."""
    if isinstance(raw, dict):
        return str(raw.get("progressPct", 0))
    if isinstance(raw, str):
        try:
            parsed = xmltodict.parse(raw)
            pct = parsed.get("response", {}).get("result", {}).get("progress", "0")
            return str(pct)
        except Exception:
            pass
    return str(raw)
