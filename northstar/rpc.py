from __future__ import annotations

import time
from typing import Any

from .net import FetchResult, HttpClient


class RpcCluster:
    """JSON-RPC client with endpoint failover and per-call retry."""

    def __init__(self, client: HttpClient, endpoints: list[str], gap_seconds: float = 0.35, timeout: float = 45.0):
        self.client = client
        self.endpoints = list(endpoints)
        self.gap = gap_seconds
        self.timeout = timeout
        self.active = endpoints[0] if endpoints else ""
        self.log: list[dict[str, Any]] = []

    def call(self, method: str, params: list[Any] | None = None) -> FetchResult:
        last: FetchResult | None = None
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        # Prefer the last healthy endpoint, then rotate.
        ordered = [self.active] + [e for e in self.endpoints if e != self.active]
        for url in ordered:
            if last is not None:
                time.sleep(self.gap)
            result = self.client.request(url, method="POST", json_body=payload, timeout=self.timeout)
            record = {
                "method": method,
                "url": url,
                "ok": result.ok,
                "status": result.status,
                "elapsed_ms": result.elapsed_ms,
                "error": result.error,
                "bytes": result.bytes,
            }
            if result.ok and isinstance(result.data, dict) and "error" in result.data:
                rpc_err = result.data.get("error")
                result = FetchResult(
                    ok=False,
                    url=url,
                    status=result.status,
                    error=f"RPC error: {rpc_err}",
                    elapsed_ms=result.elapsed_ms,
                    retries=result.retries,
                    bytes=result.bytes,
                )
                record["ok"] = False
                record["error"] = result.error
            self.log.append(record)
            if result.ok:
                self.active = url
                return result
            last = result
        return last or FetchResult(ok=False, url="", error="no RPC endpoints configured")
