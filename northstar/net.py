from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FetchResult:
    ok: bool
    url: str
    status: int | None = None
    data: Any = None
    error: str | None = None
    elapsed_ms: int = 0
    retries: int = 0
    bytes: int = 0


@dataclass
class HttpClient:
    user_agent: str
    timeout: float = 30.0
    max_retries: int = 3
    backoff: float = 1.6
    _ctx: ssl.SSLContext = field(default_factory=ssl.create_default_context)

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        payload: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        json_body: Any = None,
    ) -> FetchResult:
        hdrs = {"User-Agent": self.user_agent, "Accept": "application/json, text/html;q=0.8"}
        body = payload
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        if headers:
            hdrs.update(headers)
        timeout = self.timeout if timeout is None else timeout
        last_err = "unknown"
        status = None
        for attempt in range(self.max_retries + 1):
            started = time.time()
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as resp:
                    raw = resp.read()
                    status = getattr(resp, "status", 200)
                    elapsed = int((time.time() - started) * 1000)
                    parsed: Any
                    ctype = (resp.headers.get("Content-Type") or "").lower()
                    if "json" in ctype or (raw[:1] in (b"{", b"[")):
                        try:
                            parsed = json.loads(raw.decode("utf-8"))
                        except json.JSONDecodeError:
                            parsed = raw.decode("utf-8", "replace")
                    else:
                        parsed = raw.decode("utf-8", "replace")
                    return FetchResult(
                        ok=True,
                        url=url,
                        status=status,
                        data=parsed,
                        elapsed_ms=elapsed,
                        retries=attempt,
                        bytes=len(raw),
                    )
            except urllib.error.HTTPError as exc:
                status = exc.code
                elapsed = int((time.time() - started) * 1000)
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                body_preview = ""
                try:
                    body_preview = exc.read()[:300].decode("utf-8", "replace")
                except Exception:
                    body_preview = str(exc)
                last_err = f"HTTP {exc.code}: {body_preview or exc.reason}"
                if exc.code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    sleep_s = self.backoff ** attempt
                    if retry_after:
                        try:
                            sleep_s = max(sleep_s, float(retry_after))
                        except ValueError:
                            pass
                    time.sleep(min(sleep_s, 12.0))
                    continue
                return FetchResult(
                    ok=False,
                    url=url,
                    status=status,
                    error=last_err,
                    elapsed_ms=elapsed,
                    retries=attempt,
                )
            except Exception as exc:
                elapsed = int((time.time() - started) * 1000)
                last_err = f"{type(exc).__name__}: {exc}"
                if attempt < self.max_retries:
                    time.sleep(min(self.backoff ** attempt, 12.0))
                    continue
                return FetchResult(
                    ok=False,
                    url=url,
                    status=status,
                    error=last_err,
                    elapsed_ms=elapsed,
                    retries=attempt,
                )
        return FetchResult(ok=False, url=url, status=status, error=last_err)
