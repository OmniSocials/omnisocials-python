"""Webhooks resource: manage event subscriptions (post.scheduled,
post.published, post.failed, post.approved, post.rejected, and for ads
ad.status_changed, ad.created, ad.updated, ad.review, ad.delivery_issue,
campaign.created, campaign.updated, campaign.budget, lead.received,
ads.sync_failed, ads.sync_recovered, ads.initial_sync_completed and
ad_rule.triggered, and for X statistics x_statistics.paused and
x_statistics.resumed)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence

from .._utils import drop_none, path_segment

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Webhooks", "AsyncWebhooks"]


class Webhooks:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /webhooks`` - list the webhooks of the key's workspace and
        the organisation-wide webhooks of its organisation.

        Every webhook carries ``workspace_id``: ``None`` for an
        organisation-wide webhook (made in the OmniSocials dashboard), which
        receives the events of every workspace of the organisation. A
        webhook whose creator lost access to the organisation or workspace
        is switched off automatically:
        ``is_active`` is ``False`` and ``last_failure["error"]`` says why.
        """
        return self._client.request("GET", "/webhooks")

    def get(self, webhook_id: str) -> Any:
        """``GET /webhooks/{id}`` - fetch a webhook of the key's workspace,
        or an organisation-wide webhook of its organisation
        (``workspace_id`` ``None``)."""
        return self._client.request("GET", f"/webhooks/{path_segment(webhook_id)}")

    def create(self, *, url: str, events: Sequence[str]) -> Any:
        """``POST /webhooks`` - create a webhook subscription.

        ``url`` must be HTTPS. ``events`` is a non-empty subset of
        ``post.scheduled``, ``post.published``, ``post.failed``,
        ``post.approved``, ``post.rejected`` and the ads events
        ``ad.status_changed``, ``ad.created``, ``ad.updated``, ``ad.review``,
        ``ad.delivery_issue``, ``campaign.created``, ``campaign.updated``,
        ``campaign.budget``, ``lead.received``, ``ads.sync_failed``,
        ``ads.sync_recovered``, ``ads.initial_sync_completed`` and
        ``ad_rule.triggered``, and ``x_statistics.paused`` /
        ``x_statistics.resumed`` (the organisation's X statistics stopped at
        0 credits or started again after a top-up, one delivery per
        workspace with X; ``data`` is ``{"workspace_id", "account_id",
        "reason"}``, ``reason`` ``insufficient_credits`` or
        ``credits_added``). The ``data`` of an ``ad.status_changed``
        delivery is the campaign, not a post: ``campaign_id``,
        ``workspace_id``, ``name``, ``platform``, ``campaign_type``,
        ``status``, ``previous_status``, ``external_campaign_id`` and
        ``budget``; the other ads events carry the campaign (plus
        ``details``) or their own data (a lead, a rule run, an ad account).
        Any Ads event (``ad.*``, ``campaign.*``, ``lead.*``, ``ads.*``,
        ``ad_rule.*``) needs the ``ads:read`` scope on the key and
        ``access_ads`` for its person (``403 insufficient_scope`` /
        ``403 insufficient_permission``). The signing ``secret`` is only
        returned once, in this response - store it.
        """
        return self._client.request(
            "POST", "/webhooks", json={"url": url, "events": list(events)}
        )

    def update(
        self,
        webhook_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[Sequence[str]] = None,
        is_active: Optional[bool] = None,
    ) -> Any:
        """``PATCH /webhooks/{id}`` - update url, events, or active state.

        Ads events need the same ``ads:read`` scope and ``access_ads`` as on
        ``create()``: when the webhook has Ads events after the change,
        setting ``url`` or ``events`` or switching it on answers 403 without
        them. Works on organisation-wide webhooks too.
        ``is_active=True`` switches on a webhook that was switched off (also
        an automatic switch-off); setting ``url``, ``events`` or switching it
        on makes the key's creator the person behind the webhook. Setting
        ``url`` on an organisation-wide webhook (even its current one) moves
        it to the key's workspace: from then on it gets only that
        workspace's events, and the answer shows the new ``workspace_id``.
        """
        body = drop_none(
            {
                "url": url,
                "events": list(events) if events is not None else None,
                "is_active": is_active,
            }
        )
        return self._client.request("PATCH", f"/webhooks/{path_segment(webhook_id)}", json=body)

    def delete(self, webhook_id: str) -> None:
        """``DELETE /webhooks/{id}`` - delete a webhook of the key's
        workspace or an organisation-wide webhook of its organisation.
        Returns ``None`` (204)."""
        return self._client.request("DELETE", f"/webhooks/{path_segment(webhook_id)}")

    def rotate_secret(self, webhook_id: str) -> Any:
        """``POST /webhooks/{id}/rotate-secret`` - rotate the signing secret.

        The new secret is only returned once, in this response. The old
        secret keeps signing for 24 hours: every delivery then carries
        ``X-OmniSocials-Signature`` (new secret) and
        ``X-OmniSocials-Signature-Previous`` (old secret, same format, same
        timestamp and body). Verify the first with the new secret and, when
        that fails, the second with the old one (see
        :func:`omnisocials.verify_webhook_signature`). Rotating again within
        the 24 hours replaces the previous secret with the one just rotated
        out. Works on organisation-wide webhooks too.
        """
        return self._client.request("POST", f"/webhooks/{path_segment(webhook_id)}/rotate-secret")


class AsyncWebhooks:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /webhooks`` - list the webhooks of the key's workspace and
        the organisation-wide webhooks of its organisation.

        Every webhook carries ``workspace_id``: ``None`` for an
        organisation-wide webhook (made in the OmniSocials dashboard), which
        receives the events of every workspace of the organisation. A
        webhook whose creator lost access to the organisation or workspace
        is switched off automatically:
        ``is_active`` is ``False`` and ``last_failure["error"]`` says why.
        """
        return await self._client.request("GET", "/webhooks")

    async def get(self, webhook_id: str) -> Any:
        """``GET /webhooks/{id}`` - fetch a webhook of the key's workspace,
        or an organisation-wide webhook of its organisation
        (``workspace_id`` ``None``)."""
        return await self._client.request("GET", f"/webhooks/{path_segment(webhook_id)}")

    async def create(self, *, url: str, events: Sequence[str]) -> Any:
        """``POST /webhooks`` - create a webhook subscription.

        ``url`` must be HTTPS. ``events`` is a non-empty subset of
        ``post.scheduled``, ``post.published``, ``post.failed``,
        ``post.approved``, ``post.rejected`` and the ads events
        ``ad.status_changed``, ``ad.created``, ``ad.updated``, ``ad.review``,
        ``ad.delivery_issue``, ``campaign.created``, ``campaign.updated``,
        ``campaign.budget``, ``lead.received``, ``ads.sync_failed``,
        ``ads.sync_recovered``, ``ads.initial_sync_completed`` and
        ``ad_rule.triggered``. The ``data`` of an ``ad.status_changed``
        delivery is the campaign, not a post: ``campaign_id``,
        ``workspace_id``, ``name``, ``platform``, ``campaign_type``,
        ``status``, ``previous_status``, ``external_campaign_id`` and
        ``budget``; the other ads events carry the campaign (plus
        ``details``) or their own data (a lead, a rule run, an ad account).
        Any Ads event (``ad.*``, ``campaign.*``, ``lead.*``, ``ads.*``,
        ``ad_rule.*``) needs the ``ads:read`` scope on the key and
        ``access_ads`` for its person (``403 insufficient_scope`` /
        ``403 insufficient_permission``). The signing ``secret`` is only
        returned once, in this response - store it.
        """
        return await self._client.request(
            "POST", "/webhooks", json={"url": url, "events": list(events)}
        )

    async def update(
        self,
        webhook_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[Sequence[str]] = None,
        is_active: Optional[bool] = None,
    ) -> Any:
        """``PATCH /webhooks/{id}`` - update url, events, or active state.

        Ads events need the same ``ads:read`` scope and ``access_ads`` as on
        ``create()``: when the webhook has Ads events after the change,
        setting ``url`` or ``events`` or switching it on answers 403 without
        them. Works on organisation-wide webhooks too.
        ``is_active=True`` switches on a webhook that was switched off (also
        an automatic switch-off); setting ``url``, ``events`` or switching it
        on makes the key's creator the person behind the webhook. Setting
        ``url`` on an organisation-wide webhook (even its current one) moves
        it to the key's workspace: from then on it gets only that
        workspace's events, and the answer shows the new ``workspace_id``.
        """
        body = drop_none(
            {
                "url": url,
                "events": list(events) if events is not None else None,
                "is_active": is_active,
            }
        )
        return await self._client.request(
            "PATCH", f"/webhooks/{path_segment(webhook_id)}", json=body
        )

    async def delete(self, webhook_id: str) -> None:
        """``DELETE /webhooks/{id}`` - delete a webhook of the key's
        workspace or an organisation-wide webhook of its organisation.
        Returns ``None`` (204)."""
        return await self._client.request("DELETE", f"/webhooks/{path_segment(webhook_id)}")

    async def rotate_secret(self, webhook_id: str) -> Any:
        """``POST /webhooks/{id}/rotate-secret`` - rotate the signing secret.

        The new secret is only returned once, in this response. The old
        secret keeps signing for 24 hours: every delivery then carries
        ``X-OmniSocials-Signature`` (new secret) and
        ``X-OmniSocials-Signature-Previous`` (old secret, same format, same
        timestamp and body). Verify the first with the new secret and, when
        that fails, the second with the old one (see
        :func:`omnisocials.verify_webhook_signature`). Rotating again within
        the 24 hours replaces the previous secret with the one just rotated
        out. Works on organisation-wide webhooks too.
        """
        return await self._client.request(
            "POST", f"/webhooks/{path_segment(webhook_id)}/rotate-secret"
        )
