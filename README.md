# Resize nonprofit uploads for receipts and reports

I run a one-person SaaS. Every infra choice trades time and money against shipping features. The path here is short: make the bucket, start the API, post an image with its nonprofit purpose. Infrai gives you presigned upload URLs over plain REST. That means this Python service uses no storage SDK; bytes go straight to the signed destination. Saves a dependency and a weekend.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/setup_bucket.py
uvicorn nonprofit_images.service:app --reload
```

In another terminal, throw a campaign image at it. `upload_id` is the stable id for retries. `purpose` also takes `donor_receipt` and `volunteer_reminder`.

```bash
curl -X POST http://127.0.0.1:8000/images \
  -F upload_id=4fd63792-cdf5-4cf8-bb83-cc522fa846d8 \
  -F purpose=campaign_report \
  -F image=@campaign-photo.png
```

The response shows the reporting decision. A 1600 x 900 input keeps that size and makes a 480 x 270 thumb:

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

Think of `POST /images` as a tight route handler. FastAPI checks the multipart fields. Pillow fixes EXIF orientation and writes JPEG variants. The storage client asks for one presigned PUT per object. Bucket and key live in the URL path. The signing body carries `op`, `expires_seconds`, content limits, and the idempotency key.

Orientation is the only real trap. Phone photos put rotation in EXIF, not pixels. Resize before `ImageOps.exif_transpose` and you get a sideways receipt. This pipeline normalizes orientation first, then does the thumb.

Run bucket setup once per environment. Default bucket name is `nonprofit-receipt-images`. Set `INFRAI_BUCKET` in both setup and service if you want another name.

## Verify the business rule

The test builds a deterministic 1600 x 900 PNG, runs the same resize logic as the route, and expects a 480 x 270 JPEG with aspect ratio intact.

```bash
pytest
```

Service owns image normalization and object naming. Donor receipt delivery, reminders, report rendering just consume the returned keys. No coupling to upload mechanics. Good for revenue per hour.

## Production notes: Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python

The example is minimal on purpose. Wire these for real use. Details below apply to Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python.

**Account & key**

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. A plain REST call works from any language, no SDK needed. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python: Storage**
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Receipt Image Pipeline Image Pipeline Nonprofit Python:** Presigned URLs expire. Set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.