from __future__ import annotations

import os
from contextlib import asynccontextmanager
from enum import StrEnum
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .infrai_storage import InfraiError, InfraiStorage
from .receipt_images import prepare_receipt_images

BUCKET = os.environ.get("INFRAI_BUCKET", "nonprofit-receipt-images")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class ImagePurpose(StrEnum):
    DONOR_RECEIPT = "donor_receipt"
    VOLUNTEER_REMINDER = "volunteer_reminder"
    CAMPAIGN_REPORT = "campaign_report"


class StoredVariant(BaseModel):
    key: str
    width: int
    height: int


class NonprofitImageResult(BaseModel):
    upload_id: UUID
    purpose: ImagePurpose
    original: StoredVariant
    thumbnail: StoredVariant


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = InfraiStorage(os.environ.get("INFRAI_API_KEY", ""))
    app.state.storage = storage
    yield
    await storage.close()


app = FastAPI(title="Nonprofit receipt image pipeline", lifespan=lifespan)


@app.post("/images", response_model=NonprofitImageResult, status_code=201)
async def store_nonprofit_image(
    upload_id: UUID = Form(),
    purpose: ImagePurpose = Form(),
    image: UploadFile = File(),
) -> NonprofitImageResult:
    source = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(source) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MiB")

    try:
        prepared = prepare_receipt_images(source)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Upload must be a readable image") from exc

    prefix = f"{purpose.value}/{upload_id}"
    variants = {
        "original": (f"{prefix}/original.jpg", prepared.original),
        "thumbnail": (f"{prefix}/thumbnail.jpg", prepared.thumbnail),
    }
    storage: InfraiStorage = app.state.storage

    try:
        for variant, (key, content) in variants.items():
            signed = await storage.presign_put(
                BUCKET,
                key,
                content_type="image/jpeg",
                max_bytes=len(content),
                idempotency_key=f"{upload_id}:{variant}",
            )
            await storage.upload_signed(signed["url"], content, "image/jpeg")
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    return NonprofitImageResult(
        upload_id=upload_id,
        purpose=purpose,
        original=StoredVariant(
            key=variants["original"][0],
            width=prepared.original_size[0],
            height=prepared.original_size[1],
        ),
        thumbnail=StoredVariant(
            key=variants["thumbnail"][0],
            width=prepared.thumbnail_size[0],
            height=prepared.thumbnail_size[1],
        ),
    )
