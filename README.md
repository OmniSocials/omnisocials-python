# OmniSocials Python SDK

The official Python SDK for OmniSocials: post, schedule, reply and report on 13 social platforms (Instagram, Facebook, LinkedIn, X, TikTok, YouTube, Threads, Pinterest, Bluesky, Mastodon, Google Business, Telegram and Discord) from one API. Guide: [omnisocials.com/sdk/python](https://omnisocials.com/sdk/python)

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

Create an API key in the OmniSocials app under **Settings -> API Keys**. Keys start with `omsk_live_` and are bound to one workspace. There are no test keys and no test mode: every key works on your real connected accounts. To try things safely, leave out `scheduled_at` so the post stays a draft (a draft never publishes on its own), or use a separate workspace with test accounts.

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

### Planned drafts

Pass `draft=True` with `scheduled_at` to store the post as a draft that keeps its time. It shows on the dashboard calendar at that slot with a dashed outline and the scheduler never publishes it: a person schedules it from the composer, or you do with `update` and `draft=False`. Use it when an agent proposes a slot that a human should confirm. `draft=True` is not allowed with `publish_now` or `approval_workflow_id` (`400 validation_error`). On `update`, `draft=False` without `scheduled_at` is a `400 validation_error` when the draft has no time or its time is in the past (pass a new `scheduled_at` then), and `draft=True` on a scheduled post unschedules it while keeping the time.

```python
proposal = client.posts.create(
    content="Proposed for Friday morning",
    channels=["instagram", "linkedin"],
    scheduled_at="2026-08-01T09:00:00Z",
    draft=True,
)
print(proposal["data"]["status"], proposal["data"]["schedule_at"])  # draft, the time is kept

# The human agrees: schedule it at the time it already carries
client.posts.update(proposal["data"]["id"], draft=False)
```

### Comment-to-DM automations

Answer a keyword in an Instagram comment with a DM, once per person, with an optional public reply under the comment. Pass `comment_dm_automation=` on `create` (Instagram must be in `channels`) and the automation is bound to that post; it starts listening once the post is live. Needs the opt-in `automations:write` scope on the key. `client.automations` manages the automations themselves (`list`, `get`, `create`, `update`, `delete`) and reads their activity (`list_events`, `automations:read`). On `update`, `comment_dm_automation=` as a dict replaces the post's automation and an explicit `None` removes it. Instagram rules: one private reply per comment, within 7 days; OmniSocials caps sends at 180 DMs an hour per account.

```python
post = client.posts.create(
    content="Comment GUIDE and I will send you the link",
    channels=["instagram"],
    scheduled_at="2026-08-01T09:00:00Z",
    media_urls=["https://example.com/guide-cover.jpg"],
    comment_dm_automation={
        "trigger": {"keywords": ["guide"], "match": "word"},
        "actions": {
            "dm": {"text": "Here is the guide: https://example.com/guide"},
            "public_reply": {"enabled": True, "variations": ["Sent you a DM!", "Check your inbox"]},
        },
        "limits": {"max_sends": 500},
    },
)
automation_id = post["data"]["comment_dm_automation"]["id"]

# Later: who was answered, and why someone was skipped
events = client.automations.list_events(automation_id, outcome="sent")
print(events["counts"])  # {"sent": 12, "skipped": 3}
for event in events["data"]:
    print(event["person"]["username"], event["outcome"], event["reason_label"])
```

The events response is `{"data", "counts", "pagination"}`, not the plain list: `counts` is the number of events per outcome (`sent`, `skipped`, `failed`, `pending`, `queued`, `opted_out`, `waiting`). An automation can also listen on a post published outside OmniSocials (`client.automations.create(instagram_media_id=..., actions=...)`), on the next post the workspace publishes (`trigger={"scope": "next_post"}`) or on every post (`"scope": "any"`), and on DMs and story replies (`trigger={"kinds": ["dm", "story_reply"], ...}`).

Follow first (`actions["follow_gate"]`, Instagram only) sends the link only to people who follow the account. On a comment the private reply is a first message with one button; a tap makes OmniSocials ask Instagram whether the person follows. A follower gets the DM text, anyone else gets the `not_following` message with its button, and every later tap checks again. A DM or a story reply is checked at once. When Instagram gives no answer the link goes out anyway. Texts hold 640 characters and buttons 20; leave them out for the defaults. A person who has not followed yet is an event with outcome `waiting` and `event["follow_gate"]` (`state`, `taps`, `followed`, `checked`, `after_ask`); `stats["followed"]` counts the people who followed after the ask. `"enabled": True` on a Facebook or X automation is a `400 follow_gate_instagram_only`.

```python
client.automations.update(
    automation_id,
    actions={
        "dm": {"text": "Here is the guide: https://example.com/guide"},
        "follow_gate": {
            "enabled": True,
            "first_message": {"text": "Tap the button and I'll send you the link 👇", "button": "Send me the link"},
            "not_following": {"text": "Almost there! Follow @yourbrand first, then tap the button again.", "button": "I follow now"},
        },
    },
)
```

A Facebook Page works the same way, and the DM lands in Messenger: pass `platform="facebook"` to `client.automations.create()`, or `facebook_post_id=...` for a Page post published outside OmniSocials. On a post, `comment_dm_automation={"platforms": ["instagram", "facebook"], ...}` makes one automation per channel with the same keywords and DM. Facebook has no story replies.

On X, pass `platform="x"` with `trigger={"kinds": ["dm"], "keywords": ["guide"]}`: the X account answers a keyword in a DM, once per person, and every answer ends with "Reply STOP to stop automatic messages." An active X automation needs X DMs on for the workspace (`409 x_dms_off`; `status="paused"` always saves). An answer over the send cap waits in a queue (`queued`) for up to an hour.

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

### Telegram channels and groups

`telegram` is a channel or group the workspace connected in OmniSocials; the OmniSocials bot posts to it. The `telegram` options: `silent`, `link_preview`, `pin`, `protect_content`, `spoiler` and `caption_above_media` (booleans), up to 3 `buttons` (`{ text, url }`, not on an album or a poll), a native `poll` (2 to 12 options of up to 100 characters, `open_period` 5 to 2628000 seconds, `multiple`; the post text is the question, max 300 characters, no media) and `first_comment` (a reply under the post). Text up to 4,096 characters; with media, text over 1,024 characters is sent as a reply under the media. Albums hold up to 10 photos and videos, files up to 50 MB, no Stories. Once sent, the post's `telegram.result` carries the message ids and the link. Telegram gives bots no view counts: analytics carry the reactions and the poll votes.

```python
client.posts.create(
    content="The new collection is live. Tap the button to shop.",
    channels=["telegram"],
    scheduled_at="2026-11-02T09:00:00Z",
    media_urls=["https://example.com/collection.jpg"],
    telegram={
        "silent": True,
        "pin": True,
        "buttons": [{"text": "Shop now", "url": "https://example.com/shop"}],
        "first_comment": "Questions? Reply to this message.",
    },
)

# A native poll: the text is the question.
client.posts.create(
    content="Which day suits the live Q&A?",
    channels=["telegram"],
    telegram={"poll": {"options": ["Tuesday", "Thursday", "Saturday"], "open_period": 86400}},
)
```

### Discord channels

`discord` is one Discord channel the workspace connected in OmniSocials; the post goes out through the channel's incoming webhook and shows the webhook's name and picture. The `discord` options: `silent`, `link_preview` (default on), `allow_mentions` (default off, so @everyone, @here, role and user mentions show as text and ping nobody) and `spoiler` (booleans), `thread_name` (the post title in a forum or media channel, 1 to 100 characters), up to 5 `buttons` (`{ text, url }`, one row, not with a poll) and a native `poll` (2 to 10 options of up to 55 characters, `duration_hours` 1 to 768, default 24, `multiple`; the post text is the question, max 300 characters, no media). Text up to 2,000 characters. Up to 10 images, GIFs and videos per message; a video or GIF over Discord's 20 MB attachment limit is sent as a link in the text. No Stories. Once sent, the post's `discord.result` carries the message id and the link. Discord gives webhooks no view counts: analytics carry the reactions and the poll votes.

```python
client.posts.create(
    content="Patch 2.4 is out. Read the notes below.",
    channels=["discord"],
    scheduled_at="2026-11-02T09:00:00Z",
    media_urls=["https://example.com/patch-notes.png"],
    discord={
        "silent": True,
        "buttons": [{"text": "Patch notes", "url": "https://example.com/patch-2-4"}],
    },
)

# A native poll: the text is the question.
client.posts.create(
    content="Which mode do we test next?",
    channels=["discord"],
    discord={"poll": {"options": ["Ranked", "Co-op", "Arena"], "duration_hours": 48}},
)

# On update every key merges; None removes one option, discord=None removes them all.
client.posts.update("post_id", discord={"poll": None})
```

### Chained threads (X, Bluesky, Mastodon, Threads)

Pass 2 to 25 `thread_parts` to publish a chained thread instead of a single tweet (each part is at most 280 characters, 25,000 for X Premium/Premium+ accounts). Bluesky, Mastodon and Threads support the same `thread_parts` shape (Threads: 2 to 25 parts, 500 characters per part, up to 10 media per part; parts after the first publish as replies to the previous part, and the Threads caption is taken from part 1):

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

```python
# Meta Threads chain with a carousel on the first part
post = client.posts.create(
    content="Behind the scenes of our summer shoot",
    channels=["threads"],
    threads={
        "thread_parts": [
            {"text": "Behind the scenes of our summer shoot. A few highlights:", "media_urls": ["https://example.com/shoot-1.jpg", "https://example.com/shoot-2.jpg"]},
            {"text": "Day one: scouting locations at sunrise."},
            {"text": "Day two: the full crew, 14 hours, zero regrets."},
        ]
    },
)
```

On update, passing `x={"thread_parts": None}` clears the thread and reverts the post to single-tweet mode (same for `bluesky`, `mastodon` and `threads`). Only top-level `None` values are dropped from request bodies, so nested `None` values like this one are sent as JSON `null`.

Threads posts can also carry a location tag: pass `threads={"location_id": "..."}`, a Threads location id from `client.locations.search(platform="threads", q="...")` (Instagram Place ids are not interchangeable). On a multi-part thread the tag lands on part 1; on update, `threads={"location_id": None}` clears it. Threads location tagging is currently rolling out; until Meta approves the permissions it is disabled on production and calls return a clear error.

Threads posts can carry a topic too: pass `threads={"topic_tag": "Build in public"}`. Unlike a #tag in the text, a topic can hold spaces. 1 to 50 characters, no period and no ampersand; a leading `#` is dropped. On a multi-part thread the topic lands on part 1; on update, `threads={"topic_tag": None}` removes it.

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

From `enforce_from` (2026-08-14) the balance is checked at publish time, but credits are only deducted after the post successfully publishes (a failed publish is never charged). If the balance can't cover it, only the X target fails (other platforms publish normally); top up in the dashboard under Settings -> Organisation -> Billing -> Credits, then call `posts.retry`. Posts without links and media on X stay free. X statistics use credits too, at X's price (see [X statistics use credits](#x-statistics-use-credits)). `client.credits.get()` reads the balance; top-ups are made in the dashboard.

From 2026-08-14, scheduling an X link post also reserves its cost up front. If reserving this post's cost would push the company's total reserved credits (across every scheduled X link post) past its balance, `posts.create`, `posts.update`, and `posts.publish` refuse the request before it's even accepted, raising a `402` with `error.code == "x_credits_insufficient"` and `error.details` carrying `credits_required`, `credits_balance`, and `credits_reserved`:

```python
from omnisocials import APIError

try:
    client.posts.create(
        content="Read the full story: https://example.com/post",
        channels=["x"],
        scheduled_at="2026-08-20T09:00:00Z",
    )
except APIError as exc:
    if exc.code == "x_credits_insufficient":
        print(exc.body["error"]["details"])
```

Drafts (no `scheduled_at`) are never gated, and posts publishing before 2026-08-14 are never gated. This gate is separate from the `x_url_post_credits` warning above (a non-blocking notice at create time) and the publish-time debit failure (which fails only the X target, not the whole request).

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

These calls answer `409` and change nothing when the post is not in a state for them:

- `post_publishing`: `update` or `delete` while the post is publishing (status `posting`) or a retry publishes one of its channels. Poll `get` until the status is `published`, `warning` or `failed`. An `update` with only `tags` still works.
- `review_required`: changes were requested on the post (`approval_status` `rejected`), so `publish`, or an `update` that would schedule it, is refused. It needs a new review: create it again with `approval_workflow_id`. Saving it as a draft works.
- `retry_in_progress`: `retry` while another retry of the post runs.
- `media_processing`: a media id in `create`, `create_and_publish` or `update` is still processing. Wait until `client.media.get(id)` says `ready`, then send the same request again. A file whose processing failed answers `400 invalid_media`: upload it again.

### Approve or reject a post

```python
from omnisocials import APIError

# Read the step you review first, then name it on the decision.
review = client.posts.get_approval("123")["data"]
step = review["current_step"]

try:
    client.posts.approve("123", step_order=step)  # approve the step you reviewed
    # or: reject and stop the workflow (comment optional)
    # client.posts.reject("123", comment="Wrong CTA link, please fix.", step_order=step)
except APIError as err:
    if err.code != "step_changed":
        raise
    # Somebody decided since you read it: nothing was decided. Read the approval again.
    print("The review is on step", err.body["error"]["current_step_order"])
```

Only works on a post with `approval_status: "pending"` (`status: "in_approval"`). Both act on behalf of the user who owns the API key, who must be a listed approver for the workflow's CURRENT step. Steps approve in order, so being an approver on a later step is not enough yet (raises a 403 `PermissionDeniedError`). Approving the last step finalizes the post (`scheduled` or `posting`); rejecting stops the whole workflow immediately, not just the current step.

`step_order` is optional: the `current_step` of `get_approval`. When the review is on another step now (somebody decided since you read it, or a retried call already went through), nothing is decided and the call raises a 409 `APIError` with code `step_changed` and `error.current_step_order`, the step the review is on now. Without `step_order` the call acts on whatever step is current, so a retry after a timeout could approve the next step too. The async client takes the same arguments.

### Read the approval review

```python
review = client.posts.get_approval("123")["data"]
if review["status"] == "rejected" and review["rejection"]:
    print(f'Rejected by {review["rejection"]["by"]["name"]}: {review["rejection"]["reason"]}')
for step in review["steps"]:
    print(step["order"], step["name"], step["status"], [(a["name"], a["status"]) for a in step["approvers"]])
```

`get_approval` returns the review of a post that went through an approval workflow: `status` (`none`, `pending`, `approved`, `rejected`), the `workflow`, who requested it and when, `current_step` (the step the post waits on, `None` when the review ended), every step with its approvers and their decisions, the `rejection` (`by`, `reason`, `at`, `step`; `None` when nobody rejected) and the `comments` thread, oldest first. A post without an approval workflow returns `status: "none"` with empty `steps` and `comments`. Read-only; needs the `posts:read` scope.

## Social Inbox

List conversations across connected platforms, read a thread, and reply. Requires an API key with the opt-in `inbox:read` / `inbox:write` scopes. TikTok and YouTube conversations are video comments only (no DMs or mentions); TikTok needs the TikTok comments authorization on the channel. Threads conversations are replies and mentions only (no DMs). The Threads inbox needs a Threads connection with the reply permission: a Threads account connected before 2026-09-14 needs a one-time reconnect in the dashboard (until then replies and hides answer 401 `reauth_required`).

```python
conversations = client.inbox.list_conversations(platform="instagram", unread=True)
conversation_id = conversations["data"][0]["conversation_id"]

thread = client.inbox.get_messages(conversation_id)
for message in thread["data"]:
    print(message["direction"], message["text"])  # direction is "incoming" or "outgoing"

client.inbox.mark_read(conversation_id)
client.inbox.reply(conversation_id, "Thanks for reaching out!")

# Hide a comment someone left on one of your posts (Facebook, Instagram,
# TikTok, YouTube, Threads). hide=False unhides.
client.inbox.hide(thread["data"][0]["id"])

# Like a comment as the Page or account (Facebook, LinkedIn Page, TikTok).
# like=False unlikes. The returned message carries "liked".
liked = client.inbox.like(thread["data"][0]["id"])
print(liked["data"]["liked"])  # True

# Delete a comment outright, or one of your own replies (Facebook, Instagram,
# TikTok; YouTube: hide instead). Replies under it go with it; their ids come
# back as "removed_reply_ids".
client.inbox.delete_message(thread["data"][0]["id"])
```

`platform` filters by `"instagram"`, `"facebook"`, `"linkedin"`, `"tiktok"`, `"youtube"`, `"x"`, or `"threads"`; `type` filters by `"dm"`, `"comment"`, or `"mention"`. TikTok and YouTube replies are comments only; TikTok replies are capped at 150 characters.

### Work queue: what needs an answer

`inbox.next()` hands out the next conversation that still needs a reply (the customer's latest DM with no reply after it, or an unreplied comment/mention that is not hidden), with the whole thread and the post it belongs to (`post["url"]`, `post["media_type"]`), so a reply can be drafted from one call. DMs that can still be answered come first, then Instagram/Facebook DMs whose 24-hour window has closed (`reply_window["open"]` is `False`: answer those from the native app or mark them read), then comments and mentions, oldest first. Replies typed in the native apps count as answers. Only unread items are served by default, so `mark_read` is the durable way to skip one; `exclude` skips conversation ids for the current session only. Always pass `message_id=message["id"]` to `reply` on comment threads: every comment on a post shares one conversation, and without it the reply goes under the newest comment on the post. Pass `include_next=True` to `reply` to get the following item in the same response. `list_conversations(unanswered=True)` gives the same set as a plain list.

```python
item = client.inbox.next(platform="instagram")
while item["data"]:
    message = item["data"]["message"]
    print(item["remaining"], "left.", message["sender"]["username"], message["text"])
    print("post:", item["data"]["conversation"]["post"])

    if not item["data"]["reply_window"]["open"]:
        # An Instagram/Facebook DM past Meta's 24-hour window: reply() would
        # raise 422 outside_messaging_window. Answer it in the app, or skip it.
        client.inbox.mark_read(message["conversation_id"])
        item = client.inbox.next(platform="instagram")
        continue

    reply = client.inbox.reply(
        message["conversation_id"],
        "Thanks! DM sent.",
        message_id=message["id"],  # the comment being answered, not the newest one
        include_next=True,
    )
    item = {"data": reply.get("next"), "remaining": reply.get("remaining", 0)}
```

### X DM replies use credits

Replying to an X DM costs 2 prepaid credits per send, debited from the company balance before the send and auto-refunded if the send fails. `inbox.reply` can fail with a `402` on two new codes: `insufficient_credits` (the balance can't cover the 2 credits) and `x_inbox_suspended` (the workspace's X inbox auto-suspended after the balance hit zero; a top-up turns it back on by itself, but DMs that arrived while suspended are not recovered).

```python
from omnisocials import APIError

try:
    client.inbox.reply(conversation_id, "On it, thanks!")
except APIError as exc:
    if exc.code in ("insufficient_credits", "x_inbox_suspended"):
        print(exc.code, exc.body["error"])
```

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

Files over 100MB are processed in the background: the response has `data["status"] == "processing"`; poll `client.media.get(media_id)` until it is `"ready"` before attaching it to a post. When such a file cannot be queued, the call answers `503 processing_unavailable`: send the same request again in a minute.

### Upload a local file (multipart, max 100MB)

```python
media = client.media.upload(file="/path/to/image.jpg", name="hero-shot")
# file can also be raw bytes or a binary file-like object
```

Uploading a PDF splits it into image slides (max 20 pages) and returns `slides` plus a `media_ids` array. Pass all of `media_ids`, in order, to `posts.create` to publish the deck as a carousel (on LinkedIn a native swipeable document made from the original PDF file, which is kept so text and links stay intact; an image carousel elsewhere). To keep the PDF as ONE library item instead of one item per page, pass `pdf_mode` = `"document"`: the response then has a single `data` item of type `document` (its page images in `pdf.pages`) and `media_ids` holds that one id, which expands into every page at post time.

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

## Post tags

Tags are your workspace's own labels for posts (a hook style, a format, a campaign), to filter posts and compare how each kind does. They never go to a platform. Uses the `posts:read` / `posts:write` scopes; the comparison uses `analytics:read`. A tag is `{"id", "name", "color", "created_at"}`; names are unique in the workspace (case-insensitive, max 40 characters), at most 200 tags per workspace.

```python
tag = client.tags.create(name="Question", color="teal")  # color is optional
client.tags.list()
client.tags.update(tag["data"]["id"], name="Question hook")
client.tags.delete(tag["data"]["id"])  # {"data": {"tag": ..., "posts_untagged": 4}}

# Tag a post: ids or names, a new name becomes a tag (at most 20 per post)
client.posts.create(content="Would you post this?", channels=["instagram"], tags=["Question"])
client.posts.update("1024", tags=["Question", "Talking head"])  # replaces; tags=None or [] removes all

# Up to 500 posts at once, published ones included: add, remove or set (replace)
result = client.tags.apply(post_ids=["1024", "1025"], add=["Question"], remove=["Listicle"])
print(result["data"]["updated"], result["data"]["not_found"])

# Filter by tag (an id or name, or a list: posts with any of them)
client.posts.list(tag="Question")
client.analytics.overview(period="30d", tag=["Question", "Talking head"])

# How each tag did against your normal (default: the last 90 days)
compare = client.analytics.tags(start_date="2026-08-01", end_date="2026-10-31")
for row in compare["data"]["tags"]:
    print(row["tag"]["name"], row["vs_normal"], row["enough_posts"])  # vs_normal 0.38 = 38% above
```

`analytics.tags()` returns `period`, `platform`, `min_posts`, `tags` (comparable tags first, best first; each with `posts`, `measured`, `median_impressions`, `engagement_rate` in percent, `vs_normal` as a fraction, `best_channel` and `enough_posts`), `untagged` (the same numbers for posts without a tag) and `normals` (median impressions per channel). `platform=` keeps one channel's numbers and `min_posts=` (default 5) sets how many measured posts a tag needs before `enough_posts` is true. Every post carries `tags` and `trial_reel` (`{"strategy": "MANUAL" | "SS_PERFORMANCE"}` for an Instagram Trial Reel, else `None`), and so does every entry of `analytics.posts()`. Errors: `404 tag_not_found`, `409 tag_exists` (the existing tag is in `error.body["error"]["tag"]`), `409 tag_limit_reached`, `400 invalid_tag_name`, `invalid_tag_color`, `invalid_tags`, `invalid_post_ids`, `too_many_posts`, `too_many_tags`.

## Accounts

```python
accounts = client.accounts.list()
for account in accounts["data"]:
    print(account["platform"], account["username"], account["status"])
    if account["needs_reconnect"]:
        print("  needs a reconnect:", account.get("reauth_reason"))

account = client.accounts.get("instagram")
```

`status` is `active` or `needs_reconnect` (the token was revoked or expired; Bluesky also when its sign-in could not be renewed). Posts to a `needs_reconnect` account fail until it is reconnected in the OmniSocials app. OmniSocials Connect customer workspaces can also show `pick_pending` (Facebook, Connect customers only: no Page chosen yet).

An X account also carries `x_statistics` (`posts`, `followers`, `post_schedule`, `source`, `billing`, `state`, `paused_reason`): how often OmniSocials reads its X statistics and who pays. `client.accounts.update(account_id, x_statistics={...})` changes it; see [X statistics use credits](#x-statistics-use-credits).

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

The response is not wrapped in `data`. `platform`, `timezone`, `basis`, `grid` and `recommendations` sit at the top level.

```python
best = client.analytics.best_times(platform="instagram", timezone="Europe/Amsterdam")
for slot in best["recommendations"]:
    print(slot["day"], slot["time"], slot["score"])
```

### X statistics use credits

X bills every statistics read, and OmniSocials passes X's price on as credits: half a credit per post check (plus half a credit when the tweet has a video or GIF; each part of a thread counts) and 1 credit per follower count. Every X account carries `x_statistics`:

- `posts`: how often each post is checked. `full` (5 checks: about 5 hours, day 1, 3 and 7, and day 30 for posts with 100+ views), `light` (2 checks: about 5 hours and day 7) or `off`.
- `followers`: how often the follower count is read. `daily`, `weekly` or `off`.
- `source` (`account` or `default`), `billing` (`credits`), `state` (`active`, `paused`, `off`) and `paused_reason` (`insufficient_credits` or null).

When the balance reaches 0 the reads pause (`state` `paused`) and start again by themselves after a top-up; the webhook events `x_statistics.paused` and `x_statistics.resumed` say so. `x_statistics.charging` in the answer of `client.credits.get()` says whether reads are charged yet and from when.

```python
# How often an X account is checked (opt-in scope accounts:write, billing rights)
account = client.accounts.update(
    "1234_x",
    x_statistics={"posts": "light", "followers": "daily"},  # one key or both
)
print(account["data"]["x_statistics"]["state"])

# "Update now": read one post's X numbers now (scope analytics:read)
fresh = client.analytics.refresh_post(9123)
print(fresh["data"]["credits_used"], [t["metrics"] for t in fresh["data"]["tweets"]])

# The balance and what X statistics cost (opt-in scope credits:read, billing rights)
credits = client.credits.get()["data"]
print(credits["balance"], credits["x_statistics"]["total_credits_month"])
```

`analytics.refresh_post` costs nothing when the post was already read that day (UTC) and works at most 5 times a post and 100 times an organisation a day. Errors: `402 insufficient_credits`, `409 refresh_not_available` (no published X tweet), `429 refresh_limit`, `502 refresh_failed` (nothing charged). Because it can cost credits, the SDK retries it only after a 429, never after a 5xx or a timeout. `accounts.update` needs the opt-in scope `accounts:write` and billing rights (manage_billing) for the key's creator, sends only the keys you give, and answers `400 validation_error`, `invalid_value` or `not_supported` (not an X account) and `403 insufficient_permission` (no billing rights for the key's creator). `credits.get` needs the opt-in scope `credits:read` and billing rights. The async client has the same methods.

## Locations (Instagram and Threads location tagging)

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

Threads locations use their own ids (a Facebook Place id is not a Threads location id) and a different response shape: `{"locations": [...]}` on success, or `{"error": {"code", "message"}}` when unavailable. Search by text, or by coordinates instead of `q`, and pass a result's `id` as `threads.location_id` on the post. Threads location tagging is currently rolling out; until Meta approves the permissions it is disabled on production and calls return a clear error.

```python
spots = client.locations.search(platform="threads", q="Blue Bottle Coffee Oakland")
# or around a point: client.locations.search(platform="threads", latitude=37.8115, longitude=-122.2687)

client.posts.create(
    content="Great coffee here",
    channels=["threads"],
    media_urls=["https://example.com/latte.jpg"],
    threads={"location_id": spots["locations"][0]["id"]},
)
```

## Pinterest product tags

Tag products on a Pin so people can shop the items in the image. `client.pinterest.list_products()` returns the product Pins of the connected Pinterest account; pass their `pin_id` values (max 24) as `product_tags` in the `pinterest` options of the post. Only product Pins of your own account can be tagged; products of other merchants cannot. The tags are added right after the Pin is published. A product that Pinterest refuses never fails the post: the outcome is on the post as `pinterest["product_tags_result"]` (`requested`, `tagged`, `skipped`, `error`).

```python
result = client.pinterest.list_products()

if "error" in result:
    # HTTP 200 without "products": pinterest_not_connected,
    # pinterest_catalog_access_required or platform_error
    print(result["error"]["code"], result["error"]["message"])
else:
    product_tags = [product["pin_id"] for product in result["products"][:3]]

    client.posts.create(
        content="Our summer picks",
        channels=["pinterest"],
        media_urls=["https://example.com/summer-look.jpg"],
        scheduled_at="2026-08-01T09:00:00Z",
        pinterest={"board_id": "1234567890", "title": "Summer picks", "product_tags": product_tags},
    )
```

Without `source` the list reads the Pinterest catalog (with `price`, `currency`, `availability` and `item_id`) when the connection has catalog access, else the account's own Pins. Catalog access is given one time in the OmniSocials composer: Pinterest options, Add products, Connect catalog. `source="pins"` scans up to 250 Pins per call, so `products` can be empty while `bookmark` is set; call again with `bookmark=result["bookmark"]`. To check one Pin id or Pin link before you post, call `client.pinterest.validate_product("813744226420795884")`. On `posts.update()` the `pinterest` object replaces the stored one, so leave `product_tags` out to remove the tags.

## Ads

Boost a published post or create a new ad on Meta, Pinterest, TikTok, LinkedIn, X and Google. Boosts and new ads are drafts: your code writes the draft, and the person who pays sees the amount and starts the ad in OmniSocials from the draft's `review_url`. A key starts and raises spend itself only with the opt-in **Start ads** switch (scope `ads:spend`). Without it `ads.activate()`, `ads.activate_multi()`, `ads.resume()`, `ads.drafts.launch()`, a budget raise or any change of a campaign that reached the network through `ads.update()`, and the parity calls that switch something on or raise a budget answer `403 start_in_app`, and the error message names the page where the person does it. Google (`api_draft_only` of `ads.capabilities()`) always stops at the draft, also with `ads:spend`. `ads.pause()` and `ads.delete()` stay open, except on the networks in `api_stop_in_app` (Google), where a campaign that reached the network also answers `403 start_in_app`. Only a paused campaign resumes (`409 not_paused`). The calls that start or raise spend repeat the amount (`confirm_budget_amount`) and are not retried after a 5xx or a timeout, only after a 429, because the first attempt may have started the ad: read the campaign or the draft to see what happened.

The `ads:read` and `ads:write` scopes are opt-in: create the API key with **Ads** switched on (Settings, API). `ads:spend` is the **Start ads** switch under it, offered only to a person with `manage_ads`. A key without a scope it needs gets `403 insufficient_scope`. Ad accounts are connected and picked in the OmniSocials dashboard. Budgets are in major units (10 = 10 EUR) in the ad account's currency: a draft whose `budget["currency"]` differs from the attached ad account's currency answers `400 currency_mismatch`. Ads errors may carry `param`, the field at fault: read it from `exc.body["error"]["param"]` on the raised `APIError` (here `"budget.currency"`). Ad account and campaign ids come back as strings (`"51"`); the methods take an id as a string or a number.

### Create an ad (a draft the person starts)

```python
caps = client.ads.capabilities()
print(caps["data"]["create_networks"], caps["data"]["network_states"])

draft = client.ads.drafts.create(
    name="Autumn sale",
    objective="traffic",
    platforms=["meta", "linkedin"],
    budget={"amount": 10, "currency": "EUR"},
    schedule={"duration_days": 7},
    targeting={"countries": ["NL", "BE"], "automatic_audience": True},
    ads=[
        {
            "media": [{"url": "https://example.com/sale.jpg", "type": "image", "width": 1080, "height": 1350}],
            "primary_text": "30% off everything this week",
            "headline": "Autumn sale",
            "cta": "shop_now",
            "link": "https://example.com/sale",
        }
    ],
)["data"]

# A draft spends nothing. The person checks it and starts it in OmniSocials:
print("Check and start the ad here:", draft["review_url"])
```

With a key that has `ads:spend`, `client.ads.drafts.launch(draft["group_id"], confirm_budget_amount=10)` starts the draft after the person agreed to the amount; Google is skipped with code `start_in_app`. Without `ads:spend` the call answers `403 start_in_app`.

A draft needs no ad account; `client.ads.drafts.attach_account(group_id, platform="meta", ad_account_id="51")` sets one, and `campaigns[].readiness` says what still stops a network. `client.ads.drafts.update(group_id, ...)` replaces the whole draft (HTTP PUT), so send every field again. On Meta an ad can carry a second upright 9:16 file for Stories and Reels: `"placement_media": {"stories_reels": {"url": ..., "type": ...}}`.

### Boost a post

```python
accounts = client.ads.list_accounts()["data"]
meta = next(a for a in accounts if a["platform"] == "meta" and a["is_selected"])

boost = client.ads.boost(
    post_id=12345,
    ad_account_id=meta["id"],
    budget={"type": "daily", "amount": 5, "currency": (meta.get("account_info") or {}).get("currency", "EUR")},
    targeting={"countries": ["NL"]},
)["data"]

# The boost is a draft: the person starts it in OmniSocials.
print(boost["status"])  # "draft"
```

`client.ads.boost_multi()` makes one draft boost per ad account (up to 10, the same budget each). `client.ads.suggestions()` lists posts that do better than your median, `client.ads.overview()` the totals (`totals["spend"]` is `None` when the campaigns use more than one currency: read `totals_by_currency`, one row per currency), and `client.ads.list()`, `get()`, `pause()` and `delete()` manage campaigns. Keyword ideas through the connected Google Ads account: `client.ads.research_keywords(keywords=["running shoes"], country="NL")` and `client.ads.keyword_metrics(keywords=[...])`. The same methods are on `AsyncOmniSocials`.

## Webhooks

Subscribe to `post.scheduled`, `post.published`, `post.failed`, `post.approved`, and `post.rejected` events. `post.approved` fires when the last step of a post's approval workflow is approved, `post.rejected` when an approver rejects the post (it will not publish). These two carry `data["approval"]` with `status`, `decided_by` (the approver's user id) and `reason` (`None` on `post.approved`), and an empty `data["targets"]`. `ad.status_changed` fires when an ad campaign changes status (for example `pending_review` to `active` or `rejected`); its `data` is the campaign, not a post: `campaign_id`, `workspace_id`, `name`, `platform`, `campaign_type`, `status`, `previous_status`, `external_campaign_id` and `budget`. Subscribing to `ad.status_changed` or any other Ads event (`ad.*`, `campaign.*`, `lead.*`, `ads.*`, `ad_rule.*`) needs the `ads:read` scope on the key and `access_ads` for its person (`403 insufficient_scope` / `insufficient_permission`). `x_statistics.paused` and `x_statistics.resumed` fire when the organisation's X statistics stop at 0 credits or start again after a top-up, one delivery per workspace with X; `data` is `{ workspace_id, account_id, reason }` (`reason` is `insufficient_credits` or `credits_added`).

```python
webhook = client.webhooks.create(
    url="https://example.com/hooks/omnisocials",
    events=["post.published", "post.failed"],
)
secret = webhook["data"]["secret"]  # only shown once, store it

client.webhooks.list()
client.webhooks.get(webhook["data"]["id"])
client.webhooks.update(webhook["data"]["id"], is_active=False)
client.webhooks.rotate_secret(webhook["data"]["id"])  # new secret, shown once; the old one signs for 24 hours more
client.webhooks.delete(webhook["data"]["id"])
```

Every webhook carries `workspace_id`. `list` and `get` also return the organisation-wide webhooks of the key's organisation (`workspace_id` `None`, made in the OmniSocials dashboard; they receive the events of every workspace), and `update`, `delete` and `rotate_secret` work on them too. Webhooks you create through the API belong to the key's workspace. When the person behind a webhook loses access to the organisation or workspace, OmniSocials switches the webhook off: `is_active` is `False` and `last_failure["error"]` says why. `update(id, is_active=True)` switches it on again.

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
    elif event["type"] == "post.rejected":
        print("Rejected:", event["data"]["post_id"], event["data"]["approval"]["reason"])
    return {"ok": True}
```

`verify_webhook_signature` uses a constant-time comparison, rejects timestamps older than `tolerance` seconds (default 300) to block replays, and returns the parsed event dict on success. Respond with any 2xx within 10 seconds to acknowledge; deliveries are retried up to 3 times.

### Rotate the secret without missing deliveries

For 24 hours after `rotate_secret`, every delivery carries two headers: `X-OmniSocials-Signature`, signed with the new secret, and `X-OmniSocials-Signature-Previous`, signed with the old secret (same format, same timestamp and body). Verify the first with the new secret and, when that fails, the second with the old one:

```python
def verify_delivery(payload, headers):
    try:
        return verify_webhook_signature(
            payload, headers.get("X-OmniSocials-Signature"), NEW_WEBHOOK_SECRET
        )
    except WebhookVerificationError:
        previous = headers.get("X-OmniSocials-Signature-Previous")
        if not previous:
            raise
        return verify_webhook_signature(payload, previous, OLD_WEBHOOK_SECRET)
```

Rotating again within the 24 hours replaces the previous secret with the one you just rotated out.

## Limits and feature requests

`client.limits.list()` lists what OmniSocials cannot do, why (`says`) and what to do instead (`instead`): platform rules, features not built yet, features that work in the OmniSocials app only. Read it before you tell a person that something is not possible. When the person still wants a `requestable` entry, send a feature request with its `limit_id`. The request is stored for the person who owns the key; they see it in OmniSocials (Settings, Request a feature) and get an email when its status changes. Works with every key, no scope needed.

```python
from omnisocials import APIError

limits = client.limits.list(platform="telegram")  # area="posts" | "inbox" | ...
for limit in limits["data"]:
    print(limit["id"], limit["says"], limit["instead"], limit["requestable"])

try:
    result = client.feature_requests.create(
        summary="Post our daily update to the Announcements topic of our Telegram group, not to the whole group.",
        platform="telegram",
        limit_id="telegram.forum_topics",
    )
    # "created" (new), "voted" (added a vote to your organisation's open request)
    # or "already_requested" (you asked before; data is that request)
    print(result["outcome"], result["data"]["id"], result["data"]["status"])
except APIError as exc:
    if exc.code != "not_requestable":
        raise
    # A platform rule or a choice of OmniSocials: nothing was stored.
    limit = exc.body["error"]["limit"]
    print(limit["says"], limit["instead"])

mine = client.feature_requests.list()  # newest first, at most 50
one = client.feature_requests.get(mine["data"][0]["id"])  # status, team_answer, team_replies
```

A limit is `{"id", "kind", "kind_label", "area", "platforms", "title", "says", "instead", "requestable"}`; `kind` is `platform`, `by_design`, `not_built`, `beta`, `dashboard_only` or `needs_setup`, and `requestable` is False for `platform` and `by_design`. `limits.list()` also returns `kinds` (a label per kind). A request carries `status` (`open`, `in_progress`, `completed`, `declined`), `votes_count`, `team_answer` and `team_replies`. `summary` is 10 to 1000 characters (what the person wants to do and why), `title=` at most 120 (made from the summary when left out); `area=` is one of posts, media, inbox, analytics, automations, accounts, ads, team, other. Errors: `400 invalid_summary` / `invalid_title` / `invalid_platform` / `invalid_area` / `unknown_limit`, `409 not_requestable` (the entry is in `exc.body["error"]["limit"]`), `429 too_many_requests` (10 an hour per person), and `400 invalid_id` / `404 not_found` on `get`. The async client has the same methods.

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

The SDK automatically retries on 429, 5xx, and connection errors with exponential backoff (0.5s, 1s, 2s, with jitter), honoring the `Retry-After` header when present. Other 4xx errors are never retried. The ads calls that start or raise spend retry a 429 only (see [Ads](#ads)). Defaults: 2 retries, 30 second timeout. Both are configurable:

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
