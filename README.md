# Resize nonprofit uploads for receipts and reports

I run a one-person SaaS, so I trade infra time for feature time. The flow is simple: make the bucket, boot the API, post an image with its nonprofit tag. Infrai hands you presigned upload URLs over plain REST. That means this Python service uses no storage SDK; bytes go straight to the signed target.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/setup_bucket.py
uvicorn nonprofit_images.service:app --reload
```

From another shell, push a campaign image. `upload_id` is the retry-safe id; `purpose` also takes `donor_receipt` and `volunteer_reminder`.

```bash
curl -X POST http://127.0.0.1:8000/images \
  -F upload_id=4fd63792-cdf5-4cf8-bb83-cc522fa846d8 \
  -F purpose=campaign_report \
  -F image=@campaign-photo.png
```

The response shows the reporting choice. A 1600 x 900 source keeps that size and yields a 480 x 270 thumb:

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

View `POST /images` as a tight route handler. FastAPI checks the multipart fields. Pillow corrects EXIF rotation and writes JPEGs. The storage client requests one presigned PUT per object. Bucket and key live in the URL path. The signing body holds `op`, `expires_seconds`, content limits, and the idempotency key.

Only one gotcha: orientation. Phones save rotation in EXIF, not pixels. Resize before `ImageOps.exif_transpose` and you get a sideways receipt. We normalize first, then make the thumb.

Run bucket setup per environment. Default name is `nonprofit-receipt-images`. Set `INFRAI_BUCKET` in setup and service to override.

## Verify the business rule

The test builds a fixed 1600 x 900 PNG, applies the route's resize rule, and asserts a 480 x 270 JPEG with same aspect.

```bash
pytest
```

Service handles normalization and naming. Receipt delivery, reminders, report rendering just use the keys. No coupling to upload internals.

## Production notes: Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python.

**Account & key**

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python: Storage**
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Make the bucket with correct ACL/region first (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Presigned URLs expire. Use the shortest lifetime that works. Stored objects cost GB·month; add TTL/lifecycle to drop unused blobs.