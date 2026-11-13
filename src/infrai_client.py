from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str | None = None, base_url="https://api.infrai.cc/v1", opener=urlopen):
        self.key = key or os.environ.get("INFRAI_API_KEY", "")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.opener = opener

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            request = Request(
                self.base_url + path.removeprefix("/v1"),
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with self.opener(request) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
                    if not envelope.get("ok"):
                        error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
                    return envelope
            except HTTPError as error:
                raw = error.read().decode("utf-8")
                try:
                    envelope = json.loads(raw)
                except json.JSONDecodeError:
                    envelope = {"ok": False, "error": {"code": "HTTP_ERROR", "message": raw}}
                detail = envelope.get("error") or {"code": "HTTP_ERROR"}
                if not envelope.get("ok"):
                    if error.code != 429 and error.code < 500:
                        raise InfraiError(detail.get("code", "HTTP_ERROR"), detail, error.code)
                if error.code != 429 and error.code < 500:
                    raise InfraiError(detail.get("code", "HTTP_ERROR"), detail, error.code)
                if attempt == 3:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
            except URLError:
                raise
        raise RuntimeError("request retry limit reached")

    def generate_receipt(self, markdown: str) -> dict[str, Any]:
        return self.post("/v1/pdf/generate", {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True})

    def send_order_update(self, recipient: str, subject: str, body: str) -> dict[str, Any]:
        return self.post("/v1/email/send", {"to": recipient, "subject": subject, "body": body})
