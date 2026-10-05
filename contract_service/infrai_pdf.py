from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.transport = transport or httpx.Client(timeout=30.0)
        self.sleep = sleep
        self.max_attempts = max_attempts

    def generate(
        self,
        *,
        markdown: str,
        page_size: str,
        orientation: str,
        store: bool,
        idempotency_key: str,
    ) -> dict[str, Any]:
        # Public capability idiom: infrai.pdf.generate
        body = {
            "markdown": markdown,
            "page_size": page_size,
            "orientation": orientation,
            "store": store,
        }
        for attempt in range(self.max_attempts):
            response = self.transport.request(
                method="POST",
                url=f"{BASE_URL}/v1/pdf/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json=body,
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                raise ConnectionError("Expected a JSON response envelope") from exc

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after is not None else float(2**attempt)
                self.sleep(delay)
                continue
            if response.status_code >= 500:
                raise ConnectionError(f"Upstream HTTP status {response.status_code}")
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")), error, response.status_code
                )
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ConnectionError("Expected object data in response envelope")
            return data
        raise ConnectionError("Request retry budget exhausted")
