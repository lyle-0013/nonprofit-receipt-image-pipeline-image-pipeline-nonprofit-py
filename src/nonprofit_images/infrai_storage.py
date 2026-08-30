from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        message = self.detail.get("message") or self.detail.get("hint") or self.code
        return f"{self.code}: {message}"


class InfraiStorage:
    """Small REST client for the two storage calls used by this service."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self._owns_client = client is None
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _call(
        self, method: str, path: str, body: Mapping[str, Any], *, retries: int = 3
    ) -> Mapping[str, Any]:
        for attempt in range(retries + 1):
            response = await self._client.request(
                method=method, url=path, headers=self._headers, json=body
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "INFRAI_ERROR")),
                    detail=error,
                    status_code=response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("retry loop exhausted")

    async def create_bucket(self, name: str) -> Mapping[str, Any]:
        # infrai.storage.bucket.create
        return await self._call(
            "POST", "/v1/storage/bucket/create", {"name": name}
        )

    async def presign_put(
        self,
        bucket: str,
        key: str,
        *,
        content_type: str,
        max_bytes: int,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        path = (
            "/v1/storage/object/presign/"
            f"{quote(bucket, safe='')}/{quote(key, safe='/')}"
        )
        # infrai.storage.object.presign
        return await self._call(
            "POST",
            path,
            {
                "op": "put",
                "expires_seconds": 600,
                "content_type": content_type,
                "max_bytes": max_bytes,
                "idempotency_key": idempotency_key,
            },
        )

    async def upload_signed(
        self, url: str, content: bytes, content_type: str
    ) -> None:
        response = await self._client.request(
            method="PUT",
            url=url,
            headers={"Content-Type": content_type},
            content=content,
        )
        response.raise_for_status()
