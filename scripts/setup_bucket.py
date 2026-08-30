import asyncio
import os

from nonprofit_images.infrai_storage import InfraiStorage


async def main() -> None:
    bucket = os.environ.get("INFRAI_BUCKET", "nonprofit-receipt-images")
    storage = InfraiStorage(os.environ.get("INFRAI_API_KEY", ""))
    try:
        await storage.create_bucket(bucket)
        print(f"Bucket ready: {bucket}")
    finally:
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
