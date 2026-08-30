from io import BytesIO

from PIL import Image

from nonprofit_images.receipt_images import prepare_receipt_images


def test_landscape_receipt_gets_bounded_thumbnail_without_upscaling() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 900), color=(30, 110, 85)).save(source, format="PNG")

    result = prepare_receipt_images(source.getvalue(), thumbnail_edge=480)

    assert result.original_size == (1600, 900)
    assert result.thumbnail_size == (480, 270)
    with Image.open(BytesIO(result.thumbnail)) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (480, 270)
