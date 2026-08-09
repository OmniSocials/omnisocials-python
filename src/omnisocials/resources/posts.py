"""Posts resource: create, schedule, publish, update, and list posts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Union

from .._utils import drop_none, join_list

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
# The same entry shape works inside x/bluesky/mastodon `thread_parts` media.
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
    google_business: Optional[Mapping[str, Any]],
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
            "google_business": google_business,
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
    google_business: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    return drop_none(
        {
            "content": content,
            "scheduled_at": scheduled_at,
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
            "google_business": google_business,
        }
    )


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
        """``GET /posts`` - list posts (status: draft, scheduled, posted, failed)."""
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create`` - create a post (draft, or scheduled when
        ``scheduled_at`` is set).

        ``hashtag_set`` (set name, case-insensitive) or ``hashtag_set_id``
        applies a saved hashtag set once at create time; tags already in a
        caption are skipped; Instagram's 30-hashtag cap returns error code
        ``hashtag_limit_exceeded``. ``hashtag_placement`` is
        ``"caption_append"`` (default) or ``"first_comment"``;
        ``hashtag_platforms`` restricts the tags to a subset of ``channels``.

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
            google_business=google_business,
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create-and-publish`` - create and publish immediately.

        See :meth:`create` for the ``warnings`` list on X link posts.
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
            google_business=google_business,
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /posts/{id}`` - update a draft or scheduled post.

        Only top-level ``None`` values are dropped from the body, so passing
        e.g. ``x={"thread_parts": None}`` still clears an X thread (reverts
        the post to single-tweet mode). The same applies to ``bluesky`` and
        ``mastodon`` thread parts.

        Updating a scheduled X link post is subject to the same schedule-time
        credit gate as :meth:`create`: if the update would push the
        company's total reserved credits (across every scheduled X link
        post) past its balance, the request is rejected with
        ``402 x_credits_insufficient`` before anything changes.
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
            google_business=google_business,
        )
        return self._client.request("PATCH", f"/posts/{post_id}", json=body)

    def delete(self, post_id: str) -> None:
        """``DELETE /posts/{id}`` - delete a post. Returns ``None`` (204)."""
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
        """``GET /posts`` - list posts (status: draft, scheduled, posted, failed)."""
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create`` - create a post (draft, or scheduled when
        ``scheduled_at`` is set).

        ``hashtag_set`` (set name, case-insensitive) or ``hashtag_set_id``
        applies a saved hashtag set once at create time; tags already in a
        caption are skipped; Instagram's 30-hashtag cap returns error code
        ``hashtag_limit_exceeded``. ``hashtag_placement`` is
        ``"caption_append"`` (default) or ``"first_comment"``;
        ``hashtag_platforms`` restricts the tags to a subset of ``channels``.

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
            google_business=google_business,
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /posts/create-and-publish`` - create and publish immediately.

        See :meth:`create` for the ``warnings`` list on X link posts.
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
            google_business=google_business,
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
        google_business: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /posts/{id}`` - update a draft or scheduled post.

        Only top-level ``None`` values are dropped from the body, so passing
        e.g. ``x={"thread_parts": None}`` still clears an X thread.

        Updating a scheduled X link post is subject to the same schedule-time
        credit gate as :meth:`create`: if the update would push the
        company's total reserved credits (across every scheduled X link
        post) past its balance, the request is rejected with
        ``402 x_credits_insufficient`` before anything changes.
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
            google_business=google_business,
        )
        return await self._client.request("PATCH", f"/posts/{post_id}", json=body)

    async def delete(self, post_id: str) -> None:
        """``DELETE /posts/{id}`` - delete a post. Returns ``None`` (204)."""
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
