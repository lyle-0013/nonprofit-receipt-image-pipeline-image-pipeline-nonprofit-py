from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps


@dataclass(frozen=True)
class ReceiptImageSet:
    original: bytes
    thumbnail: bytes
    original_size: tuple[int, int]
    thumbnail_size: tuple[int, int]


def prepare_receipt_images(source: bytes, thumbnail_edge: int = 480) -> ReceiptImageSet:
    """Normalize orientation and make a bounded JPEG preview for nonprofit workflows."""
    with Image.open(BytesIO(source)) as opened:
        normalized = ImageOps.exif_transpose(opened).convert("RGB")
        original_size = normalized.size

        original_buffer = BytesIO()
        normalized.save(original_buffer, format="JPEG", quality=90, optimize=True)

        preview = normalized.copy()
        preview.thumbnail((thumbnail_edge, thumbnail_edge), Image.Resampling.LANCZOS)
        thumbnail_buffer = BytesIO()
        preview.save(thumbnail_buffer, format="JPEG", quality=82, optimize=True)

    return ReceiptImageSet(
        original=original_buffer.getvalue(),
        thumbnail=thumbnail_buffer.getvalue(),
        original_size=original_size,
        thumbnail_size=preview.size,
    )
