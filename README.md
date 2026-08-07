# OmniSocials Python SDK

The official Python client for the [OmniSocials](https://omnisocials.com) Public API. Schedule and publish posts, upload media, and read analytics across Instagram, Facebook, LinkedIn, YouTube, TikTok, X, Pinterest, Bluesky, Threads, Mastodon, and Google Business.

Full API reference: [https://docs.omnisocials.com](https://docs.omnisocials.com)

## Install

```bash
pip install omnisocials
```

Requires Python 3.9+. The only dependency is [httpx](https://www.python-httpx.org/).

## Quickstart

```python
from omnisocials import OmniSocials

client = OmniSocials()  # reads OMNISOCIALS_API_KEY from the environment
post = client.posts.create(content="Hello from Python", channels=["instagram", "linkedin"])
print(post["data"]["id"])
```

## Authentication

Create an API key in the OmniSocials app under **Settings -> API Keys**. Keys look like `omsk_live_...` (or `omsk_test_...` for test keys) and are bound to one workspace.

Pass the key explicitly or set the `OMNISOCIALS_API_KEY` environment variable:

```python
from omnisocials import OmniSocials

client = OmniSocials(api_key="omsk_live_...")
# or: export OMNISOCIALS_API_KEY=omsk_live_... and just OmniSocials()
```

The client is a context manager; use `with` (or call `client.close()`) to release connections:

```python
with OmniSocials() as client:
    accounts = client.accounts.list()
```

## Async client

Every resource and method exists on `AsyncOmniSocials` with identical names:

```python
import asyncio
from omnisocials import AsyncOmniSocials

async def main():
    async with AsyncOmniSocials() as client:
        posts = await client.posts.list(status="scheduled")
        print(len(posts["data"]))

asyncio.run(main())
```

## Posts

### Schedule a post

```python
post = client.posts.create(
    content="Big announcement coming Friday",
    channels=["instagram", "facebook", "linkedin"],
    scheduled_at="2026-08-01T09:00:00Z",
    media_urls=["https://example.com/teaser.jpg"],
)
```

Omit `scheduled_at` to create a draft, or use `create_and_publish` to publish immediately:

```python
post = client.posts.create_and_publish(
    content="We are live!",
    channels=["x", "bluesky"],
)
```

### Per-media alt text

Every `media_urls` / `media_ids` entry accepts either a plain string or a dict with an `alt` accessibility description (max 1500 chars). Alt text is delivered to Mastodon (media description), Bluesky (embed alt), X (photos and GIFs), Pinterest (pin alt text), Instagram (images), and LinkedIn (images). Strings and dicts can be mixed, and the same shape works in per-platform mappings and `thread_parts` media.

```python
post = client.posts.create(
    content="Sunrise over the harbor",
    channels=["mastodon", "bluesky"],
    scheduled_at="2026-08-01T09:00:00Z",
    media_urls=[
        {
            "url": "https://example.com/harbor.jpg",
            "alt": "A small sailboat crossing a calm harbor at sunrise, sky in deep orange",
        }
    ],
)
```

### Post to specific platforms with platform options

`content` can be a per-platform mapping (with `default` as the fallback), and each platform has its own options object:

```python
post = client.posts.create(
    content={
        "default": "New feature: best times to post",
        "linkedin": "We just shipped best times to post. Here is how it works.",
    },
    channels=["linkedin", "instagram", "youtube"],
    media_urls=["https://example.com/demo.mp4"],
    scheduled_at="2026-08-01T09:00:00Z",
    instagram={"share_to_feed": True},
    youtube={"title": "Best times to post, explained", "privacy_status": "public"},
)
```

Note that `linkedin` targets a personal LinkedIn profile and `linkedin_page` targets a LinkedIn company page. Both can be connected to the same workspace and posted to independently.

### X thread example

Pass 2 to 25 `thread_parts` to publish a chained thread instead of a single tweet (each part is at most 280 characters). Bluesky and Mastodon support the same `thread_parts` shape:

```python
post = client.posts.create(
    content="How we cut our API response times by 80%",  # fallback text
    channels=["x"],
    scheduled_at="2026-08-01T15:00:00Z",
    x={
        "thread_parts": [
            {"text": "How we cut our API response times by 80%. A thread:"},
            {"text": "1/ We started by profiling every endpoint under real load."},
            {"text": "2/ The biggest win: batching analytics reads into one query."},
            {"text": "3/ Full write-up on the blog. Thanks for reading!"},
        ]
    },
)
```

On update, passing `x={"thread_parts": None}` clears the thread and reverts the post to single-tweet mode. Only top-level `None` values are dropped from request bodies, so nested `None` values like this one are sent as JSON `null`.

### X link posts use credits

X bills API posts whose text contains a URL at a premium, and OmniSocials passes that fee through as prepaid credits (20 credits per URL-containing tweet; threads billed per part with a link). When a create targets X and the text contains a URL, the response includes a top-level `warnings` list (a sibling of `data`):

```python
res = client.posts.create(
    content="Read the full story: https://example.com/post",
    channels=["x"],
)
for warning in res.get("warnings", []):
    if warning["code"] == "x_url_post_credits":
        print(warning["credits_required"], warning["credits_balance"])
```

From `enforce_from` (2026-08-14) the balance is checked at publish time, but credits are only deducted after the post successfully publishes (a failed publish is never charged). If the balance can't cover it, only the X target fails (other platforms publish normally); top up in the dashboard under Settings -> Organisation -> Billing -> Credits, then call `posts.retry`. Posts without links, analytics, and media on X stay free. There is no API endpoint for credits — they are managed in the dashboard.

### Other post operations

```python
posts = client.posts.list(status="scheduled", limit=50, offset=0)
post = client.posts.get("123")
client.posts.update("123", scheduled_at="2026-08-02T10:00:00Z")
client.posts.publish("123")           # publish a draft or scheduled post now
client.posts.retry("123")             # retry only the failed platforms of a failed/warning post
client.posts.delete("123")            # returns None (204)

# Recent posts fetched live from the connected platforms (including content
# published outside OmniSocials). Requires the analytics:read scope. Video
# records include duration_seconds (whole seconds; TikTok and YouTube today,
# null for images and platforms that don't expose it).
recent = client.posts.recent_platform(limit=10, platforms=["instagram", "tiktok"])
```

`retry` re-publishes only the platforms that failed, on the same post; platforms that already succeeded are never posted again. It is asynchronous: a 200 means the retry is queued, so poll `get` for the outcome. Max 3 retries per platform.

## Media

### Upload from a URL (recommended, up to 1GB)

```python
media = client.media.upload_from_url(
    url="https://example.com/promo.mp4",
    name="promo-august",
    folder="Campaigns",
)
media_id = media["data"]["id"]
```

Files over 100MB are processed in the background: the response has `data["status"] == "processing"`; poll `client.media.get(media_id)` until it is `"ready"` before attaching it to a post.

### Upload a local file (multipart, max 100MB)

```python
media = client.media.upload(file="/path/to/image.jpg", name="hero-shot")
# file can also be raw bytes or a binary file-like object
```

Uploading a PDF splits it into image slides (max 20 pages) and returns `slides` plus a `media_ids` array. Pass all of `media_ids`, in order, to `posts.create` to publish the deck as a carousel (a native swipeable document on LinkedIn, an image carousel elsewhere).

Every upload response also includes a `compatibility` block listing any connected platforms that would reject the file.

### Other media operations

```python
files = client.media.list(search="promo", folder_id="42")
item = client.media.get("1001")
client.media.update("1001", name="renamed", folder_id="42")
client.media.update("1001", folder_id=None)   # move to the root ("All media")
client.media.delete("1001")

# Base64 upload (handy when you have bytes but no URL)
client.media.upload_from_base64(data=b64_string, mime_type="image/png")

# Preflight compatibility BEFORE uploading
result = client.media.check(url="https://example.com/huge.mp4")
if not result["compatible"]:
    print(result["summary"])
```

### Large file uploads with a presigned URL

`create_upload_url` mints a one-time upload URL so any environment (a CI job, a sandbox, a script without the SDK) can upload a file without auth headers:

```python
import httpx

grant = client.media.create_upload_url()
# grant contains: upload_url, upload_token, expires_in_seconds (600),
# method ("POST"), content_type ("multipart/form-data")

with open("/path/to/video.mp4", "rb") as f:
    response = httpx.post(grant["upload_url"], files={"file": f})
media_id = response.json()["data"]["id"]
```

The token is single-use and expires after 10 minutes. The response JSON contains the created media item with its `id` (or a `media_ids` array for a PDF).

## Folders

```python
folders = client.folders.list()
folder = client.folders.create(name="Campaigns")
sub = client.folders.create(name="August", parent_id=folder["data"]["id"])
client.folders.update(sub["data"]["id"], name="August 2026")
client.folders.update(sub["data"]["id"], parent_id=None)  # move to top level
client.folders.delete(folder["data"]["id"])  # files move to root, subfolders move up
```

## Hashtag Sets

Save reusable hashtag groups and apply them to posts at create time. Uses the `posts:read` / `posts:write` scopes.

```python
hashtag_set = client.hashtag_sets.create(
    name="Launch",
    hashtags=["saas", "buildinpublic", "startup"],  # or one string: "#saas #buildinpublic #startup"
)
print(hashtag_set["data"]["preview"])  # "#saas #buildinpublic #startup"

client.hashtag_sets.list()
client.hashtag_sets.get(hashtag_set["data"]["id"])
client.hashtag_sets.update(hashtag_set["data"]["id"], hashtags=["saas", "founder"])  # replaces the full list
client.hashtag_sets.delete(hashtag_set["data"]["id"])  # returns None (204)
```

Apply a set when creating a post with `hashtag_set` (the set name, case-insensitive) or `hashtag_set_id`. The set is applied once at create time and tags already in the caption are skipped. `hashtag_placement` is `"caption_append"` (default) or `"first_comment"`, and `hashtag_platforms` restricts the hashtags to a subset of the post's channels. Instagram's 30-hashtag cap returns error code `hashtag_limit_exceeded`.

```python
client.posts.create(
    content="Launch day!",
    channels=["instagram", "x"],
    scheduled_at="2026-08-01T09:00:00Z",
    hashtag_set="Launch",
    hashtag_placement="first_comment",
    hashtag_platforms=["instagram"],
)
```

## Accounts

```python
accounts = client.accounts.list()
for account in accounts["data"]:
    print(account["platform"], account["username"])

account = client.accounts.get("instagram")
```

## Analytics

```python
# One post
stats = client.analytics.post("123")

# Up to 100 posts in one request (avoids rate limit trouble when syncing)
bulk = client.analytics.posts(["123", "124", "125"])

# Workspace overview
overview = client.analytics.overview(period="30d")

# Account-level stats (followers etc.)
accounts = client.analytics.accounts(platform="instagram")
```

### Best times to post

```python
best = client.analytics.best_times(platform="instagram", timezone="Europe/Amsterdam")
for slot in best["data"]["best_times"]:
    print(slot)
```

## Locations (Instagram place tagging)

```python
results = client.locations.search("Blue Bottle Coffee Oakland")
location_id = results["data"][0]["id"]
client.locations.validate(location_id)

client.posts.create(
    content="Great coffee here",
    channels=["instagram"],
    media_urls=["https://example.com/latte.jpg"],
    location_id=location_id,
)
```

## Webhooks

Subscribe to `post.scheduled`, `post.published`, and `post.failed` events:

```python
webhook = client.webhooks.create(
    url="https://example.com/hooks/omnisocials",
    events=["post.published", "post.failed"],
)
secret = webhook["data"]["secret"]  # only shown once, store it

client.webhooks.list()
client.webhooks.get(webhook["data"]["id"])
client.webhooks.update(webhook["data"]["id"], is_active=False)
client.webhooks.rotate_secret(webhook["data"]["id"])  # new secret, shown once
client.webhooks.delete(webhook["data"]["id"])
```

### Verifying webhook signatures (FastAPI example)

Every delivery is signed with HMAC-SHA256. The `X-OmniSocials-Signature` header has the form `t=<unix>,v1=<hex>`, signed over `"{timestamp}.{raw_body}"`. Use `verify_webhook_signature` with the raw request body (do not parse it first):

```python
from fastapi import FastAPI, Header, HTTPException, Request
from omnisocials import WebhookVerificationError, verify_webhook_signature

app = FastAPI()
WEBHOOK_SECRET = "whsec_from_webhook_creation"

@app.post("/hooks/omnisocials")
async def omnisocials_webhook(
    request: Request,
    x_omnisocials_signature: str = Header(None),
):
    payload = await request.body()  # raw bytes, exactly as received
    try:
        event = verify_webhook_signature(
            payload, x_omnisocials_signature, WEBHOOK_SECRET, tolerance=300
        )
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "post.published":
        for target in event["data"]["targets"]:
            print(target["platform"], target["status"], target.get("native_post_id"))
    return {"ok": True}
```

`verify_webhook_signature` uses a constant-time comparison, rejects timestamps older than `tolerance` seconds (default 300) to block replays, and returns the parsed event dict on success. Respond with any 2xx within 10 seconds to acknowledge; deliveries are retried up to 3 times.

## Error handling

Non-2xx responses raise typed exceptions with `status`, `code`, `message`, and the parsed `body`:

```python
from omnisocials import (
    OmniSocials,
    APIError,
    APIConnectionError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

client = OmniSocials()

try:
    client.posts.get("does-not-exist")
except NotFoundError as exc:
    print("Gone:", exc.code, exc.message)
except RateLimitError as exc:
    print(f"Slow down, retry in {exc.retry_after}s")
except ValidationError as exc:
    print("Bad request:", exc.body)
except AuthenticationError:
    print("Check your API key")
except APIConnectionError:
    print("Network problem")
except APIError as exc:
    print("API error:", exc.status, exc.message)
```

The full hierarchy: `OmniSocialsError` is the base; `APIError` covers all HTTP errors with subclasses `AuthenticationError` (401), `PermissionDeniedError` (403), `NotFoundError` (404), `ValidationError` (400/422), `RateLimitError` (429, with `.retry_after`), and `ServerError` (5xx); `APIConnectionError` covers network failures; `WebhookVerificationError` covers signature failures.

## Rate limits

The API allows **100 requests per minute** per API key. Every response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers. On 429 the SDK automatically waits for the `Retry-After` value and retries. When syncing analytics for many posts, prefer the bulk `client.analytics.posts([...])` endpoint (100 posts per request) over per-post calls.

## Retries and timeouts

The SDK automatically retries on 429, 5xx, and connection errors with exponential backoff (0.5s, 1s, 2s, with jitter), honoring the `Retry-After` header when present. Other 4xx errors are never retried. Defaults: 2 retries, 30 second timeout. Both are configurable:

```python
client = OmniSocials(
    api_key="omsk_live_...",
    timeout=60.0,       # seconds
    max_retries=5,      # retries after the first attempt
    base_url="https://api.omnisocials.com/v1",  # override for testing
)
```

## More

- Full API reference and guides: [https://docs.omnisocials.com](https://docs.omnisocials.com)
- MCP server for AI agents: `npx -y @omnisocials/mcp-server`
- Agent skills CLI: `npx skills add OmniSocials/omnisocials-agent-skills`

## License

MIT
