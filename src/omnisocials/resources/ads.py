"""Ads resource: boosts, campaigns and "Create an ad" drafts on Meta,
Pinterest, TikTok, LinkedIn, X and Google.

Ads spend real money once a campaign starts. Boosts, campaigns and drafts are
created as drafts (no spend); ``activate``, ``activate_multi``,
``drafts.launch``, ``resume`` and a budget raise through ``update`` start or
raise spend, and each needs the amount again as a confirmation. These calls
are never retried after a 5xx, a timeout or a lost connection (only a 429),
because the first attempt may have started the ad. Budgets are in major
currency units (10 = 10 EUR) in the ad account's currency. Ad accounts are
connected and picked in the OmniSocials dashboard. The scopes ``ads:read``
and ``ads:write`` are opt-in on the API key (the Ads switch)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Union
from urllib.parse import quote

from .._utils import RATE_LIMIT_ONLY, drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Ads", "AsyncAds", "AdDrafts", "AsyncAdDrafts"]


def _seg(value: Union[int, str]) -> str:
    """Percent-encode an id for use as one path segment."""
    return quote(str(value), safe="")


def _boost_body(
    *,
    post_id: Union[int, str],
    budget: Mapping[str, Any],
    objective: Optional[str],
    targeting: Optional[Mapping[str, Any]],
    schedule: Optional[Mapping[str, Any]],
    creative: Optional[Mapping[str, Any]],
    name: Optional[str],
    ad_account_id: Optional[Union[int, str]] = None,
    ad_account_ids: Optional[Sequence[Union[int, str]]] = None,
) -> Dict[str, Any]:
    return drop_none(
        {
            "post_id": post_id,
            "ad_account_id": ad_account_id,
            "ad_account_ids": None if ad_account_ids is None else [*ad_account_ids],
            "budget": budget,
            "objective": objective,
            "targeting": targeting,
            "schedule": schedule,
            "creative": creative,
            "name": name,
        }
    )


def _draft_body(
    *,
    objective: str,
    platforms: Sequence[Union[str, Mapping[str, Any]]],
    budget: Mapping[str, Any],
    targeting: Mapping[str, Any],
    ads: Sequence[Mapping[str, Any]],
    name: Optional[str],
    schedule: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    return drop_none(
        {
            "name": name,
            "objective": objective,
            "platforms": [*platforms],
            "budget": budget,
            "schedule": schedule,
            "targeting": targeting,
            "ads": [*ads],
        }
    )


def _keyword_body(
    *,
    keywords: Optional[Sequence[str]],
    url: Optional[str] = None,
    country: Optional[str],
    language: Optional[str],
    limit: Optional[int] = None,
    ad_account_id: Optional[str],
) -> Dict[str, Any]:
    return drop_none(
        {
            "keywords": None if keywords is None else [*keywords],
            "url": url,
            "country": country,
            "language": language,
            "limit": limit,
            "ad_account_id": ad_account_id,
        }
    )


class AdDrafts:
    """The "Create an ad" drafts: one campaign per network in ``platforms``,
    each with the same ads. A draft never spends; ``launch()`` starts it."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def defaults(self) -> Any:
        """``GET /ads/drafts/defaults`` - suggested countries (where the
        Instagram followers are), the currency and the workspace's ad
        account per network. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/drafts/defaults")

    def create(
        self,
        *,
        objective: str,
        platforms: Sequence[Union[str, Mapping[str, Any]]],
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        ads: Sequence[Mapping[str, Any]],
        name: Optional[str] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/drafts`` - save a new ad as a draft group. It needs no
        ad account and spends nothing.

        ``objective`` is ``traffic``, ``engagement``, ``awareness`` or
        ``video_views``. ``platforms`` lists network keys (``meta``,
        ``pinterest``, ``tiktok``, ``linkedin``, ``x``, ``google``) or
        ``{"platform": ..., "budget_amount": ..., "ad_account_id": ...}``
        per network. ``budget`` is the daily amount per network,
        ``{"amount": 10, "currency": "EUR"}``. ``schedule`` is
        ``{"duration_days": 7}`` (``None`` runs until it is stopped).
        ``targeting`` needs ``countries``; ``automatic_audience=True`` lets
        the network find the audience. Each of ``ads`` has ``media``,
        ``primary_text``, ``link`` and optionally ``headline``,
        ``description``, ``cta``, ``primary_text_b`` (an A/B test) and, on
        Meta, ``placement_media={"stories_reels": {...}}`` (an upright 9:16
        file for Stories and Reels).

        Read ``ads.capabilities()`` first for what each network accepts. The
        answer carries ``review_url`` (the builder in the dashboard) and per
        network ``readiness``. Requires ``ads:write``.
        """
        body = _draft_body(
            objective=objective,
            platforms=platforms,
            budget=budget,
            targeting=targeting,
            ads=ads,
            name=name,
            schedule=schedule,
        )
        return self._client.request("POST", "/ads/drafts", json=body)

    def get(self, group_id: str) -> Any:
        """``GET /ads/drafts/{group_id}`` - one draft group. Requires
        ``ads:read``."""
        return self._client.request("GET", f"/ads/drafts/{_seg(group_id)}")

    def update(
        self,
        group_id: str,
        *,
        objective: str,
        platforms: Sequence[Union[str, Mapping[str, Any]]],
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        ads: Sequence[Mapping[str, Any]],
        name: Optional[str] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PUT /ads/drafts/{group_id}`` - replace the draft with the full
        body (the same fields as ``create()``). Networks that already
        started are left alone (``campaigns[].editable``). Requires
        ``ads:write``."""
        body = _draft_body(
            objective=objective,
            platforms=platforms,
            budget=budget,
            targeting=targeting,
            ads=ads,
            name=name,
            schedule=schedule,
        )
        return self._client.request(
            "PUT", f"/ads/drafts/{_seg(group_id)}", json=body
        )

    def delete(self, group_id: str) -> Any:
        """``DELETE /ads/drafts/{group_id}`` - delete a draft group that
        never started. Requires ``ads:write``."""
        return self._client.request("DELETE", f"/ads/drafts/{_seg(group_id)}")

    def attach_account(
        self, group_id: str, *, platform: str, ad_account_id: Union[int, str]
    ) -> Any:
        """``POST /ads/drafts/{group_id}/account`` - set the ad account of one
        network in the draft (from ``ads.list_accounts()``, same network).
        Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/drafts/{_seg(group_id)}/account",
            json={"platform": platform, "ad_account_id": ad_account_id},
        )

    def launch(
        self,
        group_id: str,
        *,
        confirm_budget_amount: Optional[float] = None,
        confirm_budget_amounts: Optional[Mapping[str, float]] = None,
    ) -> Any:
        """``POST /ads/drafts/{group_id}/launch`` - START REAL AD SPEND for
        every network of the draft that never started.

        Show the person the daily amount per network and get their yes
        first, then pass it as ``confirm_budget_amount`` (or per campaign id
        as ``confirm_budget_amounts``). A wrong or missing amount answers
        ``400 budget_confirmation_required`` and writes nothing. The answer
        is ``{"data": {"group": ..., "results": [...]}}`` with a result per
        network; one failed network never stops the others. Not retried
        after a 5xx, a timeout or a lost connection: read the draft with
        ``get()`` to see what started. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "confirm_budget_amount": confirm_budget_amount,
                "confirm_budget_amounts": confirm_budget_amounts,
            }
        )
        return self._client.request(
            "POST",
            f"/ads/drafts/{_seg(group_id)}/launch",
            json=body,
            retry=RATE_LIMIT_ONLY,
        )


class Ads:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client
        self.drafts = AdDrafts(client)

    def list_accounts(self) -> Any:
        """``GET /ads/accounts`` - the connected ad accounts, as
        ``{"data": [...], "platforms_available": [...]}``. Accounts are
        connected and picked in the dashboard; only ``is_selected`` accounts
        can run campaigns. Requires ``ads:read`` (opt-in on the API key)."""
        return self._client.request("GET", "/ads/accounts")

    def capabilities(self) -> Any:
        """``GET /ads/capabilities`` - what each network accepts for a new ad
        (goals, media, text limits, buttons, minimum daily budget),
        ``create_networks`` and ``network_states`` (``live``, ``preview`` or
        ``coming_soon``). Requires ``ads:read``."""
        return self._client.request("GET", "/ads/capabilities")

    def list(
        self,
        *,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        campaign_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /ads/campaigns`` - list campaigns and boosts, optionally by
        ``status``, ``platform`` or ``campaign_type`` (``campaign`` or
        ``boost``); ``limit`` is 1 to 100 (default 25). Requires
        ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/campaigns",
            query={
                "status": status,
                "platform": platform,
                "campaign_type": campaign_type,
                "limit": limit,
                "offset": offset,
            },
        )

    def get(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}`` - one campaign with its latest
        numbers. Requires ``ads:read``."""
        return self._client.request("GET", f"/ads/campaigns/{_seg(campaign_id)}")

    def boost(
        self,
        *,
        post_id: Union[int, str],
        ad_account_id: Union[int, str],
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        creative: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/boost`` - boost a published post. Creates a DRAFT
        boost: no spend until ``activate()``. ``budget`` is
        ``{"type": "daily", "amount": 5, "currency": "EUR"}`` in the ad
        account's currency. TikTok needs ``creative["spark_auth_code"]``,
        Google needs ``headlines``, ``descriptions`` and ``logo_url``.
        Requires ``ads:write``."""
        body = _boost_body(
            post_id=post_id,
            ad_account_id=ad_account_id,
            budget=budget,
            objective=objective,
            targeting=targeting,
            schedule=schedule,
            creative=creative,
            name=name,
        )
        return self._client.request("POST", "/ads/boost", json=body)

    def boost_multi(
        self,
        *,
        post_id: Union[int, str],
        ad_account_ids: Sequence[Union[int, str]],
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        creative: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/boost-multi`` - one DRAFT boost per ad account (up to
        10), each with the same budget, so the total is amount x accounts.
        Answers ``{"results": [...]}``; one failed account never stops the
        others. Requires ``ads:write``."""
        body = _boost_body(
            post_id=post_id,
            ad_account_ids=ad_account_ids,
            budget=budget,
            objective=objective,
            targeting=targeting,
            schedule=schedule,
            creative=creative,
            name=name,
        )
        return self._client.request("POST", "/ads/boost-multi", json=body)

    def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/campaigns`` - a DRAFT campaign without ads. It cannot
        start (``campaign_has_no_ads``): use ``ads.drafts.create()`` for a
        new ad. Requires ``ads:write``."""
        body = drop_none(
            {
                "ad_account_id": ad_account_id,
                "name": name,
                "budget": budget,
                "objective": objective,
                "targeting": targeting,
                "schedule": schedule,
            }
        )
        return self._client.request("POST", "/ads/campaigns", json=body)

    def update(
        self,
        campaign_id: Union[int, str],
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        confirm_budget_amount: Optional[float] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /ads/campaigns/{id}`` - change the name, budget, targeting
        or schedule.

        A higher budget on a running campaign RAISES REAL AD SPEND: show
        the person the new amount and get their yes first, then pass it
        again as ``confirm_budget_amount``. Not retried after a 5xx, a
        timeout or a lost connection: read the campaign with ``get()`` to
        see what happened. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "name": name,
                "budget": budget,
                "confirm_budget_amount": confirm_budget_amount,
                "targeting": targeting,
                "schedule": schedule,
            }
        )
        return self._client.request(
            "PATCH",
            f"/ads/campaigns/{_seg(campaign_id)}",
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    def activate(
        self, campaign_id: Union[int, str], confirm_budget_amount: float
    ) -> Any:
        """``POST /ads/campaigns/{id}/activate`` - START REAL AD SPEND.

        Show the person the budget (amount, currency, daily or lifetime) and
        get their yes first; ``confirm_budget_amount`` must equal the
        campaign's budget amount. A campaign of a draft group answers
        ``409 use_draft_launch``: use ``ads.drafts.launch()``. Not retried
        after a 5xx, a timeout or a lost connection: read the campaign with
        ``get()`` to see what happened. Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/activate",
            json={"confirm_budget_amount": confirm_budget_amount},
            retry=RATE_LIMIT_ONLY,
        )

    def activate_multi(
        self,
        campaign_ids: Sequence[Union[int, str]],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/campaigns/activate-multi`` - START REAL AD SPEND on up
        to 10 campaigns.

        Every campaign's budget must equal ``confirm_budget_amount``; show
        the person the total (amount x campaigns) and get their yes first.
        Answers ``{"results": [...]}``. Not retried after a 5xx, a timeout
        or a lost connection: read the campaigns with ``get()`` to see what
        happened. Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            "/ads/campaigns/activate-multi",
            json={
                "campaign_ids": [*campaign_ids],
                "confirm_budget_amount": confirm_budget_amount,
            },
            retry=RATE_LIMIT_ONLY,
        )

    def pause(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/pause`` - pause a campaign (also while
        in review). Requires ``ads:write``."""
        return self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/pause"
        )

    def resume(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/resume`` - resume a paused campaign:
        it STARTS REAL AD SPEND again. Show the person the budget and get
        their yes first. Not retried after a 5xx, a timeout or a lost
        connection: read the campaign with ``get()`` to see what happened.
        Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/resume",
            retry=RATE_LIMIT_ONLY,
        )

    def delete(self, campaign_id: Union[int, str]) -> Any:
        """``DELETE /ads/campaigns/{id}`` - delete a campaign on the network
        too. A campaign that spent is archived: its spend stays in the
        totals. Requires ``ads:write``."""
        return self._client.request(
            "DELETE", f"/ads/campaigns/{_seg(campaign_id)}"
        )

    def overview(self) -> Any:
        """``GET /ads/overview`` - accounts, campaigns per status and total
        spend. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/overview")

    def suggestions(self) -> Any:
        """``GET /ads/suggestions`` - organic posts that do better than the
        workspace median: boost candidates. Read-only. Requires
        ``ads:read``."""
        return self._client.request("GET", "/ads/suggestions")

    def research_keywords(
        self,
        *,
        keywords: Optional[Sequence[str]] = None,
        url: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        limit: Optional[int] = None,
        ad_account_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/research/keywords`` - keyword ideas from seed
        ``keywords`` (up to 20), a ``url`` or both, through the connected
        Google Ads account. ``country`` defaults to ``US``, ``language`` to
        ``en``, ``limit`` is 1 to 500 (default 100); ``ad_account_id`` only
        when the workspace has more than one Google Ads account. Read-only
        and free. Requires ``ads:read``."""
        body = _keyword_body(
            keywords=keywords,
            url=url,
            country=country,
            language=language,
            limit=limit,
            ad_account_id=ad_account_id,
        )
        return self._client.request("POST", "/ads/research/keywords", json=body)

    def keyword_metrics(
        self,
        *,
        keywords: Sequence[str],
        country: Optional[str] = None,
        language: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/research/keywords/metrics`` - search numbers for an
        exact keyword list. Read-only. Requires ``ads:read``."""
        body = _keyword_body(
            keywords=keywords,
            country=country,
            language=language,
            ad_account_id=ad_account_id,
        )
        return self._client.request(
            "POST", "/ads/research/keywords/metrics", json=body
        )


class AsyncAdDrafts:
    """The "Create an ad" drafts: one campaign per network in ``platforms``,
    each with the same ads. A draft never spends; ``launch()`` starts it."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def defaults(self) -> Any:
        """``GET /ads/drafts/defaults`` - suggested countries (where the
        Instagram followers are), the currency and the workspace's ad
        account per network. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/drafts/defaults")

    async def create(
        self,
        *,
        objective: str,
        platforms: Sequence[Union[str, Mapping[str, Any]]],
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        ads: Sequence[Mapping[str, Any]],
        name: Optional[str] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/drafts`` - save a new ad as a draft group. It needs no
        ad account and spends nothing.

        ``objective`` is ``traffic``, ``engagement``, ``awareness`` or
        ``video_views``. ``platforms`` lists network keys (``meta``,
        ``pinterest``, ``tiktok``, ``linkedin``, ``x``, ``google``) or
        ``{"platform": ..., "budget_amount": ..., "ad_account_id": ...}``
        per network. ``budget`` is the daily amount per network,
        ``{"amount": 10, "currency": "EUR"}``. ``schedule`` is
        ``{"duration_days": 7}`` (``None`` runs until it is stopped).
        ``targeting`` needs ``countries``; ``automatic_audience=True`` lets
        the network find the audience. Each of ``ads`` has ``media``,
        ``primary_text``, ``link`` and optionally ``headline``,
        ``description``, ``cta``, ``primary_text_b`` (an A/B test) and, on
        Meta, ``placement_media={"stories_reels": {...}}`` (an upright 9:16
        file for Stories and Reels).

        Read ``ads.capabilities()`` first for what each network accepts. The
        answer carries ``review_url`` (the builder in the dashboard) and per
        network ``readiness``. Requires ``ads:write``.
        """
        body = _draft_body(
            objective=objective,
            platforms=platforms,
            budget=budget,
            targeting=targeting,
            ads=ads,
            name=name,
            schedule=schedule,
        )
        return await self._client.request("POST", "/ads/drafts", json=body)

    async def get(self, group_id: str) -> Any:
        """``GET /ads/drafts/{group_id}`` - one draft group. Requires
        ``ads:read``."""
        return await self._client.request("GET", f"/ads/drafts/{_seg(group_id)}")

    async def update(
        self,
        group_id: str,
        *,
        objective: str,
        platforms: Sequence[Union[str, Mapping[str, Any]]],
        budget: Mapping[str, Any],
        targeting: Mapping[str, Any],
        ads: Sequence[Mapping[str, Any]],
        name: Optional[str] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PUT /ads/drafts/{group_id}`` - replace the draft with the full
        body (the same fields as ``create()``). Networks that already
        started are left alone (``campaigns[].editable``). Requires
        ``ads:write``."""
        body = _draft_body(
            objective=objective,
            platforms=platforms,
            budget=budget,
            targeting=targeting,
            ads=ads,
            name=name,
            schedule=schedule,
        )
        return await self._client.request(
            "PUT", f"/ads/drafts/{_seg(group_id)}", json=body
        )

    async def delete(self, group_id: str) -> Any:
        """``DELETE /ads/drafts/{group_id}`` - delete a draft group that
        never started. Requires ``ads:write``."""
        return await self._client.request("DELETE", f"/ads/drafts/{_seg(group_id)}")

    async def attach_account(
        self, group_id: str, *, platform: str, ad_account_id: Union[int, str]
    ) -> Any:
        """``POST /ads/drafts/{group_id}/account`` - set the ad account of one
        network in the draft (from ``ads.list_accounts()``, same network).
        Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/drafts/{_seg(group_id)}/account",
            json={"platform": platform, "ad_account_id": ad_account_id},
        )

    async def launch(
        self,
        group_id: str,
        *,
        confirm_budget_amount: Optional[float] = None,
        confirm_budget_amounts: Optional[Mapping[str, float]] = None,
    ) -> Any:
        """``POST /ads/drafts/{group_id}/launch`` - START REAL AD SPEND for
        every network of the draft that never started.

        Show the person the daily amount per network and get their yes
        first, then pass it as ``confirm_budget_amount`` (or per campaign id
        as ``confirm_budget_amounts``). A wrong or missing amount answers
        ``400 budget_confirmation_required`` and writes nothing. The answer
        is ``{"data": {"group": ..., "results": [...]}}`` with a result per
        network; one failed network never stops the others. Not retried
        after a 5xx, a timeout or a lost connection: read the draft with
        ``get()`` to see what started. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "confirm_budget_amount": confirm_budget_amount,
                "confirm_budget_amounts": confirm_budget_amounts,
            }
        )
        return await self._client.request(
            "POST",
            f"/ads/drafts/{_seg(group_id)}/launch",
            json=body,
            retry=RATE_LIMIT_ONLY,
        )


class AsyncAds:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client
        self.drafts = AsyncAdDrafts(client)

    async def list_accounts(self) -> Any:
        """``GET /ads/accounts`` - the connected ad accounts, as
        ``{"data": [...], "platforms_available": [...]}``. Accounts are
        connected and picked in the dashboard; only ``is_selected`` accounts
        can run campaigns. Requires ``ads:read`` (opt-in on the API key)."""
        return await self._client.request("GET", "/ads/accounts")

    async def capabilities(self) -> Any:
        """``GET /ads/capabilities`` - what each network accepts for a new ad
        (goals, media, text limits, buttons, minimum daily budget),
        ``create_networks`` and ``network_states`` (``live``, ``preview`` or
        ``coming_soon``). Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/capabilities")

    async def list(
        self,
        *,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        campaign_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /ads/campaigns`` - list campaigns and boosts, optionally by
        ``status``, ``platform`` or ``campaign_type`` (``campaign`` or
        ``boost``); ``limit`` is 1 to 100 (default 25). Requires
        ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/campaigns",
            query={
                "status": status,
                "platform": platform,
                "campaign_type": campaign_type,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}`` - one campaign with its latest
        numbers. Requires ``ads:read``."""
        return await self._client.request("GET", f"/ads/campaigns/{_seg(campaign_id)}")

    async def boost(
        self,
        *,
        post_id: Union[int, str],
        ad_account_id: Union[int, str],
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        creative: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/boost`` - boost a published post. Creates a DRAFT
        boost: no spend until ``activate()``. ``budget`` is
        ``{"type": "daily", "amount": 5, "currency": "EUR"}`` in the ad
        account's currency. TikTok needs ``creative["spark_auth_code"]``,
        Google needs ``headlines``, ``descriptions`` and ``logo_url``.
        Requires ``ads:write``."""
        body = _boost_body(
            post_id=post_id,
            ad_account_id=ad_account_id,
            budget=budget,
            objective=objective,
            targeting=targeting,
            schedule=schedule,
            creative=creative,
            name=name,
        )
        return await self._client.request("POST", "/ads/boost", json=body)

    async def boost_multi(
        self,
        *,
        post_id: Union[int, str],
        ad_account_ids: Sequence[Union[int, str]],
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        creative: Optional[Mapping[str, Any]] = None,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/boost-multi`` - one DRAFT boost per ad account (up to
        10), each with the same budget, so the total is amount x accounts.
        Answers ``{"results": [...]}``; one failed account never stops the
        others. Requires ``ads:write``."""
        body = _boost_body(
            post_id=post_id,
            ad_account_ids=ad_account_ids,
            budget=budget,
            objective=objective,
            targeting=targeting,
            schedule=schedule,
            creative=creative,
            name=name,
        )
        return await self._client.request("POST", "/ads/boost-multi", json=body)

    async def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        budget: Mapping[str, Any],
        objective: Optional[str] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/campaigns`` - a DRAFT campaign without ads. It cannot
        start (``campaign_has_no_ads``): use ``ads.drafts.create()`` for a
        new ad. Requires ``ads:write``."""
        body = drop_none(
            {
                "ad_account_id": ad_account_id,
                "name": name,
                "budget": budget,
                "objective": objective,
                "targeting": targeting,
                "schedule": schedule,
            }
        )
        return await self._client.request("POST", "/ads/campaigns", json=body)

    async def update(
        self,
        campaign_id: Union[int, str],
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        confirm_budget_amount: Optional[float] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /ads/campaigns/{id}`` - change the name, budget, targeting
        or schedule.

        A higher budget on a running campaign RAISES REAL AD SPEND: show
        the person the new amount and get their yes first, then pass it
        again as ``confirm_budget_amount``. Not retried after a 5xx, a
        timeout or a lost connection: read the campaign with ``get()`` to
        see what happened. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "name": name,
                "budget": budget,
                "confirm_budget_amount": confirm_budget_amount,
                "targeting": targeting,
                "schedule": schedule,
            }
        )
        return await self._client.request(
            "PATCH",
            f"/ads/campaigns/{_seg(campaign_id)}",
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    async def activate(
        self, campaign_id: Union[int, str], confirm_budget_amount: float
    ) -> Any:
        """``POST /ads/campaigns/{id}/activate`` - START REAL AD SPEND.

        Show the person the budget (amount, currency, daily or lifetime) and
        get their yes first; ``confirm_budget_amount`` must equal the
        campaign's budget amount. A campaign of a draft group answers
        ``409 use_draft_launch``: use ``ads.drafts.launch()``. Not retried
        after a 5xx, a timeout or a lost connection: read the campaign with
        ``get()`` to see what happened. Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/activate",
            json={"confirm_budget_amount": confirm_budget_amount},
            retry=RATE_LIMIT_ONLY,
        )

    async def activate_multi(
        self,
        campaign_ids: Sequence[Union[int, str]],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/campaigns/activate-multi`` - START REAL AD SPEND on up
        to 10 campaigns.

        Every campaign's budget must equal ``confirm_budget_amount``; show
        the person the total (amount x campaigns) and get their yes first.
        Answers ``{"results": [...]}``. Not retried after a 5xx, a timeout
        or a lost connection: read the campaigns with ``get()`` to see what
        happened. Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            "/ads/campaigns/activate-multi",
            json={
                "campaign_ids": [*campaign_ids],
                "confirm_budget_amount": confirm_budget_amount,
            },
            retry=RATE_LIMIT_ONLY,
        )

    async def pause(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/pause`` - pause a campaign (also while
        in review). Requires ``ads:write``."""
        return await self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/pause"
        )

    async def resume(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/resume`` - resume a paused campaign:
        it STARTS REAL AD SPEND again. Show the person the budget and get
        their yes first. Not retried after a 5xx, a timeout or a lost
        connection: read the campaign with ``get()`` to see what happened.
        Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/resume",
            retry=RATE_LIMIT_ONLY,
        )

    async def delete(self, campaign_id: Union[int, str]) -> Any:
        """``DELETE /ads/campaigns/{id}`` - delete a campaign on the network
        too. A campaign that spent is archived: its spend stays in the
        totals. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE", f"/ads/campaigns/{_seg(campaign_id)}"
        )

    async def overview(self) -> Any:
        """``GET /ads/overview`` - accounts, campaigns per status and total
        spend. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/overview")

    async def suggestions(self) -> Any:
        """``GET /ads/suggestions`` - organic posts that do better than the
        workspace median: boost candidates. Read-only. Requires
        ``ads:read``."""
        return await self._client.request("GET", "/ads/suggestions")

    async def research_keywords(
        self,
        *,
        keywords: Optional[Sequence[str]] = None,
        url: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        limit: Optional[int] = None,
        ad_account_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/research/keywords`` - keyword ideas from seed
        ``keywords`` (up to 20), a ``url`` or both, through the connected
        Google Ads account. ``country`` defaults to ``US``, ``language`` to
        ``en``, ``limit`` is 1 to 500 (default 100); ``ad_account_id`` only
        when the workspace has more than one Google Ads account. Read-only
        and free. Requires ``ads:read``."""
        body = _keyword_body(
            keywords=keywords,
            url=url,
            country=country,
            language=language,
            limit=limit,
            ad_account_id=ad_account_id,
        )
        return await self._client.request("POST", "/ads/research/keywords", json=body)

    async def keyword_metrics(
        self,
        *,
        keywords: Sequence[str],
        country: Optional[str] = None,
        language: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/research/keywords/metrics`` - search numbers for an
        exact keyword list. Read-only. Requires ``ads:read``."""
        body = _keyword_body(
            keywords=keywords,
            country=country,
            language=language,
            ad_account_id=ad_account_id,
        )
        return await self._client.request(
            "POST", "/ads/research/keywords/metrics", json=body
        )
