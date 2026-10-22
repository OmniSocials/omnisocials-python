"""Posts resource: create, schedule, publish, update, and list posts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Union

from .._utils import NOT_GIVEN, NotGiven, drop_none, join_list

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Posts", "AsyncPosts"]

# `content` is a plain string, or a per-platform mapping with a `default` key.
ContentType = Union[str, Mapping[str, str]]
# One `media_ids` / `media_urls` entry: a plain string, or a mapping with an
# `alt` accessibility description (max 1500 chars), e.g.
# `{"url": "https://...", "alt": "..."}` for media_urls or
# `{"id": "...", "alt": "..."}` for media_ids. Alt text is delivered to
# Mastodon (media description), Bluesky (embed alt), X (photos/GIFs),
# Pinterest (pin alt text), Instagram (images), and LinkedIn (images).
# The same entry shape works inside x/bluesky/mastodon/threads `thread_parts` media.
MediaEntryType = Union[str, Mapping[str, str]]
# `media_ids` / `media_urls` are a flat list, or a per-platform mapping.
MediaMapType = Union[Sequence[MediaEntryType], Mapping[str, Sequence[MediaEntryType]]]


def _create_body(
    *,
    content: ContentType,
    channels: Optional[Sequence[str]],
    scheduled_at: Optional[str],
    media_ids: Optional[MediaMapType],
    media_urls: Optional[MediaMapType],
    type: Optional[str],
    source: Optional[str],
    link_url: Optional[str],
    link_title: Optional[str],
    link_description: Optional[str],
    link_thumbnail_url: Optional[str],
    location_id: Optional[str],
    collaborators: Optional[Sequence[str]],
    user_tags: Optional[Sequence[Mapping[str, Any]]],
    hashtag_set: Optional[str],
    hashtag_set_id: Optional[str],
    hashtag_placement: Optional[str],
    hashtag_platforms: Optional[Sequence[str]],
    approval_workflow_id: Optional[str] = None,
    draft: Optional[bool] = None,
    media_fit: Optional[Mapping[str, str]] = None,
    pinterest: Optional[Mapping[str, Any]],
    youtube: Optional[Mapping[str, Any]],
    instagram: Optional[Mapping[str, Any]],
    facebook: Optional[Mapping[str, Any]],
    linkedin: Optional[Mapping[str, Any]],
    linkedin_page: Optional[Mapping[str, Any]],
    tiktok: Optional[Mapping[str, Any]],
    x: Optional[Mapping[str, Any]],
    bluesky: Optional[Mapping[str, Any]],
    mastodon: Optional[Mapping[str, Any]],
    threads: Optional[Mapping[str, Any]],
    google_business: Optional[Mapping[str, Any]],
    telegram: Optional[Mapping[str, Any]] = None,
    discord: Optional[Mapping[str, Any]] = None,
    linkedin_poll: Optional[Mapping[str, Any]],
    video_cover: Optional[Mapping[str, Any]] = None,
    comment_dm_automation: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return drop_none(
        {
            "content": content,
            "channels": channels,
            "scheduled_at": scheduled_at,
            "media_ids": media_ids,
            "media_urls": media_urls,
            "type": type,
            "source": source,
            "link_url": link_url,
            "link_title": link_title,
            "link_description": link_description,
            "link_thumbnail_url": link_thumbnail_url,
            "location_id": location_id,
            "collaborators": collaborators,
            "user_tags": user_tags,
            "hashtag_set": hashtag_set,
            "hashtag_set_id": hashtag_set_id,
            "hashtag_placement": hashtag_placement,
            "hashtag_platforms": hashtag_platforms,
            "approval_workflow_id": approval_workflow_id,
            "draft": draft,
            "media_fit": media_fit,
            "pinterest": pinterest,
            "youtube": youtube,
            "instagram": instagram,
            "facebook": facebook,
            "linkedin": linkedin,
            "linkedin_page": linkedin_page,
            "tiktok": tiktok,
            "x": x,
            "bluesky": bluesky,
            "mastodon": mastodon,
            "threads": threads,
            "google_business": google_business,
            "telegram": telegram,
            "discord": discord,
            "linkedin_poll": linkedin_poll,
            "video_cover": video_cover,
            "comment_dm_automation": comment_dm_automation,
        }
    )


def _update_body(
    *,
    content: Optional[ContentType],
    scheduled_at: Optional[str],
    channels: Optional[Sequence[str]],
    media_ids: Optional[MediaMapType],
    media_urls: Optional[MediaMapType],
    type: Optional[str],
    location_id: Optional[str],
    collaborators: Optional[Sequence[str]],
    user_tags: Optional[Sequence[Mapping[str, Any]]],
    pinterest: Optional[Mapping[str, Any]],
    youtube: Optional[Mapping[str, Any]],
    instagram: Optional[Mapping[str, Any]],
    facebook: Optional[Mapping[str, Any]],
    linkedin: Optional[Mapping[str, Any]],
    linkedin_page: Optional[Mapping[str, Any]],
    tiktok: Optional[Mapping[str, Any]],
    x: Optional[Mapping[str, Any]],
    bluesky: Optional[Mapping[str, Any]],
    mastodon: Optional[Mapping[str, Any]],
    threads: Optional[Mapping[str, Any]],
    google_business: Optional[Mapping[str, Any]],
    telegram: Optional[Mapping[str, Any]] = None,
    discord: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
    linkedin_poll: Optional[Mapping[str, Any]],
    video_cover: Optional[Mapping[str, Any]] = None,
    draft: Optional[bool] = None,
    media_fit: Optional[Mapping[str, str]] = None,
    comment_dm_automation: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
) -> Dict[str, Any]:
    body = drop_none(
        {
            "content": content,
            "scheduled_at": scheduled_at,
            "draft": draft,
            "media_fit": media_fit,
            "channels": channels,
            "media_ids": media_ids,
            "media_urls": media_urls,
            "type": type,
            "location_id": location_id,
            "collaborators": collaborators,
            "user_tags": user_tags,
            "pinterest": pinterest,
            "youtube": youtube,
            "instagram": instagram,
            "facebook": facebook,
            "linkedin": linkedin,
            "linkedin_page": linkedin_page,
            "tiktok": tiktok,
            "x": x,
            "bluesky": bluesky,
            "mastodon": mastodon,
            "threads": threads,
            "google_business": google_business,
            "telegram": telegram,
            "linkedin_poll": linkedin_poll,
            "video_cover": video_cover,
        }
    )
    # An explicit None removes the post's automation, so it must survive
    # drop_none; NOT_GIVEN (the default) leaves it untouched.
    if not isinstance(comment_dm_automation, NotGiven):
        body["comment_dm_automation"] = comment_dm_automation
    # Same for discord: an explicit None removes every Discord option.
    if not isinstance(discord, NotGiven):
        body["discord"] = discord
    return body


class Posts:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /posts`` - list posts (status: draft, in_approval, scheduled, posting, posted, failed, warning; in_approval = waiting for a reviewer in an approval workflow)."""
        return self._client.request(
            "GET", "/posts", query={"status": status, "limit": limit, "offset": offset}
        )

    def get(self, post_id: str) -> Any:
        """``GET /posts/{id}`` - fetch a single post."""
        return self._client.request("GET", f"/posts/{post_id}")

    def recent_platform(
        self,
        *,
        limit: Optional[int] = None,
        platforms: Optional[Union[str, Sequence[str]]] = None,
    ) -> Any:
        """``GET /posts/recent-platform`` - recent posts fetched live from the
        connected platform APIs (including content published outside
        OmniSocials). Requires the analytics:read scope."""
        return self._client.request(
            "GET",
            "/posts/recent-platform",
            query={"limit": limit, "platforms": join_list(platforms)},
        )

    def create(
        self,
        *,
        content: ContentType,
        channels: Optional[Sequence[str]] = None,
        scheduled_at: Optional[str] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        source: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None,
        link_thumbnail_url: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        hashtag_set: Optional[str] = None,
        hashtag_set_id: Optional[str] = None,
        hashtag_placement: Optional[str] = None,
        hashtag_platforms: Optional[Sequence[str]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Optional[Mapping[str, Any]] = None,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        approval_workflow_id: Optional[str] = None,
        draft: Optional[bool] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create`` - create a post (draft, or scheduled when
        ``scheduled_at`` is set).

        ``draft=True`` with ``scheduled_at`` stores a planned draft: the post
        is ``draft`` and keeps that time, shows on the dashboard calendar at
        that slot with a dashed outline, and the scheduler never publishes it.
        A person schedules it from the composer, or you do with
        :meth:`update` and ``draft=False``. Use it when an agent proposes a
        slot that a human should confirm. Not allowed with ``publish_now`` or
        ``approval_workflow_id`` (``400 validation_error``). Without
        ``scheduled_at`` it changes nothing.

        ``approval_workflow_id`` (a workflow id from
        ``client.approval_workflows.list()``) routes the post through a saved
        approval workflow: it is created as ``in_approval``
        (``approval_status: "pending"``) instead of ``scheduled``, the
        approvers are notified, and it publishes at ``scheduled_at`` once the
        last step approves. Requires ``scheduled_at``; not allowed with
        ``publish_now``. Errors: ``404 workflow_not_found``,
        ``400 validation_error``.

        ``hashtag_set`` (set name, case-insensitive) or ``hashtag_set_id``
        applies a saved hashtag set once at create time; tags already in a
        caption are skipped; Instagram's 30-hashtag cap returns error code
        ``hashtag_limit_exceeded``. ``hashtag_placement`` is
        ``"caption_append"`` (default) or ``"first_comment"``;
        ``hashtag_platforms`` restricts the tags to a subset of ``channels``.

        ``pinterest["product_tags"]`` tags products on the Pin: up to 24
        product Pins of the connected Pinterest account, each as a Pin id
        string (see ``client.pinterest.list_products()``) or a Pin link.
        Products of other merchants cannot be tagged. The tags are added
        right after the Pin is published; a product Pinterest refuses never
        fails the post, and the outcome is returned on the post as
        ``pinterest["product_tags_result"]`` (``requested``, ``tagged``,
        ``skipped``, ``error``). More than 24 entries or an invalid entry
        returns ``400 validation_error``.

        When the post targets X and its text (or any thread part) contains a
        URL, the response includes a top-level ``warnings`` list (sibling of
        ``data``) with a ``x_url_post_credits`` entry carrying
        ``credits_required`` and ``credits_balance``: X's link-post fee is
        passed through as prepaid credits, debited at publish time (from
        2026-08-14). Credits are managed in the dashboard, not the API.

        From 2026-08-14, scheduling an X link post also reserves its credit
        cost up front: if that reservation would push the company's total
        reserved credits (across every scheduled X link post) past its
        balance, the request is rejected before it's accepted, with
        ``402 x_credits_insufficient`` (``error.details`` carries
        ``credits_required``, ``credits_balance``, and
        ``credits_reserved``). Drafts (no ``scheduled_at``) are never gated,
        and posts publishing before 2026-08-14 are never gated.

        ``media_fit`` is the image fit per channel for feed images whose
        ratio is outside what a channel shows uncropped: a mapping of
        platform id (``"instagram"``, ``"pinterest"``, ...) to ``"auto"``,
        ``"crop"`` or ``"keep"``. ``auto`` (default): Instagram crops a tall
        or wide image to 4:5 / 1.91:1 around the subject (Instagram cuts it
        to that window anyway and Meta cannot boost a feed post outside it);
        Pinterest keeps a Pin taller than 2:3 and reports it. ``crop`` /
        ``keep`` force it per channel. Every decision comes back in the same
        ``warnings`` list with ``code: "image_fit"`` (``action`` is
        ``cropped``, ``kept`` or ``crop_failed``, with ``platform``,
        ``media_url``, ``ratio``, ``target`` and ``crop_url``).

        ``telegram`` holds the Telegram options (the connected channel or
        group, posted by the OmniSocials bot): ``silent``, ``link_preview``,
        ``pin``, ``protect_content``, ``spoiler``, ``caption_above_media``
        (booleans), up to 3 ``buttons`` (``{"text", "url"}``, not on an album
        or a poll), a native ``poll`` (``{"options": 2 to 12 of up to 100
        characters, "open_period": 5 to 2628000 seconds, "multiple"}``; the
        post text is the question, max 300 characters, no media) and
        ``first_comment`` (a reply under the post). Text up to 4,096
        characters; with media, text over 1,024 characters is sent as a reply
        under the media. No Stories. Once sent, ``data["telegram"]["result"]``
        carries the message ids and the links.

        ``discord`` holds the Discord options (one Discord channel, posted
        through its incoming webhook with the webhook's name and picture):
        ``silent``, ``link_preview`` (default on), ``allow_mentions`` (default
        off: @everyone, @here, role and user mentions show as text and ping
        nobody), ``spoiler`` (booleans), ``thread_name`` (the post title in a
        forum or media channel, 1 to 100 characters; on a text channel the
        post goes out without it), up to 5 ``buttons`` (``{"text": 1 to 80 characters, "url":
        https:// or http://}``, one row, not with a poll) and a native
        ``poll`` (``{"options": 2 to 10 of up to 55 characters,
        "duration_hours": 1 to 768 (default 24), "multiple"}``; the post text
        is the question, max 300 characters, no media and no buttons). Text
        up to 2,000 characters; up to 10 images, GIFs and videos per message,
        a video or GIF over 20 MB is sent as a link in the text. No Stories.
        Once sent, ``data["discord"]["result"]`` carries the message id and
        the link.

        ``comment_dm_automation`` binds a comment-to-DM automation to the
        post (Instagram or Facebook must be in ``channels``): a keyword in a
        comment is answered with a DM, once per person, with an optional
        public reply under the comment. Shape: ``{"trigger": {"keywords":
        ["guide"], "match": "word"}, "actions": {"dm": {"text": "..."},
        "public_reply": {"enabled": True, "variations": [...]}}, "limits":
        {"max_sends": 500}, "platforms": ["instagram", "facebook"]}`` (see
        ``client.automations.create()`` for the fields). ``platforms`` makes
        one automation per listed channel; each must be a channel of the
        post. Without it: Instagram when the post goes there, else Facebook.
        Needs the ``automations:write`` scope on the key (``403
        insufficient_scope``, checked before anything else); a bad object is
        a ``400 validation_error`` whose message starts with
        ``comment_dm_automation: ``. The response then carries
        ``data["comment_dm_automation"]`` (the first automation, with
        ``post`` ``None``, plus ``platforms`` and ``automations``, one
        ``{"id", "platform", "status"}`` per channel); each starts listening
        once the post is live on its channel.
        """
        body = _create_body(
            content=content,
            channels=channels,
            scheduled_at=scheduled_at,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            source=source,
            link_url=link_url,
            link_title=link_title,
            link_description=link_description,
            link_thumbnail_url=link_thumbnail_url,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            hashtag_set=hashtag_set,
            hashtag_set_id=hashtag_set_id,
            hashtag_placement=hashtag_placement,
            hashtag_platforms=hashtag_platforms,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            approval_workflow_id=approval_workflow_id,
            draft=draft,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return self._client.request("POST", "/posts/create", json=body)

    def create_and_publish(
        self,
        *,
        content: ContentType,
        channels: Optional[Sequence[str]] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        source: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None,
        link_thumbnail_url: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        hashtag_set: Optional[str] = None,
        hashtag_set_id: Optional[str] = None,
        hashtag_placement: Optional[str] = None,
        hashtag_platforms: Optional[Sequence[str]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Optional[Mapping[str, Any]] = None,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create-and-publish`` - create and publish immediately.

        See :meth:`create` for the ``warnings`` list on X link posts, the
        ``image_fit`` entries steered by ``media_fit`` and
        ``comment_dm_automation``.
        """
        body = _create_body(
            content=content,
            channels=channels,
            scheduled_at=None,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            source=source,
            link_url=link_url,
            link_title=link_title,
            link_description=link_description,
            link_thumbnail_url=link_thumbnail_url,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            hashtag_set=hashtag_set,
            hashtag_set_id=hashtag_set_id,
            hashtag_placement=hashtag_placement,
            hashtag_platforms=hashtag_platforms,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return self._client.request("POST", "/posts/create-and-publish", json=body)

    def update(
        self,
        post_id: str,
        *,
        content: Optional[ContentType] = None,
        scheduled_at: Optional[str] = None,
        channels: Optional[Sequence[str]] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        draft: Optional[bool] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /posts/{id}`` - update a draft or scheduled post.

        ``draft=False`` without ``scheduled_at`` schedules a planned draft at
        the ``scheduled_at`` it already carries (``400 validation_error`` when
        it has none or it is in the past). ``draft=True`` without
        ``scheduled_at`` unschedules a scheduled post: it keeps its time and
        stays on the calendar as a dashed draft, nothing publishes; a post
        waiting for approval leaves its workflow. ``draft=True`` with
        ``scheduled_at`` moves the time and keeps (or makes) the post a draft.

        ``media_fit`` (same shape as on :meth:`create`) alone re-decides the
        stored images: ``"keep"`` gives the original back, ``"crop"`` crops
        an image that was kept. Like :meth:`create`, the response can carry a
        top-level ``warnings`` list with ``image_fit`` entries when the update
        changes the images or ``media_fit``.

        Only top-level ``None`` values are dropped from the body, so passing
        e.g. ``x={"thread_parts": None}`` still clears an X thread (reverts
        the post to single-tweet mode). The same applies to ``bluesky``,
        ``mastodon`` and ``threads`` thread parts.

        ``pinterest`` replaces the stored Pinterest options wholesale, so
        leave ``product_tags`` out (or send ``[]``) to remove the product
        tags.

        Updating a scheduled X link post is subject to the same schedule-time
        credit gate as :meth:`create`: if the update would push the
        company's total reserved credits (across every scheduled X link
        post) past its balance, the request is rejected with
        ``402 x_credits_insufficient`` before anything changes.

        ``comment_dm_automation`` (same shape as on :meth:`create`) as a
        mapping replaces the post's comment-to-DM automations (a channel no
        longer in ``platforms`` loses its automation), an explicit ``None``
        removes them all, and leaving it out keeps them. Needs the
        ``automations:write`` scope.

        ``discord`` merges into the stored Discord options: a key set to
        ``None`` removes that option (e.g. ``discord={"poll": None}``), an
        explicit ``discord=None`` removes every option, and leaving it out
        keeps them.
        """
        body = _update_body(
            content=content,
            scheduled_at=scheduled_at,
            channels=channels,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            draft=draft,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return self._client.request("PATCH", f"/posts/{post_id}", json=body)

    def delete(self, post_id: str) -> None:
        """``DELETE /posts/{id}`` - remove a post from OmniSocials (the live post stays on the platform). Returns ``None`` (204)."""
        return self._client.request("DELETE", f"/posts/{post_id}")

    def publish(self, post_id: str) -> Any:
        """``POST /posts/{id}/publish`` - publish a draft or scheduled post now.

        Publishing an X link post is subject to the same schedule-time
        credit gate as :meth:`create` (``402 x_credits_insufficient`` when
        the reservation would exceed the company's credit balance).
        """
        return self._client.request("POST", f"/posts/{post_id}/publish")

    def retry(self, post_id: str) -> Any:
        """``POST /posts/{id}/retry`` - retry the failed platforms of a
        ``failed`` or ``warning`` (partially failed) post, on the same post.

        Only the platforms that failed are re-published; platforms that
        already succeeded are never posted again. Asynchronous: a 200 means
        the retry is queued - poll ``get`` for the outcome. Max 3 retries per
        platform.
        """
        return self._client.request("POST", f"/posts/{post_id}/retry")

    def approve(self, post_id: str) -> Any:
        """``POST /posts/{id}/approve`` - approve the current step of a
        post's approval workflow, on behalf of the user who owns this API
        key. That user must be a listed approver for the workflow's CURRENT
        step - steps approve in order, so an approver on a later step gets
        a 403 ``forbidden`` error until earlier steps clear. Only works on a
        post with ``approval_status: "pending"``. If this is the last step,
        the post finalizes immediately (``scheduled`` or ``posting``);
        otherwise it stays ``in_approval`` and the next step's approvers are
        notified.
        """
        return self._client.request("POST", f"/posts/{post_id}/approve")

    def reject(self, post_id: str, comment: Optional[str] = None) -> Any:
        """``POST /posts/{id}/reject`` - reject a post's approval workflow,
        on behalf of the user who owns this API key. Same approver
        requirement as :meth:`approve`. Unlike approval, a rejection stops
        the WHOLE workflow immediately (not just the current step) - the
        post's status becomes ``rejected``. ``comment`` is optional and,
        when given, is shown to the requester and other approvers in the
        post's review thread.
        """
        body = {"comment": comment} if comment else None
        return self._client.request("POST", f"/posts/{post_id}/reject", json=body)

    def get_approval(self, post_id: str) -> Any:
        """``GET /posts/{id}/approval`` - the approval review of a post:
        every step with its approvers and their decisions, the rejection
        with its reason, and the comment thread. Use it when
        ``approval_status`` is ``rejected`` to learn who rejected the post
        and why, or while it is ``pending`` to see who the post waits for.

        ``data`` carries ``post_id``, ``status`` (``none``, ``pending``,
        ``approved``, ``rejected``), ``workflow``, ``requested_by``,
        ``requested_at``, ``current_step``, ``steps``, ``rejection`` and
        ``comments`` (oldest first). A post without an approval workflow
        returns ``status: "none"`` with the object fields ``None`` and
        empty ``steps`` and ``comments``. Read-only; requires the
        ``posts:read`` scope.
        """
        return self._client.request("GET", f"/posts/{post_id}/approval")


class AsyncPosts:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        *,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /posts`` - list posts (status: draft, in_approval, scheduled, posting, posted, failed, warning; in_approval = waiting for a reviewer in an approval workflow)."""
        return await self._client.request(
            "GET", "/posts", query={"status": status, "limit": limit, "offset": offset}
        )

    async def get(self, post_id: str) -> Any:
        """``GET /posts/{id}`` - fetch a single post."""
        return await self._client.request("GET", f"/posts/{post_id}")

    async def recent_platform(
        self,
        *,
        limit: Optional[int] = None,
        platforms: Optional[Union[str, Sequence[str]]] = None,
    ) -> Any:
        """``GET /posts/recent-platform`` - recent posts fetched live from the
        connected platform APIs. Requires the analytics:read scope."""
        return await self._client.request(
            "GET",
            "/posts/recent-platform",
            query={"limit": limit, "platforms": join_list(platforms)},
        )

    async def create(
        self,
        *,
        content: ContentType,
        channels: Optional[Sequence[str]] = None,
        scheduled_at: Optional[str] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        source: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None,
        link_thumbnail_url: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        hashtag_set: Optional[str] = None,
        hashtag_set_id: Optional[str] = None,
        hashtag_placement: Optional[str] = None,
        hashtag_platforms: Optional[Sequence[str]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Optional[Mapping[str, Any]] = None,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        approval_workflow_id: Optional[str] = None,
        draft: Optional[bool] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create`` - create a post (draft, or scheduled when
        ``scheduled_at`` is set).

        ``draft=True`` with ``scheduled_at`` stores a planned draft: the post
        is ``draft`` and keeps that time, shows on the dashboard calendar at
        that slot with a dashed outline, and the scheduler never publishes it.
        A person schedules it from the composer, or you do with
        :meth:`update` and ``draft=False``. Use it when an agent proposes a
        slot that a human should confirm. Not allowed with ``publish_now`` or
        ``approval_workflow_id`` (``400 validation_error``). Without
        ``scheduled_at`` it changes nothing.

        ``approval_workflow_id`` (a workflow id from
        ``client.approval_workflows.list()``) routes the post through a saved
        approval workflow: it is created as ``in_approval``
        (``approval_status: "pending"``) instead of ``scheduled``, the
        approvers are notified, and it publishes at ``scheduled_at`` once the
        last step approves. Requires ``scheduled_at``; not allowed with
        ``publish_now``. Errors: ``404 workflow_not_found``,
        ``400 validation_error``.

        ``hashtag_set`` (set name, case-insensitive) or ``hashtag_set_id``
        applies a saved hashtag set once at create time; tags already in a
        caption are skipped; Instagram's 30-hashtag cap returns error code
        ``hashtag_limit_exceeded``. ``hashtag_placement`` is
        ``"caption_append"`` (default) or ``"first_comment"``;
        ``hashtag_platforms`` restricts the tags to a subset of ``channels``.

        ``pinterest["product_tags"]`` tags products on the Pin: up to 24
        product Pins of the connected Pinterest account, each as a Pin id
        string (see ``client.pinterest.list_products()``) or a Pin link.
        Products of other merchants cannot be tagged. The tags are added
        right after the Pin is published; a product Pinterest refuses never
        fails the post, and the outcome is returned on the post as
        ``pinterest["product_tags_result"]`` (``requested``, ``tagged``,
        ``skipped``, ``error``). More than 24 entries or an invalid entry
        returns ``400 validation_error``.

        When the post targets X and its text (or any thread part) contains a
        URL, the response includes a top-level ``warnings`` list (sibling of
        ``data``) with a ``x_url_post_credits`` entry carrying
        ``credits_required`` and ``credits_balance``: X's link-post fee is
        passed through as prepaid credits, debited at publish time (from
        2026-08-14). Credits are managed in the dashboard, not the API.

        From 2026-08-14, scheduling an X link post also reserves its credit
        cost up front: if that reservation would push the company's total
        reserved credits (across every scheduled X link post) past its
        balance, the request is rejected before it's accepted, with
        ``402 x_credits_insufficient`` (``error.details`` carries
        ``credits_required``, ``credits_balance``, and
        ``credits_reserved``). Drafts (no ``scheduled_at``) are never gated,
        and posts publishing before 2026-08-14 are never gated.

        ``media_fit`` is the image fit per channel for feed images whose
        ratio is outside what a channel shows uncropped: a mapping of
        platform id (``"instagram"``, ``"pinterest"``, ...) to ``"auto"``,
        ``"crop"`` or ``"keep"``. ``auto`` (default): Instagram crops a tall
        or wide image to 4:5 / 1.91:1 around the subject (Instagram cuts it
        to that window anyway and Meta cannot boost a feed post outside it);
        Pinterest keeps a Pin taller than 2:3 and reports it. ``crop`` /
        ``keep`` force it per channel. Every decision comes back in the same
        ``warnings`` list with ``code: "image_fit"`` (``action`` is
        ``cropped``, ``kept`` or ``crop_failed``, with ``platform``,
        ``media_url``, ``ratio``, ``target`` and ``crop_url``).

        ``telegram`` holds the Telegram options (the connected channel or
        group, posted by the OmniSocials bot): ``silent``, ``link_preview``,
        ``pin``, ``protect_content``, ``spoiler``, ``caption_above_media``
        (booleans), up to 3 ``buttons`` (``{"text", "url"}``, not on an album
        or a poll), a native ``poll`` (``{"options": 2 to 12 of up to 100
        characters, "open_period": 5 to 2628000 seconds, "multiple"}``; the
        post text is the question, max 300 characters, no media) and
        ``first_comment`` (a reply under the post). Text up to 4,096
        characters; with media, text over 1,024 characters is sent as a reply
        under the media. No Stories. Once sent, ``data["telegram"]["result"]``
        carries the message ids and the links.

        ``discord`` holds the Discord options (one Discord channel, posted
        through its incoming webhook with the webhook's name and picture):
        ``silent``, ``link_preview`` (default on), ``allow_mentions`` (default
        off: @everyone, @here, role and user mentions show as text and ping
        nobody), ``spoiler`` (booleans), ``thread_name`` (the post title in a
        forum or media channel, 1 to 100 characters; on a text channel the
        post goes out without it), up to 5 ``buttons`` (``{"text": 1 to 80 characters, "url":
        https:// or http://}``, one row, not with a poll) and a native
        ``poll`` (``{"options": 2 to 10 of up to 55 characters,
        "duration_hours": 1 to 768 (default 24), "multiple"}``; the post text
        is the question, max 300 characters, no media and no buttons). Text
        up to 2,000 characters; up to 10 images, GIFs and videos per message,
        a video or GIF over 20 MB is sent as a link in the text. No Stories.
        Once sent, ``data["discord"]["result"]`` carries the message id and
        the link.

        ``comment_dm_automation`` binds a comment-to-DM automation to the
        post (Instagram or Facebook must be in ``channels``): a keyword in a
        comment is answered with a DM, once per person, with an optional
        public reply under the comment. Shape: ``{"trigger": {"keywords":
        ["guide"], "match": "word"}, "actions": {"dm": {"text": "..."},
        "public_reply": {"enabled": True, "variations": [...]}}, "limits":
        {"max_sends": 500}, "platforms": ["instagram", "facebook"]}`` (see
        ``client.automations.create()`` for the fields). ``platforms`` makes
        one automation per listed channel; each must be a channel of the
        post. Without it: Instagram when the post goes there, else Facebook.
        Needs the ``automations:write`` scope on the key (``403
        insufficient_scope``, checked before anything else); a bad object is
        a ``400 validation_error`` whose message starts with
        ``comment_dm_automation: ``. The response then carries
        ``data["comment_dm_automation"]`` (the first automation, with
        ``post`` ``None``, plus ``platforms`` and ``automations``, one
        ``{"id", "platform", "status"}`` per channel); each starts listening
        once the post is live on its channel.
        """
        body = _create_body(
            content=content,
            channels=channels,
            scheduled_at=scheduled_at,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            source=source,
            link_url=link_url,
            link_title=link_title,
            link_description=link_description,
            link_thumbnail_url=link_thumbnail_url,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            hashtag_set=hashtag_set,
            hashtag_set_id=hashtag_set_id,
            hashtag_placement=hashtag_placement,
            hashtag_platforms=hashtag_platforms,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            approval_workflow_id=approval_workflow_id,
            draft=draft,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return await self._client.request("POST", "/posts/create", json=body)

    async def create_and_publish(
        self,
        *,
        content: ContentType,
        channels: Optional[Sequence[str]] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        source: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None,
        link_thumbnail_url: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        hashtag_set: Optional[str] = None,
        hashtag_set_id: Optional[str] = None,
        hashtag_placement: Optional[str] = None,
        hashtag_platforms: Optional[Sequence[str]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Optional[Mapping[str, Any]] = None,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create-and-publish`` - create and publish immediately.

        See :meth:`create` for the ``warnings`` list on X link posts, the
        ``image_fit`` entries steered by ``media_fit`` and
        ``comment_dm_automation``.
        """
        body = _create_body(
            content=content,
            channels=channels,
            scheduled_at=None,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            source=source,
            link_url=link_url,
            link_title=link_title,
            link_description=link_description,
            link_thumbnail_url=link_thumbnail_url,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            hashtag_set=hashtag_set,
            hashtag_set_id=hashtag_set_id,
            hashtag_placement=hashtag_placement,
            hashtag_platforms=hashtag_platforms,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return await self._client.request(
            "POST", "/posts/create-and-publish", json=body
        )

    async def update(
        self,
        post_id: str,
        *,
        content: Optional[ContentType] = None,
        scheduled_at: Optional[str] = None,
        channels: Optional[Sequence[str]] = None,
        media_ids: Optional[MediaMapType] = None,
        media_urls: Optional[MediaMapType] = None,
        type: Optional[str] = None,
        location_id: Optional[str] = None,
        collaborators: Optional[Sequence[str]] = None,
        user_tags: Optional[Sequence[Mapping[str, Any]]] = None,
        pinterest: Optional[Mapping[str, Any]] = None,
        youtube: Optional[Mapping[str, Any]] = None,
        instagram: Optional[Mapping[str, Any]] = None,
        facebook: Optional[Mapping[str, Any]] = None,
        linkedin: Optional[Mapping[str, Any]] = None,
        linkedin_page: Optional[Mapping[str, Any]] = None,
        tiktok: Optional[Mapping[str, Any]] = None,
        x: Optional[Mapping[str, Any]] = None,
        bluesky: Optional[Mapping[str, Any]] = None,
        mastodon: Optional[Mapping[str, Any]] = None,
        threads: Optional[Mapping[str, Any]] = None,
        google_business: Optional[Mapping[str, Any]] = None,
        telegram: Optional[Mapping[str, Any]] = None,
        discord: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
        linkedin_poll: Optional[Mapping[str, Any]] = None,
        video_cover: Optional[Mapping[str, Any]] = None,
        draft: Optional[bool] = None,
        media_fit: Optional[Mapping[str, str]] = None,
        comment_dm_automation: Union[Mapping[str, Any], None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /posts/{id}`` - update a draft or scheduled post.

        ``draft=False`` without ``scheduled_at`` schedules a planned draft at
        the ``scheduled_at`` it already carries (``400 validation_error`` when
        it has none or it is in the past). ``draft=True`` without
        ``scheduled_at`` unschedules a scheduled post: it keeps its time and
        stays on the calendar as a dashed draft, nothing publishes; a post
        waiting for approval leaves its workflow. ``draft=True`` with
        ``scheduled_at`` moves the time and keeps (or makes) the post a draft.

        ``media_fit`` (same shape as on :meth:`create`) alone re-decides the
        stored images: ``"keep"`` gives the original back, ``"crop"`` crops
        an image that was kept. Like :meth:`create`, the response can carry a
        top-level ``warnings`` list with ``image_fit`` entries when the update
        changes the images or ``media_fit``.

        Only top-level ``None`` values are dropped from the body, so passing
        e.g. ``x={"thread_parts": None}`` still clears an X thread. The same
        applies to ``bluesky``, ``mastodon`` and ``threads`` thread parts.

        ``pinterest`` replaces the stored Pinterest options wholesale, so
        leave ``product_tags`` out (or send ``[]``) to remove the product
        tags.

        Updating a scheduled X link post is subject to the same schedule-time
        credit gate as :meth:`create`: if the update would push the
        company's total reserved credits (across every scheduled X link
        post) past its balance, the request is rejected with
        ``402 x_credits_insufficient`` before anything changes.

        ``comment_dm_automation`` (same shape as on :meth:`create`) as a
        mapping replaces the post's comment-to-DM automations (a channel no
        longer in ``platforms`` loses its automation), an explicit ``None``
        removes them all, and leaving it out keeps them. Needs the
        ``automations:write`` scope.

        ``discord`` merges into the stored Discord options: a key set to
        ``None`` removes that option (e.g. ``discord={"poll": None}``), an
        explicit ``discord=None`` removes every option, and leaving it out
        keeps them.
        """
        body = _update_body(
            content=content,
            scheduled_at=scheduled_at,
            channels=channels,
            media_ids=media_ids,
            media_urls=media_urls,
            type=type,
            location_id=location_id,
            collaborators=collaborators,
            user_tags=user_tags,
            pinterest=pinterest,
            youtube=youtube,
            instagram=instagram,
            facebook=facebook,
            linkedin=linkedin,
            linkedin_page=linkedin_page,
            tiktok=tiktok,
            x=x,
            bluesky=bluesky,
            mastodon=mastodon,
            threads=threads,
            google_business=google_business,
            telegram=telegram,
            discord=discord,
            linkedin_poll=linkedin_poll,
            video_cover=video_cover,
            draft=draft,
            media_fit=media_fit,
            comment_dm_automation=comment_dm_automation,
        )
        return await self._client.request("PATCH", f"/posts/{post_id}", json=body)

    async def delete(self, post_id: str) -> None:
        """``DELETE /posts/{id}`` - remove a post from OmniSocials (the live post stays on the platform). Returns ``None`` (204)."""
        return await self._client.request("DELETE", f"/posts/{post_id}")

    async def publish(self, post_id: str) -> Any:
        """``POST /posts/{id}/publish`` - publish a draft or scheduled post now.

        Publishing an X link post is subject to the same schedule-time
        credit gate as :meth:`create` (``402 x_credits_insufficient`` when
        the reservation would exceed the company's credit balance).
        """
        return await self._client.request("POST", f"/posts/{post_id}/publish")

    async def retry(self, post_id: str) -> Any:
        """``POST /posts/{id}/retry`` - retry the failed platforms of a
        ``failed`` or ``warning`` (partially failed) post, on the same post.

        Only the platforms that failed are re-published; platforms that
        already succeeded are never posted again. Asynchronous: a 200 means
        the retry is queued - poll ``get`` for the outcome. Max 3 retries per
        platform.
        """
        return await self._client.request("POST", f"/posts/{post_id}/retry")

    async def approve(self, post_id: str) -> Any:
        """``POST /posts/{id}/approve`` - approve the current step of a
        post's approval workflow, on behalf of the user who owns this API
        key. That user must be a listed approver for the workflow's CURRENT
        step - steps approve in order, so an approver on a later step gets
        a 403 ``forbidden`` error until earlier steps clear. Only works on a
        post with ``approval_status: "pending"``. If this is the last step,
        the post finalizes immediately (``scheduled`` or ``posting``);
        otherwise it stays ``in_approval`` and the next step's approvers are
        notified.
        """
        return await self._client.request("POST", f"/posts/{post_id}/approve")

    async def reject(self, post_id: str, comment: Optional[str] = None) -> Any:
        """``POST /posts/{id}/reject`` - reject a post's approval workflow,
        on behalf of the user who owns this API key. Same approver
        requirement as :meth:`approve`. Unlike approval, a rejection stops
        the WHOLE workflow immediately (not just the current step) - the
        post's status becomes ``rejected``. ``comment`` is optional and,
        when given, is shown to the requester and other approvers in the
        post's review thread.
        """
        body = {"comment": comment} if comment else None
        return await self._client.request(
            "POST", f"/posts/{post_id}/reject", json=body
        )

    async def get_approval(self, post_id: str) -> Any:
        """``GET /posts/{id}/approval`` - the approval review of a post:
        every step with its approvers and their decisions, the rejection
        with its reason, and the comment thread. Use it when
        ``approval_status`` is ``rejected`` to learn who rejected the post
        and why, or while it is ``pending`` to see who the post waits for.

        ``data`` carries ``post_id``, ``status`` (``none``, ``pending``,
        ``approved``, ``rejected``), ``workflow``, ``requested_by``,
        ``requested_at``, ``current_step``, ``steps``, ``rejection`` and
        ``comments`` (oldest first). A post without an approval workflow
        returns ``status: "none"`` with the object fields ``None`` and
        empty ``steps`` and ``comments``. Read-only; requires the
        ``posts:read`` scope.
        """
        return await self._client.request("GET", f"/posts/{post_id}/approval")
