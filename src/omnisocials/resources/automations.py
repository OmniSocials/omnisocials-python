"""Automations resource: comment-to-DM automations (list, get, create,
update, delete, events). An automation answers a keyword in an Instagram
comment (or a DM, or a story reply) with a DM, once per person, with an
optional public reply under the comment. The scopes are opt-in on the API
key: ``automations:read`` for list / get / list_events, ``automations:write``
for create / update / delete (and for ``comment_dm_automation`` on posts)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Automations", "AsyncAutomations"]


def _automation_body(
    *,
    name: Optional[str],
    post_id: Optional[str],
    instagram_media_id: Optional[str],
    trigger: Optional[Mapping[str, Any]],
    actions: Optional[Mapping[str, Any]],
    limits: Optional[Mapping[str, Any]],
    status: Optional[str],
) -> Dict[str, Any]:
    return drop_none(
        {
            "name": name,
            "post_id": post_id,
            "instagram_media_id": instagram_media_id,
            "trigger": trigger,
            "actions": actions,
            "limits": limits,
            "status": status,
        }
    )


class Automations:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self, *, status: Optional[str] = None, post_id: Optional[str] = None
    ) -> Any:
        """``GET /automations`` - list the workspace's comment-to-DM
        automations, optionally by ``status`` (``active``, ``paused``,
        ``completed``) or by the OmniSocials ``post_id`` they are bound to.
        Requires the ``automations:read`` scope (opt-in on the API key)."""
        return self._client.request(
            "GET", "/automations", query={"status": status, "post_id": post_id}
        )

    def get(self, automation_id: str) -> Any:
        """``GET /automations/{id}`` - fetch a single automation. Requires
        the ``automations:read`` scope (opt-in on the API key)."""
        return self._client.request("GET", f"/automations/{automation_id}")

    def create(
        self,
        *,
        actions: Mapping[str, Any],
        trigger: Optional[Mapping[str, Any]] = None,
        limits: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
        post_id: Optional[str] = None,
        instagram_media_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        """``POST /automations`` - create a comment-to-DM automation.

        A keyword in an Instagram comment (or a DM, or a story reply) is
        answered with a DM, once per person, with an optional public reply
        under the comment. Bind it to one post with ``post_id`` (an
        OmniSocials post that goes to Instagram, scheduled or live; one
        automation per post) or ``instagram_media_id`` (a post published
        outside OmniSocials), not both; ``trigger["scope"]`` ``next_post`` or
        ``any`` needs neither.

        ``actions`` is required: ``{"dm": {"text": "..."}}`` (max 1000
        characters) plus an optional ``"public_reply": {"enabled": True,
        "variations": [...]}`` (comment kind only, up to 10 of 300
        characters). ``trigger`` is ``{"kinds": ["comment"], "scope":
        "post", "keywords": [...], "match": "word"}``: ``kinds`` one or more
        of ``comment``, ``dm``, ``story_reply``; ``keywords`` up to 20 of 60
        characters, required unless ``match`` is ``any``; ``match`` is
        ``word``, ``contains`` or ``any``. ``limits`` is ``{"max_sends":
        500, "stop_at": "2026-12-31T00:00:00Z"}`` (both optional).
        ``status`` is ``active`` (default) or ``paused``. Instagram rules:
        one private reply per comment, within 7 days; OmniSocials caps sends
        at 180 DMs an hour per account.

        Requires the ``automations:write`` scope (opt-in on the API key).
        Errors: ``400 validation_error``, ``400 post_not_instagram``,
        ``400 post_required``, ``404 post_not_found``,
        ``404 instagram_media_not_found``, ``409 instagram_not_connected``,
        ``409 instagram_needs_reauth``, ``409 automation_exists`` (the error
        body also carries ``automation_id``).
        """
        body = _automation_body(
            name=name,
            post_id=post_id,
            instagram_media_id=instagram_media_id,
            trigger=trigger,
            actions=actions,
            limits=limits,
            status=status,
        )
        return self._client.request("POST", "/automations", json=body)

    def update(
        self,
        automation_id: str,
        *,
        name: Optional[str] = None,
        post_id: Optional[str] = None,
        instagram_media_id: Optional[str] = None,
        trigger: Optional[Mapping[str, Any]] = None,
        actions: Optional[Mapping[str, Any]] = None,
        limits: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Any:
        """``PATCH /automations/{id}`` - partial update.

        Each section (``trigger``, ``actions``, ``limits``) is merged into
        the stored one; keys you omit keep their value: new
        ``trigger["keywords"]`` keep the kinds, the scope and the match; a
        new ``actions["dm"]["text"]`` keeps the public reply;
        ``limits={"stop_at": ...}`` keeps ``max_sends``.
        ``public_reply`` with ``"enabled": False`` or ``"variations": []``
        turns the public reply off; ``limits={"max_sends": None}`` removes
        that limit. ``status="paused"`` pauses and ``"active"`` resumes;
        another ``post_id`` / ``instagram_media_id`` moves the automation to
        that post. A ``completed`` automation starts again when its limits
        or trigger change. Requires the ``automations:write`` scope.
        ``400 no_fields`` when nothing is passed.
        """
        body = _automation_body(
            name=name,
            post_id=post_id,
            instagram_media_id=instagram_media_id,
            trigger=trigger,
            actions=actions,
            limits=limits,
            status=status,
        )
        return self._client.request(
            "PATCH", f"/automations/{automation_id}", json=body
        )

    def delete(self, automation_id: str) -> None:
        """``DELETE /automations/{id}`` - delete an automation. Returns
        ``None`` (204). Requires the ``automations:write`` scope."""
        return self._client.request("DELETE", f"/automations/{automation_id}")

    def list_events(
        self,
        automation_id: str,
        *,
        outcome: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /automations/{id}/events`` - the automation's activity: one
        event per person it answered, skipped or failed on.

        ``outcome`` filters on ``sent``, ``skipped``, ``failed`` or
        ``pending``; ``limit`` is 1 to 100 (default 25), ``offset`` skips.
        Requires the ``automations:read`` scope.

        The response is not the plain list envelope: ``{"data": [...],
        "counts": {"sent": 12, "skipped": 3}, "pagination": {...}}``, where
        ``counts`` is the number of events per outcome (an outcome with no
        events is left out). Each event carries ``kind`` (``comment``,
        ``dm``, ``story_reply``), ``outcome``, ``reason`` /
        ``reason_label``, ``person`` (``id``, ``username``),
        ``trigger_id``, ``trigger_text``, ``message`` (the DM sent),
        ``public_reply``, ``platform_message_id``, ``created_at`` and
        ``sent_at``.
        """
        return self._client.request(
            "GET",
            f"/automations/{automation_id}/events",
            query={"outcome": outcome, "limit": limit, "offset": offset},
        )


class AsyncAutomations:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self, *, status: Optional[str] = None, post_id: Optional[str] = None
    ) -> Any:
        """``GET /automations`` - list the workspace's comment-to-DM
        automations, optionally by ``status`` (``active``, ``paused``,
        ``completed``) or by the OmniSocials ``post_id`` they are bound to.
        Requires the ``automations:read`` scope (opt-in on the API key)."""
        return await self._client.request(
            "GET", "/automations", query={"status": status, "post_id": post_id}
        )

    async def get(self, automation_id: str) -> Any:
        """``GET /automations/{id}`` - fetch a single automation. Requires
        the ``automations:read`` scope (opt-in on the API key)."""
        return await self._client.request("GET", f"/automations/{automation_id}")

    async def create(
        self,
        *,
        actions: Mapping[str, Any],
        trigger: Optional[Mapping[str, Any]] = None,
        limits: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
        post_id: Optional[str] = None,
        instagram_media_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        """``POST /automations`` - create a comment-to-DM automation.

        A keyword in an Instagram comment (or a DM, or a story reply) is
        answered with a DM, once per person, with an optional public reply
        under the comment. Bind it to one post with ``post_id`` (an
        OmniSocials post that goes to Instagram, scheduled or live; one
        automation per post) or ``instagram_media_id`` (a post published
        outside OmniSocials), not both; ``trigger["scope"]`` ``next_post`` or
        ``any`` needs neither.

        ``actions`` is required: ``{"dm": {"text": "..."}}`` (max 1000
        characters) plus an optional ``"public_reply": {"enabled": True,
        "variations": [...]}`` (comment kind only, up to 10 of 300
        characters). ``trigger`` is ``{"kinds": ["comment"], "scope":
        "post", "keywords": [...], "match": "word"}``: ``kinds`` one or more
        of ``comment``, ``dm``, ``story_reply``; ``keywords`` up to 20 of 60
        characters, required unless ``match`` is ``any``; ``match`` is
        ``word``, ``contains`` or ``any``. ``limits`` is ``{"max_sends":
        500, "stop_at": "2026-12-31T00:00:00Z"}`` (both optional).
        ``status`` is ``active`` (default) or ``paused``. Instagram rules:
        one private reply per comment, within 7 days; OmniSocials caps sends
        at 180 DMs an hour per account.

        Requires the ``automations:write`` scope (opt-in on the API key).
        Errors: ``400 validation_error``, ``400 post_not_instagram``,
        ``400 post_required``, ``404 post_not_found``,
        ``404 instagram_media_not_found``, ``409 instagram_not_connected``,
        ``409 instagram_needs_reauth``, ``409 automation_exists`` (the error
        body also carries ``automation_id``).
        """
        body = _automation_body(
            name=name,
            post_id=post_id,
            instagram_media_id=instagram_media_id,
            trigger=trigger,
            actions=actions,
            limits=limits,
            status=status,
        )
        return await self._client.request("POST", "/automations", json=body)

    async def update(
        self,
        automation_id: str,
        *,
        name: Optional[str] = None,
        post_id: Optional[str] = None,
        instagram_media_id: Optional[str] = None,
        trigger: Optional[Mapping[str, Any]] = None,
        actions: Optional[Mapping[str, Any]] = None,
        limits: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Any:
        """``PATCH /automations/{id}`` - partial update.

        Each section (``trigger``, ``actions``, ``limits``) is merged into
        the stored one; keys you omit keep their value: new
        ``trigger["keywords"]`` keep the kinds, the scope and the match; a
        new ``actions["dm"]["text"]`` keeps the public reply;
        ``limits={"stop_at": ...}`` keeps ``max_sends``.
        ``public_reply`` with ``"enabled": False`` or ``"variations": []``
        turns the public reply off; ``limits={"max_sends": None}`` removes
        that limit. ``status="paused"`` pauses and ``"active"`` resumes;
        another ``post_id`` / ``instagram_media_id`` moves the automation to
        that post. A ``completed`` automation starts again when its limits
        or trigger change. Requires the ``automations:write`` scope.
        ``400 no_fields`` when nothing is passed.
        """
        body = _automation_body(
            name=name,
            post_id=post_id,
            instagram_media_id=instagram_media_id,
            trigger=trigger,
            actions=actions,
            limits=limits,
            status=status,
        )
        return await self._client.request(
            "PATCH", f"/automations/{automation_id}", json=body
        )

    async def delete(self, automation_id: str) -> None:
        """``DELETE /automations/{id}`` - delete an automation. Returns
        ``None`` (204). Requires the ``automations:write`` scope."""
        return await self._client.request(
            "DELETE", f"/automations/{automation_id}"
        )

    async def list_events(
        self,
        automation_id: str,
        *,
        outcome: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /automations/{id}/events`` - the automation's activity: one
        event per person it answered, skipped or failed on.

        ``outcome`` filters on ``sent``, ``skipped``, ``failed`` or
        ``pending``; ``limit`` is 1 to 100 (default 25), ``offset`` skips.
        Requires the ``automations:read`` scope.

        The response is not the plain list envelope: ``{"data": [...],
        "counts": {"sent": 12, "skipped": 3}, "pagination": {...}}``, where
        ``counts`` is the number of events per outcome (an outcome with no
        events is left out). Each event carries ``kind`` (``comment``,
        ``dm``, ``story_reply``), ``outcome``, ``reason`` /
        ``reason_label``, ``person`` (``id``, ``username``),
        ``trigger_id``, ``trigger_text``, ``message`` (the DM sent),
        ``public_reply``, ``platform_message_id``, ``created_at`` and
        ``sent_at``.
        """
        return await self._client.request(
            "GET",
            f"/automations/{automation_id}/events",
            query={"outcome": outcome, "limit": limit, "offset": offset},
        )
