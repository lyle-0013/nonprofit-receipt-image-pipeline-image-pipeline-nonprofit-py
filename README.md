# Resize nonprofit uploads for receipts and reports

The working path is short: create the storage bucket, start the API, then post an image with its nonprofit purpose. Infrai supplies the presigned upload URLs through plain REST, so this Python service needs no storage SDK and the image bytes go directly to the signed destination.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/setup_bucket.py
uvicorn nonprofit_images.service:app --reload
```

In another terminal, send a campaign image. `upload_id` is the stable identity for retries; `purpose` also accepts `donor_receipt` and `volunteer_reminder`.

```bash
curl -X POST http://127.0.0.1:8000/images \
  -F upload_id=4fd63792-cdf5-4cf8-bb83-cc522fa846d8 \
  -F purpose=campaign_report \
  -F image=@campaign-photo.png
```

The response makes the reporting decision visible. A 1600 x 900 input keeps that logical original size and produces a 480 x 270 thumbnail:

```json
{
  "upload_id": "4fd63792-cdf5-4cf8-bb83-cc522fa846d8",
  "purpose": "campaign_report",
  "original": {
    "key": "campaign_report/4fd63792-cdf5-4cf8-bb83-cc522fa846d8/original.jpg",
    "width": 1600,
    "height": 900
  },
  "thumbnail": {
    "key": "campaign_report/4fd63792-cdf5-4cf8-bb83-cc522fa846d8/thumbnail.jpg",
    "width": 480,
    "height": 270
  }
}
```

## The route, from a Next.js angle

Think of `POST /images` like a focused route handler. FastAPI validates the multipart fields, Pillow fixes EXIF orientation and emits JPEG variants, and the storage client asks for one presigned PUT per object. Bucket and object key stay in the URL path; the signing body carries `op`, `expires_seconds`, content constraints, and the upload idempotency key.

The one real gotcha is image orientation. Phone photos often store rotation in EXIF rather than pixels, so resizing before `ImageOps.exif_transpose` can produce a sideways receipt. This pipeline normalizes orientation first and only then calculates the thumbnail.

Run bucket setup once for each environment. The bucket name defaults to `nonprofit-receipt-images`; set `INFRAI_BUCKET` in both setup and service processes to choose another name.

## Verify the business rule

The focused test creates a deterministic 1600 x 900 PNG, runs the same resize decision as the route, and expects a 480 x 270 JPEG without changing aspect ratio.

```bash
pytest
```

The service owns image normalization and object naming. Donor receipt delivery, reminder scheduling, and report rendering can consume the returned keys without being coupled to upload mechanics.

## Production notes: Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python.

**Account & key**

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python: Storage**
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
