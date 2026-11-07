"""Ads resource: boosts, campaigns and "Create an ad" drafts on Meta,
Pinterest, TikTok, LinkedIn, X and Google.

Ads spend real money once a campaign starts. Boosts and drafts are created as
drafts (no spend). Starting or raising spend needs a key with the opt-in
``ads:spend`` scope ("Start ads", a second switch under "Ads"; its creator
needs ``manage_ads``): ``activate``, ``activate_multi``, ``resume``, the draft
launch (``drafts.launch``), a budget raise or any change of a campaign that
reached the network through ``update``, and the parity calls that switch
something on or raise a budget. Each repeats the amount. Without ``ads:spend``
these calls answer ``403 start_in_app`` with the page in the app where a
person does it; on Google (``api_draft_only``) they always do, also with
``ads:spend``. Pause and delete stay open, except on the networks in
``api_stop_in_app`` (Google). The calls that start or raise spend are never
retried after a 5xx, a timeout or a lost connection (only a 429), because the
first attempt may have started the ad. Budgets are in major currency units
(10 = 10 EUR) in the ad account's currency. An Ads error may carry
``param`` (the field at fault) in the error body. Ad accounts are connected
and picked in the OmniSocials dashboard. The scopes ``ads:read`` and
``ads:write`` are opt-in on the API key (the Ads switch).

The sub-resources of the Ads API parity build (``objects``, ``campaign_ads``,
``comments``, ``targeting``, ``audiences``, ``lead_forms``, ``leads``,
``conversions``, ``insights``, ``reports``, ``rules``, ``results``, ``media``,
``previews``, ``partnership``, ``accounts``, ``reach_frequency``, ``studies``,
``budget_schedules``, ``google``) are a thin passthrough: the API checks every
field. A network without the feature answers ``400 not_supported_on_network``
(``ads.capabilities()`` lists ``features`` per network); a missing permission
on the network side answers ``403 network_permission_missing``. Every call
there that switches something on or can raise spend (``objects.update``,
``objects.set_status``, ``objects.duplicate``, ``bulk_status``,
``campaign_ads.add``, ``campaign_ads.set_status``, ``rules.create``,
``rules.update``, ``rules.undo``, ``accounts.update_settings``,
``reach_frequency.reserve``, ``studies.create``, ``budget_schedules.create``)
needs a key with ``ads:spend`` (rules: else ``403 rule_raises_spend``), takes
the person's own amount where it raises spend (``confirm_budget_amount``,
rules ``confirm_max_daily_budget``) and follows the same no-retry rule.
Pausing, deleting and archiving stay open, except on Google."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Union
from urllib.parse import quote

from .._utils import NOT_GIVEN, RATE_LIMIT_ONLY, NotGiven, drop_none, join_list

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = [
    "Ads",
    "AsyncAds",
    "AdDrafts",
    "AsyncAdDrafts",
    "AdObjects",
    "AsyncAdObjects",
    "AdCampaignAds",
    "AsyncAdCampaignAds",
    "AdComments",
    "AsyncAdComments",
    "AdTargeting",
    "AsyncAdTargeting",
    "AdAudiences",
    "AsyncAdAudiences",
    "AdLeadForms",
    "AsyncAdLeadForms",
    "AdLeads",
    "AsyncAdLeads",
    "AdConversions",
    "AsyncAdConversions",
    "AdInsights",
    "AsyncAdInsights",
    "AdReports",
    "AsyncAdReports",
    "AdRules",
    "AsyncAdRules",
    "AdResults",
    "AsyncAdResults",
    "AdMedia",
    "AsyncAdMedia",
    "AdPreviews",
    "AsyncAdPreviews",
    "AdPartnership",
    "AsyncAdPartnership",
    "AdAccountsAdmin",
    "AsyncAdAccountsAdmin",
    "AdReachFrequency",
    "AsyncAdReachFrequency",
    "AdStudies",
    "AsyncAdStudies",
    "AdBudgetSchedules",
    "AsyncAdBudgetSchedules",
    "AdGoogle",
    "AsyncAdGoogle",
]


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
    each with the same ads. A draft never spends; ``launch()`` starts it (a
    key with ``ads:spend``), or a person does in the app from its
    ``review_url``."""

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
        ``video_views``; through the API also ``lead_generation``,
        ``conversions``, ``messages`` or ``calls`` (each network's goal in
        ``ads.capabilities()`` says what it ``needs``). ``platforms`` lists
        network keys (``meta``, ``pinterest``, ``tiktok``, ``linkedin``,
        ``x``, ``google``) or ``{"platform": ..., "budget_amount": ...,
        "ad_account_id": ..., "settings": {...}}`` per network (``settings``:
        bidding, conversion goal, lead form, messaging). ``budget`` is the daily amount per network,
        ``{"amount": 10, "currency": "EUR"}``. ``schedule`` is
        ``{"duration_days": 7}`` (``None`` runs until it is stopped).
        ``targeting`` needs ``countries``; ``automatic_audience=True`` lets
        the network find the audience; ``networks={"meta": {"include":
        {...}, "exclude": {...}, "audiences": {...}}}`` adds each network's
        own targeting (ids from ``ads.targeting.search()``). Each of ``ads`` has ``media``,
        ``primary_text``, ``link`` and optionally ``headline``,
        ``description``, ``cta``, ``primary_text_b`` (an A/B test),
        ``network`` (per network extras such as ``lead_form_id``,
        ``media_ref``, ``spark_auth_code`` or Google's
        ``responsive_search_ad``) and, on Meta,
        ``placement_media={"stories_reels": {...}}`` (an upright 9:16 file
        for Stories and Reels).

        Read ``ads.capabilities()`` first for what each network accepts. The
        answer carries ``review_url`` (the builder in the dashboard, where the
        person checks and starts the ad: hand it over) and per network
        ``readiness``. A ``budget["currency"]`` other than the attached ad
        account's currency answers ``400 currency_mismatch`` with
        ``param: "budget.currency"``. Requires ``ads:write``.
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
        body (the same fields as ``create()``). Networks that already started
        are left alone (``campaigns[].editable``). A ``budget["currency"]``
        other than the attached ad account's currency answers
        ``400 currency_mismatch`` with ``param: "budget.currency"``. Requires
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

        Needs a key with the opt-in ``ads:spend`` scope ("Start ads"): without
        it the call answers ``403 start_in_app`` with the draft's page (its
        ``review_url``), and a network in ``api_draft_only`` (Google) is
        always skipped with code ``start_in_app``. Show the person the daily
        amount per network and get their yes first, then pass it as
        ``confirm_budget_amount`` (or per campaign id as
        ``confirm_budget_amounts``). A wrong or missing amount answers
        ``400 budget_confirmation_required`` and writes nothing. The answer is
        ``{"data": {"group": ..., "results": [...]}}`` with a result per
        network (``campaign_id`` is a string); one failed network never stops
        the others. Not retried after a 5xx, a timeout or a lost connection:
        read the draft with ``get()`` to see what started. Requires
        ``ads:write``.
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


# ---------------------------------------------------------------------------
# Ads API parity (2026-11-05)
# ---------------------------------------------------------------------------


def _object_path(account_id: Union[int, str], level: str, external_id: str) -> str:
    return f"/ads/accounts/{_seg(account_id)}/objects/{_seg(level)}/{_seg(external_id)}"


def _ad_path(campaign_id: Union[int, str], ad_id: Union[int, str]) -> str:
    return f"/ads/campaigns/{_seg(campaign_id)}/ads/{_seg(ad_id)}"


def _account_path(account_id: Union[int, str], rest: str) -> str:
    return f"/ads/accounts/{_seg(account_id)}/{rest}"


def _insights_body(
    *,
    ad_account_id: Union[int, str],
    level: Optional[str],
    ids: Optional[Sequence[str]],
    metrics: Optional[Sequence[str]],
    breakdowns: Optional[Sequence[str]],
    from_: Optional[str],
    to: Optional[str],
    time_increment: Optional[str],
) -> Dict[str, Any]:
    return drop_none(
        {
            "ad_account_id": ad_account_id,
            "level": level,
            "ids": None if ids is None else [*ids],
            "metrics": None if metrics is None else [*metrics],
            "breakdowns": None if breakdowns is None else [*breakdowns],
            "from": from_,
            "to": to,
            "time_increment": time_increment,
        }
    )


def _rule_body(
    *,
    name: Optional[str],
    conditions: Optional[Sequence[Mapping[str, Any]]],
    action: Optional[Mapping[str, Any]],
    ad_account_id: Optional[Union[int, str]],
    enabled: Optional[bool],
    scope: Optional[Mapping[str, Any]],
    every_minutes: Optional[int],
    cooldown_minutes: Optional[int],
    max_actions_per_run: Optional[int],
    confirm_max_daily_budget: Optional[float],
) -> Dict[str, Any]:
    return drop_none(
        {
            "name": name,
            "ad_account_id": ad_account_id,
            "enabled": enabled,
            "scope": scope,
            "conditions": None if conditions is None else [*conditions],
            "action": action,
            "every_minutes": every_minutes,
            "cooldown_minutes": cooldown_minutes,
            "max_actions_per_run": max_actions_per_run,
            "confirm_max_daily_budget": confirm_max_daily_budget,
        }
    )


class AdObjects:
    """Campaigns, ad sets and ads of an ad account as the network has them,
    also the ones made outside OmniSocials, and the import of those
    campaigns. ``level`` is ``campaign``, ``ad_set`` or ``ad``. Objects of
    OmniSocials campaigns answer ``409 use_campaign_routes``: change those
    with the campaign methods."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def tree(
        self,
        account_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        status: Union[str, Sequence[str], None] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/accounts/{accountId}/tree`` - campaigns, ad sets and ads
        with the numbers of the date range (``from_`` / ``to``, ISO dates; at
        most 90 days, default the last 30). Each campaign says ``source``
        (``omnisocials`` or ``external``). ``status`` is a list or a comma
        list. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            f"/ads/accounts/{_seg(account_id)}/tree",
            query={
                "from": from_,
                "to": to,
                "status": join_list(status),
                "limit": limit,
                "cursor": cursor,
            },
        )

    def get(self, account_id: Union[int, str], level: str, external_id: str) -> Any:
        """``GET /ads/accounts/{accountId}/objects/{level}/{externalId}`` -
        live details of one object. Requires ``ads:read``."""
        return self._client.request("GET", _object_path(account_id, level, external_id))

    def update(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        end_at: Union[str, None, NotGiven] = NOT_GIVEN,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PATCH /ads/accounts/{accountId}/objects/{level}/{externalId}`` -
        change the name, budget or end date (``end_at=None`` removes it) of
        a campaign or ad set made outside OmniSocials.

        A higher budget RAISES REAL AD SPEND: show the person the new amount
        and get their yes first, then pass it as ``confirm_budget_amount``. It
        changes the campaign on the network: needs a key with the opt-in
        ``ads:spend`` scope ("Start ads"); without it, and on Google
        (``api_draft_only``) always, the call answers ``403 start_in_app``
        with the page where a person does it in the app. Not retried after a
        5xx, a timeout or a lost connection: read the object with ``get()``.
        Requires ``ads:write``.
        """
        body = drop_none(
            {"name": name, "budget": budget, "confirm_budget_amount": confirm_budget_amount}
        )
        if not isinstance(end_at, NotGiven):
            body["end_at"] = end_at
        return self._client.request(
            "PATCH",
            _object_path(account_id, level, external_id),
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    def set_status(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PUT /ads/accounts/{accountId}/objects/{level}/{externalId}/status``
        - ``status`` is ``paused`` or ``active``.

        Switching on STARTS REAL AD SPEND: pass the budget that pays (the
        object's own or its parent's) as ``confirm_budget_amount`` after the
        person agreed. Switching on: needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Pausing needs nothing and stays open
        (Google: ``start_in_app``). Not retried after a 5xx, a timeout or a
        lost connection. Requires ``ads:write``.
        """
        return self._client.request(
            "PUT",
            f"{_object_path(account_id, level, external_id)}/status",
            json=drop_none({"status": status, "confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    def duplicate(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        deep: Optional[bool] = None,
        rename: Optional[str] = None,
    ) -> Any:
        """``POST /ads/accounts/{accountId}/objects/{level}/{externalId}/duplicate``
        - copy an object made outside OmniSocials; the copy is paused (Meta
        today). It changes the ad account on the network: needs a key with the
        opt-in ``ads:spend`` scope ("Start ads"); without it, and on Google
        (``api_draft_only``) always, the call answers ``403 start_in_app``
        with the page where a person does it in the app. Requires
        ``ads:write``."""
        return self._client.request(
            "POST",
            f"{_object_path(account_id, level, external_id)}/duplicate",
            json=drop_none({"deep": deep, "rename": rename}),
        )

    def import_status(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/import`` - the import state of the
        campaigns made outside OmniSocials. Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "import"))

    def start_import(self, account_id: Union[int, str]) -> Any:
        """``POST /ads/accounts/{accountId}/import`` - read the ad account
        again at the next sync (within 15 minutes). The first import reads
        90 days; webhook ``ads.initial_sync_completed`` when it is done.
        Requires ``ads:write``."""
        return self._client.request("POST", _account_path(account_id, "import"))

    def list_external(
        self,
        *,
        ad_account_id: Optional[Union[int, str]] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /ads/external-campaigns`` - the imported campaigns (``limit``
        at most 200). Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/external-campaigns",
            query={
                "ad_account_id": ad_account_id,
                "platform": platform,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        )

    def get_external(
        self,
        campaign_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
    ) -> Any:
        """``GET /ads/external-campaigns/{id}`` - one imported campaign with
        its daily numbers. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            f"/ads/external-campaigns/{_seg(campaign_id)}",
            query={"from": from_, "to": to},
        )


class AdCampaignAds:
    """The ads of an OmniSocials campaign."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads`` - the ads with their status, review
        and latest numbers. Requires ``ads:read``."""
        return self._client.request("GET", f"/ads/campaigns/{_seg(campaign_id)}/ads")

    def add(self, campaign_id: Union[int, str], ads: Sequence[Mapping[str, Any]]) -> Any:
        """``POST /ads/campaigns/{id}/ads`` - add up to 6 ads (the shape of a
        draft ad) to a campaign that runs. They are created PAUSED on the
        network; switch each one on with ``set_status()``. Needs a key with
        the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Webhook ``ad.created``. Requires ``ads:write``."""
        return self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/ads", json={"ads": [*ads]}
        )

    def get(self, campaign_id: Union[int, str], ad_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}`` - one ad. Requires
        ``ads:read``."""
        return self._client.request("GET", _ad_path(campaign_id, ad_id))

    def set_status(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PUT /ads/campaigns/{id}/ads/{adId}/status`` - ``paused`` or
        ``active``.

        Switching on STARTS REAL AD SPEND: pass the campaign budget as
        ``confirm_budget_amount`` after the person agreed. Switching on: needs
        a key with the opt-in ``ads:spend`` scope ("Start ads"); without it,
        and on Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Pausing stays open (Google: ``start_in_app``). Not retried after a
        5xx, a timeout or a lost connection. Webhook ``ad.updated``. Requires
        ``ads:write``.
        """
        return self._client.request(
            "PUT",
            f"{_ad_path(campaign_id, ad_id)}/status",
            json=drop_none({"status": status, "confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    def review(self, campaign_id: Union[int, str], ad_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/review`` - the network's review
        verdict (``in_review``, ``approved`` or ``rejected`` with reasons).
        Requires ``ads:read``."""
        return self._client.request("GET", f"{_ad_path(campaign_id, ad_id)}/review")


class AdComments:
    """Comments on an ad of an OmniSocials campaign."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/comments``. Requires
        ``ads:read``."""
        return self._client.request(
            "GET", f"{_ad_path(campaign_id, ad_id)}/comments", query={"cursor": cursor}
        )

    def reply(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
        text: str,
    ) -> Any:
        """``POST /ads/campaigns/{id}/ads/{adId}/comments/{commentId}/reply`` -
        answer a comment. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}/reply",
            json={"text": text},
        )

    def hide(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
        hidden: bool = True,
    ) -> Any:
        """``POST /ads/campaigns/{id}/ads/{adId}/comments/{commentId}/hide`` -
        hide (default) or show a comment. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}/hide",
            json={"hidden": hidden},
        )

    def delete(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
    ) -> Any:
        """``DELETE /ads/campaigns/{id}/ads/{adId}/comments/{commentId}``.
        Requires ``ads:write``."""
        return self._client.request(
            "DELETE", f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}"
        )


class AdTargeting:
    """Targeting options of a network. The ids go in
    ``targeting["networks"][<network>]["include"]`` of a draft (or
    ``targeting["network"]`` of a campaign); the types per network are
    ``ads.capabilities()`` ``targeting_types``."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def search(
        self,
        *,
        ad_account_id: Union[int, str],
        type: str,
        q: str,
        limit: Optional[int] = None,
        country: Optional[str] = None,
    ) -> Any:
        """``GET /ads/targeting/search`` - interests, places, languages, job
        titles ... (``limit`` at most 100). Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/targeting/search",
            query={
                "ad_account_id": ad_account_id,
                "type": type,
                "q": q,
                "limit": limit,
                "country": country,
            },
        )

    def browse(self, *, ad_account_id: Union[int, str], type: str) -> Any:
        """``GET /ads/targeting/browse`` - the categories as a tree. Requires
        ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/targeting/browse",
            query={"ad_account_id": ad_account_id, "type": type},
        )

    def reach_estimate(
        self,
        *,
        ad_account_id: Union[int, str],
        targeting: Mapping[str, Any],
        objective: Optional[str] = None,
    ) -> Any:
        """``POST /ads/targeting/reach-estimate`` - the audience size of a
        targeting (``countries``, ``age_min``, ``age_max``, ``genders``,
        ``network``). Read-only. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/targeting/reach-estimate",
            json=drop_none(
                {"ad_account_id": ad_account_id, "objective": objective, "targeting": targeting}
            ),
        )

    def bid_suggestions(
        self,
        *,
        ad_account_id: Union[int, str],
        targeting: Mapping[str, Any],
        objective: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/targeting/bid-suggestions`` - a suggested bid and daily
        budget. Read-only. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/targeting/bid-suggestions",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "objective": objective,
                    "targeting": targeting,
                    "budget": budget,
                }
            ),
        )


class AdAudiences:
    """Custom audiences of an ad account: customer lists, lookalikes and
    company lists. ``audience_id`` is the network's audience id."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, *, ad_account_id: Union[int, str], cursor: Optional[str] = None) -> Any:
        """``GET /ads/audiences``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/audiences", query={"ad_account_id": ad_account_id, "cursor": cursor}
        )

    def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        description: Optional[str] = None,
        kind: Optional[str] = None,
        lookalike: Optional[Mapping[str, Any]] = None,
        customer_file_source: Optional[str] = None,
        schema: Optional[Sequence[str]] = None,
        rows: Optional[Sequence[Sequence[str]]] = None,
    ) -> Any:
        """``POST /ads/audiences`` - ``kind`` is ``customer_list``,
        ``lookalike`` (``lookalike={"source_audience_id", "country",
        "ratio"}``, ratio 0.01 to 0.2) or ``company_list``.

        ``customer_file_source`` (Meta: ``user_provided``,
        ``partner_provided`` or ``both``) is what the person says. ``schema``
        + ``rows`` are optional first members of a customer list (Pinterest
        needs them); raw values are hashed with SHA-256 before they leave.
        Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            "/ads/audiences",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "description": description,
                    "kind": kind,
                    "lookalike": lookalike,
                    "customer_file_source": customer_file_source,
                    "schema": None if schema is None else [*schema],
                    "rows": None if rows is None else [[*row] for row in rows],
                }
            ),
        )

    def get(self, audience_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/audiences/{audienceId}``. Requires ``ads:read``."""
        return self._client.request(
            "GET", f"/ads/audiences/{_seg(audience_id)}", query={"ad_account_id": ad_account_id}
        )

    def update(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        """``PATCH /ads/audiences/{audienceId}`` - rename. Requires
        ``ads:write``."""
        return self._client.request(
            "PATCH",
            f"/ads/audiences/{_seg(audience_id)}",
            json=drop_none(
                {"ad_account_id": ad_account_id, "name": name, "description": description}
            ),
        )

    def delete(self, audience_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``DELETE /ads/audiences/{audienceId}``. Requires ``ads:write``."""
        return self._client.request(
            "DELETE", f"/ads/audiences/{_seg(audience_id)}", query={"ad_account_id": ad_account_id}
        )

    def add_members(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        schema: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> Any:
        """``POST /ads/audiences/{audienceId}/members`` - add people to a
        customer list. Send the raw values: OmniSocials normalizes them and
        hashes them with SHA-256 before they leave and stores nothing. At
        most 10,000 rows. ``schema`` keys: email, phone, first_name,
        last_name, city, state, zip, country, external_id, dob_year, gender,
        maid. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/audiences/{_seg(audience_id)}/members",
            json={
                "ad_account_id": ad_account_id,
                "schema": [*schema],
                "rows": [[*row] for row in rows],
            },
        )

    def remove_members(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        schema: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> Any:
        """``DELETE /ads/audiences/{audienceId}/members`` - remove people
        (the same body as ``add_members()``). Requires ``ads:write``."""
        return self._client.request(
            "DELETE",
            f"/ads/audiences/{_seg(audience_id)}/members",
            json={
                "ad_account_id": ad_account_id,
                "schema": [*schema],
                "rows": [[*row] for row in rows],
            },
        )

    def add_companies(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        companies: Sequence[Mapping[str, Any]],
    ) -> Any:
        """``POST /ads/audiences/{audienceId}/companies`` - add companies
        (``name``, ``domain``, ``linkedin_url``) to a company list
        (LinkedIn). Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/audiences/{_seg(audience_id)}/companies",
            json={"ad_account_id": ad_account_id, "companies": [*companies]},
        )


class AdLeadForms:
    """Lead forms (Meta: the workspace's Page). ``form_id`` is the
    OmniSocials form id; a form's ``external_id`` goes in
    ``settings["lead_form_id"]``."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/lead-forms``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/lead-forms", query={"ad_account_id": ad_account_id}
        )

    def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        privacy_policy_url: str,
        questions: Sequence[Mapping[str, Any]],
        thank_you: Mapping[str, Any],
        locale: Optional[str] = None,
        headline: Optional[str] = None,
        description: Optional[str] = None,
        accept_terms: Optional[bool] = None,
    ) -> Any:
        """``POST /ads/lead-forms``. ``accept_terms=True`` says the person
        accepts the network's lead ad terms (Pinterest refuses a form
        without it): only send it after the person said yes. Requires
        ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/lead-forms",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "privacy_policy_url": privacy_policy_url,
                    "locale": locale,
                    "headline": headline,
                    "description": description,
                    "questions": [*questions],
                    "thank_you": thank_you,
                    "accept_terms": accept_terms,
                }
            ),
        )

    def get(self, form_id: Union[int, str]) -> Any:
        """``GET /ads/lead-forms/{formId}``. Requires ``ads:read``."""
        return self._client.request("GET", f"/ads/lead-forms/{_seg(form_id)}")

    def update(
        self,
        form_id: Union[int, str],
        *,
        status: Optional[str] = None,
        sync_enabled: Optional[bool] = None,
    ) -> Any:
        """``PATCH /ads/lead-forms/{formId}`` - archive or open a form
        (``status`` ``archived`` or ``active``), or switch its lead sync.
        Requires ``ads:write``."""
        return self._client.request(
            "PATCH",
            f"/ads/lead-forms/{_seg(form_id)}",
            json=drop_none({"status": status, "sync_enabled": sync_enabled}),
        )

    def delete(self, form_id: Union[int, str]) -> Any:
        """``DELETE /ads/lead-forms/{formId}`` - archive a form (the leads
        already copied stay). Requires ``ads:write``."""
        return self._client.request("DELETE", f"/ads/lead-forms/{_seg(form_id)}")

    def send_test_lead(
        self, form_id: Union[int, str], *, fields: Optional[Mapping[str, Any]] = None
    ) -> Any:
        """``POST /ads/lead-forms/{formId}/test-leads`` - a test lead (the
        next sync copies it, marked ``is_test``). Requires ``ads:write``."""
        return self._client.request(
            "POST", f"/ads/lead-forms/{_seg(form_id)}/test-leads", json=drop_none({"fields": fields})
        )


class AdLeads:
    """Leads of the workspace, copied from the networks every 15 minutes
    (webhook ``lead.received``). The answers are personal data."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        *,
        form_id: Optional[Union[int, str]] = None,
        status: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/leads`` - newest first (``limit`` at most 200).
        Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/leads",
            query={
                "form_id": form_id,
                "status": status,
                "since": since,
                "until": until,
                "limit": limit,
                "cursor": cursor,
            },
        )

    def counts(self, *, form_id: Optional[Union[int, str]] = None) -> Any:
        """``GET /ads/leads/counts`` - ``total`` and ``by_status``. Requires
        ``ads:read``."""
        return self._client.request("GET", "/ads/leads/counts", query={"form_id": form_id})

    def update(
        self,
        lead_id: Union[int, str],
        *,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Any:
        """``PATCH /ads/leads/{leadId}`` - ``status`` is ``new``,
        ``contacted``, ``qualified``, ``won``, ``lost`` or ``spam``.
        Requires ``ads:write``."""
        return self._client.request(
            "PATCH",
            f"/ads/leads/{_seg(lead_id)}",
            json=drop_none({"status": status, "note": note}),
        )


class AdConversions:
    """Pixels, conversion goals, custom conversions and server-side
    conversion events."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def destinations(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/conversions/destinations`` - pixels, datasets,
        conversion tags and conversion actions. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/conversions/destinations", query={"ad_account_id": ad_account_id}
        )

    def goals(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/conversions/goals`` - the events a campaign can
        optimise for. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/conversions/goals", query={"ad_account_id": ad_account_id}
        )

    def create_custom(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        destination_id: str,
        event: Optional[str] = None,
        url_contains: Optional[str] = None,
    ) -> Any:
        """``POST /ads/conversions/custom`` - a custom conversion (a URL rule
        and/or an event on a pixel). Requires ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/conversions/custom",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "destination_id": destination_id,
                    "event": event,
                    "url_contains": url_contains,
                }
            ),
        )

    def send_events(
        self,
        *,
        ad_account_id: Union[int, str],
        destination_id: str,
        events: Sequence[Mapping[str, Any]],
    ) -> Any:
        """``POST /ads/conversions/events`` - up to 1,000 conversion events
        from your server. Send the raw email and phone: OmniSocials
        normalizes and SHA-256 hashes them before they leave and stores
        nothing. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/conversions/events",
            json={
                "ad_account_id": ad_account_id,
                "destination_id": destination_id,
                "events": [*events],
            },
        )


class AdInsights:
    """Numbers: live from the network, per campaign or ad, over time, ranked,
    and what needs attention."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def query(
        self,
        *,
        ad_account_id: Union[int, str],
        level: Optional[str] = None,
        ids: Optional[Sequence[str]] = None,
        metrics: Optional[Sequence[str]] = None,
        breakdowns: Optional[Sequence[str]] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        time_increment: Optional[str] = None,
    ) -> Any:
        """``POST /ads/insights`` - live numbers from the network by day, ad,
        country, age, gender, placement, device or platform (at most 2
        ``breakdowns``). Read-only. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/insights",
            json=_insights_body(
                ad_account_id=ad_account_id,
                level=level,
                ids=ids,
                metrics=metrics,
                breakdowns=breakdowns,
                from_=from_,
                to=to,
                time_increment=time_increment,
            ),
        )

    def campaign(
        self,
        campaign_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        breakdown: Optional[str] = None,
        time_increment: Optional[str] = None,
        metrics: Union[str, Sequence[str], None] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/analytics`` - numbers of an OmniSocials
        campaign (``breakdown="ad"`` gives one row per ad). Requires
        ``ads:read``."""
        return self._client.request(
            "GET",
            f"/ads/campaigns/{_seg(campaign_id)}/analytics",
            query={
                "from": from_,
                "to": to,
                "breakdown": breakdown,
                "time_increment": time_increment,
                "metrics": join_list(metrics),
            },
        )

    def ad(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        breakdown: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/analytics`` - numbers of one
        ad. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            f"{_ad_path(campaign_id, ad_id)}/analytics",
            query={"from": from_, "to": to, "breakdown": breakdown},
        )

    def timeline(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        platform: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Any:
        """``GET /ads/timeline`` - daily totals of the workspace (``source``
        ``all``, ``omnisocials`` or ``external``). Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/timeline",
            query={"from": from_, "to": to, "platform": platform, "source": source},
        )

    def performance(
        self,
        *,
        level: Optional[str] = None,
        metric: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        min_impressions: Optional[int] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Any:
        """``GET /ads/performance`` - campaigns or ads ranked by one metric.
        Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/performance",
            query={
                "level": level,
                "metric": metric,
                "order": order,
                "limit": limit,
                "min_impressions": min_impressions,
                "from": from_,
                "to": to,
                "platform": platform,
            },
        )

    def alerts(self) -> Any:
        """``GET /ads/alerts`` - rejected ads, held campaigns, sign-in or
        payment problems, no delivery. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/alerts")


class AdReports:
    """Long reports that run in the background (up to 730 days)."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /ads/insights/reports``. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/insights/reports")

    def start(
        self,
        *,
        ad_account_id: Union[int, str],
        level: Optional[str] = None,
        ids: Optional[Sequence[str]] = None,
        metrics: Optional[Sequence[str]] = None,
        breakdowns: Optional[Sequence[str]] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        time_increment: Optional[str] = None,
    ) -> Any:
        """``POST /ads/insights/reports`` - start a report with the fields of
        ``ads.insights.query()``; poll ``get()``. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/insights/reports",
            json=_insights_body(
                ad_account_id=ad_account_id,
                level=level,
                ids=ids,
                metrics=metrics,
                breakdowns=breakdowns,
                from_=from_,
                to=to,
                time_increment=time_increment,
            ),
        )

    def get(self, report_id: str) -> Any:
        """``GET /ads/insights/reports/{reportId}`` - ``running``, ``done``
        (with ``rows``) or ``failed``. Requires ``ads:read``."""
        return self._client.request("GET", f"/ads/insights/reports/{_seg(report_id)}")


class AdRules:
    """Automated rules: check campaigns on a schedule and notify, pause,
    activate or adjust the budget. A rule that notifies, pauses or lowers a
    budget works with ``ads:write``. A rule that can raise spend
    (``activate``, a positive ``adjust_budget``) needs a key with
    ``ads:spend`` (else ``403 rule_raises_spend``) and
    ``action["max_daily_budget"]``, confirmed by the person as
    ``confirm_max_daily_budget``; it never acts on Google. ``create``,
    ``update`` and ``undo`` are not retried after a 5xx, a timeout or a lost
    connection."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /ads/rules``. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/rules")

    def create(
        self,
        *,
        name: str,
        conditions: Sequence[Mapping[str, Any]],
        action: Mapping[str, Any],
        ad_account_id: Optional[Union[int, str]] = None,
        enabled: Optional[bool] = None,
        scope: Optional[Mapping[str, Any]] = None,
        every_minutes: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        confirm_max_daily_budget: Optional[float] = None,
    ) -> Any:
        """``POST /ads/rules`` - a new rule, off until ``enabled=True``.

        A rule that can RAISE REAL AD SPEND (``activate``, a positive
        ``adjust_budget``) needs the person's own ceiling as
        ``confirm_max_daily_budget`` and a key with ``ads:spend`` (else
        ``403 rule_raises_spend``). Preview it first with ``preview()``. Not
        retried after a 5xx, a timeout or a lost connection: read the rules
        with ``list()``. Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            "/ads/rules",
            json=_rule_body(
                name=name,
                conditions=conditions,
                action=action,
                ad_account_id=ad_account_id,
                enabled=enabled,
                scope=scope,
                every_minutes=every_minutes,
                cooldown_minutes=cooldown_minutes,
                max_actions_per_run=max_actions_per_run,
                confirm_max_daily_budget=confirm_max_daily_budget,
            ),
            retry=RATE_LIMIT_ONLY,
        )

    def templates(self) -> Any:
        """``GET /ads/rules/templates`` - ready-made rules. Requires
        ``ads:read``."""
        return self._client.request("GET", "/ads/rules/templates")

    def preview(
        self,
        *,
        conditions: Sequence[Mapping[str, Any]],
        action: Mapping[str, Any],
        name: Optional[str] = None,
        ad_account_id: Optional[Union[int, str]] = None,
        scope: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/rules/preview`` - what an unsaved rule would match and
        do now. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/rules/preview",
            json=drop_none(
                {
                    "name": name,
                    "ad_account_id": ad_account_id,
                    "scope": scope,
                    "conditions": [*conditions],
                    "action": action,
                }
            ),
        )

    def activity(
        self, *, rule_id: Optional[Union[int, str]] = None, limit: Optional[int] = None
    ) -> Any:
        """``GET /ads/rules/activity`` - every change the rules made, with
        before and after. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/rules/activity", query={"rule_id": rule_id, "limit": limit}
        )

    def undo(
        self, activity_id: Union[int, str], *, confirm_budget_amount: Optional[float] = None
    ) -> Any:
        """``POST /ads/rules/activity/{activityId}/undo`` - undo a change a
        rule made.

        Undo of a pause or of a budget cut RESTARTS or RAISES REAL AD SPEND:
        pass the amount as ``confirm_budget_amount`` after the person agreed,
        with a key that has ``ads:spend`` (else, and on Google always,
        ``403 start_in_app``). Not retried after a 5xx, a timeout or a lost
        connection. Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            f"/ads/rules/activity/{_seg(activity_id)}/undo",
            json=drop_none({"confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    def get(self, rule_id: Union[int, str]) -> Any:
        """``GET /ads/rules/{ruleId}``. Requires ``ads:read``."""
        return self._client.request("GET", f"/ads/rules/{_seg(rule_id)}")

    def update(
        self,
        rule_id: Union[int, str],
        *,
        name: Optional[str] = None,
        conditions: Optional[Sequence[Mapping[str, Any]]] = None,
        action: Optional[Mapping[str, Any]] = None,
        ad_account_id: Optional[Union[int, str]] = None,
        enabled: Optional[bool] = None,
        scope: Optional[Mapping[str, Any]] = None,
        every_minutes: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        confirm_max_daily_budget: Optional[float] = None,
    ) -> Any:
        """``PATCH /ads/rules/{ruleId}`` - change a rule (also ``enabled``). A
        changed action that can raise spend needs ``confirm_max_daily_budget``
        again and a key with ``ads:spend`` (else ``403 rule_raises_spend``).
        Not retried after a 5xx, a timeout or a lost connection. Requires
        ``ads:write``."""
        return self._client.request(
            "PATCH",
            f"/ads/rules/{_seg(rule_id)}",
            json=_rule_body(
                name=name,
                conditions=conditions,
                action=action,
                ad_account_id=ad_account_id,
                enabled=enabled,
                scope=scope,
                every_minutes=every_minutes,
                cooldown_minutes=cooldown_minutes,
                max_actions_per_run=max_actions_per_run,
                confirm_max_daily_budget=confirm_max_daily_budget,
            ),
            retry=RATE_LIMIT_ONLY,
        )

    def delete(self, rule_id: Union[int, str]) -> Any:
        """``DELETE /ads/rules/{ruleId}``. Requires ``ads:write``."""
        return self._client.request("DELETE", f"/ads/rules/{_seg(rule_id)}")

    def preview_saved(self, rule_id: Union[int, str]) -> Any:
        """``POST /ads/rules/{ruleId}/preview`` - what a saved rule would
        match and do now. Requires ``ads:read``."""
        return self._client.request("POST", f"/ads/rules/{_seg(rule_id)}/preview")

    def runs(self, rule_id: Union[int, str], *, limit: Optional[int] = None) -> Any:
        """``GET /ads/rules/{ruleId}/runs``. Requires ``ads:read``."""
        return self._client.request(
            "GET", f"/ads/rules/{_seg(rule_id)}/runs", query={"limit": limit}
        )


class AdResults:
    """Your own numbers per campaign and day (qualified leads, sales,
    revenue). Rules read them as ``results.<metric>``."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
        metric: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaign-results``. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/campaign-results",
            query={"from": from_, "to": to, "campaign_id": campaign_id, "metric": metric},
        )

    def upload(self, rows: Sequence[Mapping[str, Any]]) -> Any:
        """``POST /ads/campaign-results`` - up to 5,000 rows of ``day``,
        ``metric``, ``value`` and the campaign (``campaign_id``,
        ``external_campaign_id`` + ``platform``, ``utm_campaign`` or
        ``campaign_name``). Sending a day again replaces it. Requires
        ``ads:write``."""
        return self._client.request("POST", "/ads/campaign-results", json={"rows": [*rows]})

    def totals(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
    ) -> Any:
        """``GET /ads/campaign-results/totals`` - totals over a period, with
        the formulas. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/campaign-results/totals",
            query={"from": from_, "to": to, "campaign_id": campaign_id},
        )

    def metrics(self) -> Any:
        """``GET /ads/campaign-results/metrics`` - your metric names and
        formulas. Requires ``ads:read``."""
        return self._client.request("GET", "/ads/campaign-results/metrics")

    def put_metric(
        self,
        key: str,
        *,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        formula: Optional[str] = None,
    ) -> Any:
        """``PUT /ads/campaign-results/metrics/{key}`` - name a metric or
        define a formula (``unit`` ``number``, ``money`` or ``percent``).
        Requires ``ads:write``."""
        return self._client.request(
            "PUT",
            f"/ads/campaign-results/metrics/{_seg(key)}",
            json=drop_none({"label": label, "unit": unit, "formula": formula}),
        )


class AdMedia:
    """The network's own image and video library of an ad account. Use an
    id in an ad as ``network[<network>]["media_ref"]``."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        *,
        ad_account_id: Union[int, str],
        type: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/media``. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/media",
            query={"ad_account_id": ad_account_id, "type": type, "cursor": cursor},
        )

    def upload(
        self,
        *,
        ad_account_id: Union[int, str],
        type: str,
        url: str,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/media`` - upload an image or video to the network
        ahead of an ad. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/media",
            json=drop_none(
                {"ad_account_id": ad_account_id, "type": type, "url": url, "name": name}
            ),
        )

    def get(
        self, media_id: str, *, ad_account_id: Union[int, str], type: Optional[str] = None
    ) -> Any:
        """``GET /ads/media/{mediaId}`` - the processing status of an upload.
        Requires ``ads:read``."""
        return self._client.request(
            "GET",
            f"/ads/media/{_seg(media_id)}",
            query={"ad_account_id": ad_account_id, "type": type},
        )

    def delete(self, media_id: str, *, ad_account_id: Union[int, str], type: str) -> Any:
        """``DELETE /ads/media/{mediaId}``. Requires ``ads:write``."""
        return self._client.request(
            "DELETE",
            f"/ads/media/{_seg(media_id)}",
            query={"ad_account_id": ad_account_id, "type": type},
        )


class AdPreviews:
    """Previews drawn by the network."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def create(
        self,
        *,
        ad_account_id: Union[int, str],
        ad: Mapping[str, Any],
        placements: Optional[Sequence[str]] = None,
        objective: Optional[str] = None,
    ) -> Any:
        """``POST /ads/previews`` - previews of a new ad (the shape of a
        draft ad). Read-only. Requires ``ads:read``."""
        return self._client.request(
            "POST",
            "/ads/previews",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "ad": ad,
                    "placements": None if placements is None else [*placements],
                    "objective": objective,
                }
            ),
        )

    def for_ad(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        placements: Union[str, Sequence[str], None] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/previews`` - previews of an
        existing ad. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            f"{_ad_path(campaign_id, ad_id)}/previews",
            query={"placements": join_list(placements)},
        )


class AdPartnership:
    """Partnership ads with creators (Meta)."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list_content(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/partnership/content`` - creator posts you may run as
        partnership ads. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/partnership/content", query={"ad_account_id": ad_account_id}
        )

    def list_permissions(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/partnership/permissions``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/partnership/permissions", query={"ad_account_id": ad_account_id}
        )

    def set_permission(self, *, ad_account_id: Union[int, str], **fields: Any) -> Any:
        """``POST /ads/partnership/permissions`` - ask for or set a
        permission; Meta's fields pass through as keyword arguments.
        Requires ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/partnership/permissions",
            json={**fields, "ad_account_id": ad_account_id},
        )


class AdAccountsAdmin:
    """Ad account admin: identities, health, finance, settings, people,
    change log, businesses, DSA and the manager hierarchy. ``account_id`` is
    the OmniSocials ad account id."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def identities(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/identities`` - Pages, profiles and
        identities an ad can run as. Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "identities"))

    def health(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/health`` - status, payment, spend
        limit, Page and pixel before an ad starts. A check that cannot be
        read is ``unknown``; failed checks carry a ``fix_url``. Requires
        ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "health"))

    def finance(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/finance`` - spend limit, amount
        spent, balance and payment method. Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "finance"))

    def update_settings(
        self,
        account_id: Union[int, str],
        *,
        spend_cap: Union[float, None, NotGiven] = NOT_GIVEN,
        dsa_beneficiary: Optional[str] = None,
        dsa_payor: Optional[str] = None,
        name: Optional[str] = None,
        confirm_budget_amount: Optional[Union[float, str]] = None,
    ) -> Any:
        """``PATCH /ads/accounts/{accountId}/settings`` - spend cap, DSA payer
        and beneficiary, name.

        A higher ``spend_cap`` ALLOWS MORE REAL AD SPEND: pass the new cap as
        ``confirm_budget_amount`` after the person agreed; ``spend_cap=None``
        removes the cap and needs ``confirm_budget_amount="remove"``. A spend
        cap change: needs a key with the opt-in ``ads:spend`` scope ("Start
        ads"); without it, and on Google (``api_draft_only``) always, the call
        answers ``403 start_in_app`` with the page where a person does it in
        the app. The name and the DSA names stay open. Not retried after a
        5xx, a timeout or a lost connection. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "dsa_beneficiary": dsa_beneficiary,
                "dsa_payor": dsa_payor,
                "name": name,
                "confirm_budget_amount": confirm_budget_amount,
            }
        )
        if not isinstance(spend_cap, NotGiven):
            body["spend_cap"] = spend_cap
        return self._client.request(
            "PATCH",
            _account_path(account_id, "settings"),
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    def list_users(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/users`` - people with access.
        Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "users"))

    def add_user(
        self,
        account_id: Union[int, str],
        *,
        role: str,
        email: Optional[str] = None,
        member_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/accounts/{accountId}/users`` - give a person access
        (LinkedIn). Requires ``ads:write``."""
        return self._client.request(
            "POST",
            _account_path(account_id, "users"),
            json=drop_none({"email": email, "member_id": member_id, "role": role}),
        )

    def remove_user(self, account_id: Union[int, str], user_id: str) -> Any:
        """``DELETE /ads/accounts/{accountId}/users/{userId}`` - remove a
        person's access. Requires ``ads:write``."""
        return self._client.request(
            "DELETE", _account_path(account_id, f"users/{_seg(user_id)}")
        )

    def activity(
        self,
        account_id: Union[int, str],
        *,
        since: Optional[str] = None,
        until: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/accounts/{accountId}/activity`` - the change log of the
        ad account. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            _account_path(account_id, "activity"),
            query={"since": since, "until": until, "cursor": cursor},
        )

    def businesses(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/businesses`` - Meta business
        portfolios and TikTok Business Centers. Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "businesses"))

    def dsa(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/dsa`` - the EU DSA payer and
        beneficiary (Meta). Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "dsa"))

    def hierarchy(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/hierarchy`` - the manager account
        hierarchy (Google). Requires ``ads:read``."""
        return self._client.request("GET", _account_path(account_id, "hierarchy"))


class AdReachFrequency:
    """Meta reach and frequency buying. A prediction spends nothing; a
    reservation does."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def create(
        self,
        *,
        ad_account_id: Union[int, str],
        objective: str,
        targeting: Mapping[str, Any],
        start_at: str,
        end_at: str,
        budget: Optional[Mapping[str, Any]] = None,
        reach: Optional[int] = None,
        frequency_cap: Optional[int] = None,
        frequency_interval_days: Optional[int] = None,
    ) -> Any:
        """``POST /ads/reach-frequency`` - a prediction (``objective``
        ``awareness``, ``engagement`` or ``video_views``; exactly one
        country in ``targeting``; ``budget`` in major units or ``reach``).
        It spends nothing; Meta needs the reach and frequency capability on
        the ad account. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            "/ads/reach-frequency",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "objective": objective,
                    "targeting": targeting,
                    "start_at": start_at,
                    "end_at": end_at,
                    "budget": budget,
                    "reach": reach,
                    "frequency_cap": frequency_cap,
                    "frequency_interval_days": frequency_interval_days,
                }
            ),
        )

    def get(self, prediction_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/reach-frequency/{predictionId}``. Requires
        ``ads:read``."""
        return self._client.request(
            "GET",
            f"/ads/reach-frequency/{_seg(prediction_id)}",
            query={"ad_account_id": ad_account_id},
        )

    def cancel(self, prediction_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``DELETE /ads/reach-frequency/{predictionId}`` - cancel a
        prediction or a reservation. Requires ``ads:write``."""
        return self._client.request(
            "DELETE",
            f"/ads/reach-frequency/{_seg(prediction_id)}",
            query={"ad_account_id": ad_account_id},
        )

    def reserve(
        self,
        prediction_id: str,
        *,
        ad_account_id: Union[int, str],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/reach-frequency/{predictionId}/reserve`` - COMMITS REAL
        AD SPEND: pass the prediction's budget as ``confirm_budget_amount``
        after the person agreed. Needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Not retried after a 5xx, a timeout or a
        lost connection: read the prediction with ``get()``. Requires
        ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/reach-frequency/{_seg(prediction_id)}/reserve",
            json={"ad_account_id": ad_account_id, "confirm_budget_amount": confirm_budget_amount},
            retry=RATE_LIMIT_ONLY,
        )


class AdStudies:
    """A/B tests and lift studies (Meta)."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/studies``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/studies", query={"ad_account_id": ad_account_id}
        )

    def create(self, *, ad_account_id: Union[int, str], **fields: Any) -> Any:
        """``POST /ads/studies`` - an A/B test between existing campaigns or
        ad sets; Meta's fields pass through as keyword arguments. Needs a key
        with the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Requires ``ads:write``."""
        return self._client.request(
            "POST", "/ads/studies", json={**fields, "ad_account_id": ad_account_id}
        )


class AdBudgetSchedules:
    """Planned budget increases of a campaign for high-demand periods
    (Meta)."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/budget-schedules``. Requires
        ``ads:read``."""
        return self._client.request(
            "GET", f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules"
        )

    def create(
        self,
        campaign_id: Union[int, str],
        *,
        start_at: str,
        end_at: str,
        budget_increase: Mapping[str, Any],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/campaigns/{id}/budget-schedules`` - plan a budget
        increase (``budget_increase={"type": "absolute" | "multiplier",
        "value": ...}``).

        NEW REAL AD SPEND in that period: pass the increase per day (absolute)
        or the campaign budget times the multiplier as
        ``confirm_budget_amount`` after the person agreed. Needs a key with
        the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Not retried after a 5xx, a timeout or a lost connection: read the
        schedules with ``list()``. Requires ``ads:write``.
        """
        return self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules",
            json={
                "start_at": start_at,
                "end_at": end_at,
                "budget_increase": budget_increase,
                "confirm_budget_amount": confirm_budget_amount,
            },
            retry=RATE_LIMIT_ONLY,
        )

    def delete(self, campaign_id: Union[int, str], schedule_id: str) -> Any:
        """``DELETE /ads/campaigns/{id}/budget-schedules/{scheduleId}``.
        Requires ``ads:write``."""
        return self._client.request(
            "DELETE",
            f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules/{_seg(schedule_id)}",
        )


class AdGoogle:
    """Google reports (read-only; every API caller stops at the draft on
    Google)."""

    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def search_terms(
        self,
        *,
        ad_account_id: Union[int, str],
        campaign_id: Optional[Union[int, str]] = None,
        external_campaign_id: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """``GET /ads/google/search-terms``. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/google/search-terms",
            query={
                "ad_account_id": ad_account_id,
                "campaign_id": campaign_id,
                "external_campaign_id": external_campaign_id,
                "from": from_,
                "to": to,
                "limit": limit,
            },
        )

    def recommendations(
        self, *, ad_account_id: Union[int, str], types: Union[str, Sequence[str], None] = None
    ) -> Any:
        """``GET /ads/google/recommendations``. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/google/recommendations",
            query={"ad_account_id": ad_account_id, "types": join_list(types)},
        )

    def keywords(
        self,
        *,
        ad_account_id: Union[int, str],
        external_campaign_id: Optional[str] = None,
        external_ad_set_id: Optional[str] = None,
    ) -> Any:
        """``GET /ads/google/keywords`` - search keywords and negative
        keywords. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/google/keywords",
            query={
                "ad_account_id": ad_account_id,
                "external_campaign_id": external_campaign_id,
                "external_ad_set_id": external_ad_set_id,
            },
        )

    def assets(self, *, ad_account_id: Union[int, str], type: Optional[str] = None) -> Any:
        """``GET /ads/google/assets`` - sitelinks, callouts and structured
        snippets. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/google/assets", query={"ad_account_id": ad_account_id, "type": type}
        )

    def shared_budgets(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/shared-budgets``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/google/shared-budgets", query={"ad_account_id": ad_account_id}
        )

    def bid_strategies(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/bid-strategies`` - portfolio bid strategies.
        Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/google/bid-strategies", query={"ad_account_id": ad_account_id}
        )

    def ad_schedule(
        self, *, ad_account_id: Union[int, str], external_campaign_id: str
    ) -> Any:
        """``GET /ads/google/ad-schedule`` - the days and hours of a Google
        campaign. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/google/ad-schedule",
            query={"ad_account_id": ad_account_id, "external_campaign_id": external_campaign_id},
        )

    def labels(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/labels``. Requires ``ads:read``."""
        return self._client.request(
            "GET", "/ads/google/labels", query={"ad_account_id": ad_account_id}
        )

    def local_services_leads(
        self, *, ad_account_id: Union[int, str], since: Optional[str] = None
    ) -> Any:
        """``GET /ads/google/local-services-leads``. Requires ``ads:read``."""
        return self._client.request(
            "GET",
            "/ads/google/local-services-leads",
            query={"ad_account_id": ad_account_id, "since": since},
        )

class Ads:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client
        self.drafts = AdDrafts(client)
        #: Campaigns, ad sets and ads of an ad account, also the ones made outside OmniSocials, and their import.
        self.objects = AdObjects(client)
        #: The ads of an OmniSocials campaign.
        self.campaign_ads = AdCampaignAds(client)
        #: Comments on ads.
        self.comments = AdComments(client)
        #: Targeting search, browse, reach estimate and bid suggestions.
        self.targeting = AdTargeting(client)
        #: Custom audiences: customer lists, lookalikes, company lists.
        self.audiences = AdAudiences(client)
        #: Lead forms.
        self.lead_forms = AdLeadForms(client)
        #: Leads copied from the lead forms.
        self.leads = AdLeads(client)
        #: Pixels, conversion goals, custom conversions, server-side events.
        self.conversions = AdConversions(client)
        #: Live numbers, campaign and ad analytics, timeline, ranking, alerts.
        self.insights = AdInsights(client)
        #: Background reports.
        self.reports = AdReports(client)
        #: Automated rules.
        self.rules = AdRules(client)
        #: Your own numbers per campaign and day.
        self.results = AdResults(client)
        #: The network's own image and video library.
        self.media = AdMedia(client)
        #: Previews drawn by the network.
        self.previews = AdPreviews(client)
        #: Partnership ads (Meta).
        self.partnership = AdPartnership(client)
        #: Ad account admin (health, finance, settings, people, change log).
        self.accounts = AdAccountsAdmin(client)
        #: Meta reach and frequency.
        self.reach_frequency = AdReachFrequency(client)
        #: A/B tests and lift studies (Meta).
        self.studies = AdStudies(client)
        #: Planned budget increases (Meta).
        self.budget_schedules = AdBudgetSchedules(client)
        #: Google reports.
        self.google = AdGoogle(client)

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
        ``coming_soon``), and per network the ``features`` its API offers,
        ``targeting_types``, ``bid_strategies``, ``settings`` and
        ``ad_fields``, plus ``api_goals``, ``api_draft_only`` (networks where
        every API caller stops at the draft, also a key with ``ads:spend``:
        Google) and ``api_stop_in_app`` (networks where the API may not even
        pause or delete a campaign that reached the network: Google). Requires
        ``ads:read``."""
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
        """``POST /ads/boost`` - boost a published post. Creates a DRAFT boost
        that spends nothing; the person starts it in the app. ``budget`` is
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

    def update(
        self,
        campaign_id: Union[int, str],
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        confirm_budget_amount: Optional[float] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        objective: Optional[str] = None,
        settings: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /ads/campaigns/{id}`` - change the name, budget, targeting
        or schedule of a draft; ``objective`` and ``settings`` only while the
        campaign is a draft (``400 settings_locked`` after the start:
        duplicate it).

        A campaign that reached the network changes only with a key that has
        ``ads:spend``; without it, and on Google always, the call answers
        ``403 start_in_app`` and a person changes it in the app. A higher
        budget on a running campaign RAISES REAL AD SPEND: show the person the
        new amount and get their yes first, then pass it again as
        ``confirm_budget_amount``. Not retried after a 5xx, a timeout or a
        lost connection: read the campaign with ``get()`` to see what
        happened. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "name": name,
                "budget": budget,
                "confirm_budget_amount": confirm_budget_amount,
                "targeting": targeting,
                "schedule": schedule,
                "objective": objective,
                "settings": settings,
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

        Needs a key with the opt-in ``ads:spend`` scope ("Start ads"); without
        it, and on Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
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

        Needs a key with ``ads:spend``: without it, and on Google always, a
        result answers ``ok: false`` with code ``start_in_app`` and the page
        where a person starts it. Every campaign's budget must equal
        ``confirm_budget_amount``; show the person the total (amount x
        campaigns) and get their yes first. Answers ``{"results": [...]}``.
        Not retried after a 5xx, a timeout or a lost connection: read the
        campaigns with ``get()`` to see what happened. Requires ``ads:write``.
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
        in review). Open with ``ads:write``, except on the networks in
        ``api_stop_in_app`` (Google): there a campaign that reached the
        network answers ``403 start_in_app``. Requires ``ads:write``."""
        return self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/pause"
        )

    def resume(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/resume`` - resume a paused campaign: it
        STARTS REAL AD SPEND again. Needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Only a paused campaign resumes
        (``409 not_paused``). Show the person the budget and get their yes
        first. Not retried after a 5xx, a timeout or a lost connection: read
        the campaign with ``get()`` to see what happened. Requires
        ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/resume",
            retry=RATE_LIMIT_ONLY,
        )

    def bulk_status(
        self,
        *,
        campaign_ids: Sequence[Union[int, str]],
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``POST /ads/campaigns/bulk-status`` - pause or resume up to 50
        campaigns (``status`` ``paused`` or ``active``).

        Resuming RESTARTS REAL AD SPEND: every campaign's budget must equal
        ``confirm_budget_amount`` (one amount for all), checked before any
        change; show the person the total and get their yes first. Resuming
        needs a key with ``ads:spend``: without it, and on Google always, a
        result answers ``start_in_app``. Pausing stays open (Google:
        ``start_in_app``). Answers ``{"data": {"results": [...]}}``. Not
        retried after a 5xx, a timeout or a lost connection. Requires
        ``ads:write``.
        """
        return self._client.request(
            "POST",
            "/ads/campaigns/bulk-status",
            json=drop_none(
                {
                    "campaign_ids": [*campaign_ids],
                    "status": status,
                    "confirm_budget_amount": confirm_budget_amount,
                }
            ),
            retry=RATE_LIMIT_ONLY,
        )

    def duplicate(self, campaign_id: Union[int, str], *, name: Optional[str] = None) -> Any:
        """``POST /ads/campaigns/{id}/duplicate`` - copy a campaign as a new
        draft (same ad account, goal, budget, targeting, settings and ads).
        A draft never spends. Requires ``ads:write``."""
        return self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/duplicate",
            json=drop_none({"name": name}),
        )

    def delete(self, campaign_id: Union[int, str]) -> Any:
        """``DELETE /ads/campaigns/{id}`` - delete a campaign on the network
        too. A campaign that spent is archived: its spend stays in the totals.
        Open with ``ads:write``, except on the networks in ``api_stop_in_app``
        (Google): there a campaign that reached the network answers
        ``403 start_in_app``. Requires ``ads:write``."""
        return self._client.request(
            "DELETE", f"/ads/campaigns/{_seg(campaign_id)}"
        )

    def overview(self) -> Any:
        """``GET /ads/overview`` - accounts, campaigns per status and the
        totals. ``totals["spend"]`` is ``None`` when the campaigns use more
        than one currency (``totals["currency"]`` names the one currency):
        read ``totals_by_currency`` then, one row per currency with
        ``currency``, ``spend``, ``impressions`` and ``clicks`` (spend is
        never added across currencies). Requires ``ads:read``."""
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
    each with the same ads. A draft never spends; ``launch()`` starts it (a
    key with ``ads:spend``), or a person does in the app from its
    ``review_url``."""

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
        ``video_views``; through the API also ``lead_generation``,
        ``conversions``, ``messages`` or ``calls`` (each network's goal in
        ``ads.capabilities()`` says what it ``needs``). ``platforms`` lists
        network keys (``meta``, ``pinterest``, ``tiktok``, ``linkedin``,
        ``x``, ``google``) or ``{"platform": ..., "budget_amount": ...,
        "ad_account_id": ..., "settings": {...}}`` per network (``settings``:
        bidding, conversion goal, lead form, messaging). ``budget`` is the daily amount per network,
        ``{"amount": 10, "currency": "EUR"}``. ``schedule`` is
        ``{"duration_days": 7}`` (``None`` runs until it is stopped).
        ``targeting`` needs ``countries``; ``automatic_audience=True`` lets
        the network find the audience; ``networks={"meta": {"include":
        {...}, "exclude": {...}, "audiences": {...}}}`` adds each network's
        own targeting (ids from ``ads.targeting.search()``). Each of ``ads`` has ``media``,
        ``primary_text``, ``link`` and optionally ``headline``,
        ``description``, ``cta``, ``primary_text_b`` (an A/B test),
        ``network`` (per network extras such as ``lead_form_id``,
        ``media_ref``, ``spark_auth_code`` or Google's
        ``responsive_search_ad``) and, on Meta,
        ``placement_media={"stories_reels": {...}}`` (an upright 9:16 file
        for Stories and Reels).

        Read ``ads.capabilities()`` first for what each network accepts. The
        answer carries ``review_url`` (the builder in the dashboard, where the
        person checks and starts the ad: hand it over) and per network
        ``readiness``. A ``budget["currency"]`` other than the attached ad
        account's currency answers ``400 currency_mismatch`` with
        ``param: "budget.currency"``. Requires ``ads:write``.
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
        body (the same fields as ``create()``). Networks that already started
        are left alone (``campaigns[].editable``). A ``budget["currency"]``
        other than the attached ad account's currency answers
        ``400 currency_mismatch`` with ``param: "budget.currency"``. Requires
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

        Needs a key with the opt-in ``ads:spend`` scope ("Start ads"): without
        it the call answers ``403 start_in_app`` with the draft's page (its
        ``review_url``), and a network in ``api_draft_only`` (Google) is
        always skipped with code ``start_in_app``. Show the person the daily
        amount per network and get their yes first, then pass it as
        ``confirm_budget_amount`` (or per campaign id as
        ``confirm_budget_amounts``). A wrong or missing amount answers
        ``400 budget_confirmation_required`` and writes nothing. The answer is
        ``{"data": {"group": ..., "results": [...]}}`` with a result per
        network (``campaign_id`` is a string); one failed network never stops
        the others. Not retried after a 5xx, a timeout or a lost connection:
        read the draft with ``get()`` to see what started. Requires
        ``ads:write``.
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


class AsyncAdObjects:
    """Campaigns, ad sets and ads of an ad account as the network has them,
    also the ones made outside OmniSocials, and the import of those
    campaigns. ``level`` is ``campaign``, ``ad_set`` or ``ad``. Objects of
    OmniSocials campaigns answer ``409 use_campaign_routes``: change those
    with the campaign methods."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def tree(
        self,
        account_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        status: Union[str, Sequence[str], None] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/accounts/{accountId}/tree`` - campaigns, ad sets and ads
        with the numbers of the date range (``from_`` / ``to``, ISO dates; at
        most 90 days, default the last 30). Each campaign says ``source``
        (``omnisocials`` or ``external``). ``status`` is a list or a comma
        list. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            f"/ads/accounts/{_seg(account_id)}/tree",
            query={
                "from": from_,
                "to": to,
                "status": join_list(status),
                "limit": limit,
                "cursor": cursor,
            },
        )

    async def get(self, account_id: Union[int, str], level: str, external_id: str) -> Any:
        """``GET /ads/accounts/{accountId}/objects/{level}/{externalId}`` -
        live details of one object. Requires ``ads:read``."""
        return await self._client.request("GET", _object_path(account_id, level, external_id))

    async def update(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        end_at: Union[str, None, NotGiven] = NOT_GIVEN,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PATCH /ads/accounts/{accountId}/objects/{level}/{externalId}`` -
        change the name, budget or end date (``end_at=None`` removes it) of
        a campaign or ad set made outside OmniSocials.

        A higher budget RAISES REAL AD SPEND: show the person the new amount
        and get their yes first, then pass it as ``confirm_budget_amount``. It
        changes the campaign on the network: needs a key with the opt-in
        ``ads:spend`` scope ("Start ads"); without it, and on Google
        (``api_draft_only``) always, the call answers ``403 start_in_app``
        with the page where a person does it in the app. Not retried after a
        5xx, a timeout or a lost connection: read the object with ``get()``.
        Requires ``ads:write``.
        """
        body = drop_none(
            {"name": name, "budget": budget, "confirm_budget_amount": confirm_budget_amount}
        )
        if not isinstance(end_at, NotGiven):
            body["end_at"] = end_at
        return await self._client.request(
            "PATCH",
            _object_path(account_id, level, external_id),
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    async def set_status(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PUT /ads/accounts/{accountId}/objects/{level}/{externalId}/status``
        - ``status`` is ``paused`` or ``active``.

        Switching on STARTS REAL AD SPEND: pass the budget that pays (the
        object's own or its parent's) as ``confirm_budget_amount`` after the
        person agreed. Switching on: needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Pausing needs nothing and stays open
        (Google: ``start_in_app``). Not retried after a 5xx, a timeout or a
        lost connection. Requires ``ads:write``.
        """
        return await self._client.request(
            "PUT",
            f"{_object_path(account_id, level, external_id)}/status",
            json=drop_none({"status": status, "confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    async def duplicate(
        self,
        account_id: Union[int, str],
        level: str,
        external_id: str,
        *,
        deep: Optional[bool] = None,
        rename: Optional[str] = None,
    ) -> Any:
        """``POST /ads/accounts/{accountId}/objects/{level}/{externalId}/duplicate``
        - copy an object made outside OmniSocials; the copy is paused (Meta
        today). It changes the ad account on the network: needs a key with the
        opt-in ``ads:spend`` scope ("Start ads"); without it, and on Google
        (``api_draft_only``) always, the call answers ``403 start_in_app``
        with the page where a person does it in the app. Requires
        ``ads:write``."""
        return await self._client.request(
            "POST",
            f"{_object_path(account_id, level, external_id)}/duplicate",
            json=drop_none({"deep": deep, "rename": rename}),
        )

    async def import_status(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/import`` - the import state of the
        campaigns made outside OmniSocials. Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "import"))

    async def start_import(self, account_id: Union[int, str]) -> Any:
        """``POST /ads/accounts/{accountId}/import`` - read the ad account
        again at the next sync (within 15 minutes). The first import reads
        90 days; webhook ``ads.initial_sync_completed`` when it is done.
        Requires ``ads:write``."""
        return await self._client.request("POST", _account_path(account_id, "import"))

    async def list_external(
        self,
        *,
        ad_account_id: Optional[Union[int, str]] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """``GET /ads/external-campaigns`` - the imported campaigns (``limit``
        at most 200). Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/external-campaigns",
            query={
                "ad_account_id": ad_account_id,
                "platform": platform,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get_external(
        self,
        campaign_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
    ) -> Any:
        """``GET /ads/external-campaigns/{id}`` - one imported campaign with
        its daily numbers. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            f"/ads/external-campaigns/{_seg(campaign_id)}",
            query={"from": from_, "to": to},
        )


class AsyncAdCampaignAds:
    """The ads of an OmniSocials campaign."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads`` - the ads with their status, review
        and latest numbers. Requires ``ads:read``."""
        return await self._client.request("GET", f"/ads/campaigns/{_seg(campaign_id)}/ads")

    async def add(self, campaign_id: Union[int, str], ads: Sequence[Mapping[str, Any]]) -> Any:
        """``POST /ads/campaigns/{id}/ads`` - add up to 6 ads (the shape of a
        draft ad) to a campaign that runs. They are created PAUSED on the
        network; switch each one on with ``set_status()``. Needs a key with
        the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Webhook ``ad.created``. Requires ``ads:write``."""
        return await self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/ads", json={"ads": [*ads]}
        )

    async def get(self, campaign_id: Union[int, str], ad_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}`` - one ad. Requires
        ``ads:read``."""
        return await self._client.request("GET", _ad_path(campaign_id, ad_id))

    async def set_status(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``PUT /ads/campaigns/{id}/ads/{adId}/status`` - ``paused`` or
        ``active``.

        Switching on STARTS REAL AD SPEND: pass the campaign budget as
        ``confirm_budget_amount`` after the person agreed. Switching on: needs
        a key with the opt-in ``ads:spend`` scope ("Start ads"); without it,
        and on Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Pausing stays open (Google: ``start_in_app``). Not retried after a
        5xx, a timeout or a lost connection. Webhook ``ad.updated``. Requires
        ``ads:write``.
        """
        return await self._client.request(
            "PUT",
            f"{_ad_path(campaign_id, ad_id)}/status",
            json=drop_none({"status": status, "confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    async def review(self, campaign_id: Union[int, str], ad_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/review`` - the network's review
        verdict (``in_review``, ``approved`` or ``rejected`` with reasons).
        Requires ``ads:read``."""
        return await self._client.request("GET", f"{_ad_path(campaign_id, ad_id)}/review")


class AsyncAdComments:
    """Comments on an ad of an OmniSocials campaign."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/comments``. Requires
        ``ads:read``."""
        return await self._client.request(
            "GET", f"{_ad_path(campaign_id, ad_id)}/comments", query={"cursor": cursor}
        )

    async def reply(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
        text: str,
    ) -> Any:
        """``POST /ads/campaigns/{id}/ads/{adId}/comments/{commentId}/reply`` -
        answer a comment. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}/reply",
            json={"text": text},
        )

    async def hide(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
        hidden: bool = True,
    ) -> Any:
        """``POST /ads/campaigns/{id}/ads/{adId}/comments/{commentId}/hide`` -
        hide (default) or show a comment. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}/hide",
            json={"hidden": hidden},
        )

    async def delete(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        comment_id: str,
    ) -> Any:
        """``DELETE /ads/campaigns/{id}/ads/{adId}/comments/{commentId}``.
        Requires ``ads:write``."""
        return await self._client.request(
            "DELETE", f"{_ad_path(campaign_id, ad_id)}/comments/{_seg(comment_id)}"
        )


class AsyncAdTargeting:
    """Targeting options of a network. The ids go in
    ``targeting["networks"][<network>]["include"]`` of a draft (or
    ``targeting["network"]`` of a campaign); the types per network are
    ``ads.capabilities()`` ``targeting_types``."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def search(
        self,
        *,
        ad_account_id: Union[int, str],
        type: str,
        q: str,
        limit: Optional[int] = None,
        country: Optional[str] = None,
    ) -> Any:
        """``GET /ads/targeting/search`` - interests, places, languages, job
        titles ... (``limit`` at most 100). Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/targeting/search",
            query={
                "ad_account_id": ad_account_id,
                "type": type,
                "q": q,
                "limit": limit,
                "country": country,
            },
        )

    async def browse(self, *, ad_account_id: Union[int, str], type: str) -> Any:
        """``GET /ads/targeting/browse`` - the categories as a tree. Requires
        ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/targeting/browse",
            query={"ad_account_id": ad_account_id, "type": type},
        )

    async def reach_estimate(
        self,
        *,
        ad_account_id: Union[int, str],
        targeting: Mapping[str, Any],
        objective: Optional[str] = None,
    ) -> Any:
        """``POST /ads/targeting/reach-estimate`` - the audience size of a
        targeting (``countries``, ``age_min``, ``age_max``, ``genders``,
        ``network``). Read-only. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/targeting/reach-estimate",
            json=drop_none(
                {"ad_account_id": ad_account_id, "objective": objective, "targeting": targeting}
            ),
        )

    async def bid_suggestions(
        self,
        *,
        ad_account_id: Union[int, str],
        targeting: Mapping[str, Any],
        objective: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/targeting/bid-suggestions`` - a suggested bid and daily
        budget. Read-only. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/targeting/bid-suggestions",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "objective": objective,
                    "targeting": targeting,
                    "budget": budget,
                }
            ),
        )


class AsyncAdAudiences:
    """Custom audiences of an ad account: customer lists, lookalikes and
    company lists. ``audience_id`` is the network's audience id."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self, *, ad_account_id: Union[int, str], cursor: Optional[str] = None) -> Any:
        """``GET /ads/audiences``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/audiences", query={"ad_account_id": ad_account_id, "cursor": cursor}
        )

    async def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        description: Optional[str] = None,
        kind: Optional[str] = None,
        lookalike: Optional[Mapping[str, Any]] = None,
        customer_file_source: Optional[str] = None,
        schema: Optional[Sequence[str]] = None,
        rows: Optional[Sequence[Sequence[str]]] = None,
    ) -> Any:
        """``POST /ads/audiences`` - ``kind`` is ``customer_list``,
        ``lookalike`` (``lookalike={"source_audience_id", "country",
        "ratio"}``, ratio 0.01 to 0.2) or ``company_list``.

        ``customer_file_source`` (Meta: ``user_provided``,
        ``partner_provided`` or ``both``) is what the person says. ``schema``
        + ``rows`` are optional first members of a customer list (Pinterest
        needs them); raw values are hashed with SHA-256 before they leave.
        Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            "/ads/audiences",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "description": description,
                    "kind": kind,
                    "lookalike": lookalike,
                    "customer_file_source": customer_file_source,
                    "schema": None if schema is None else [*schema],
                    "rows": None if rows is None else [[*row] for row in rows],
                }
            ),
        )

    async def get(self, audience_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/audiences/{audienceId}``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", f"/ads/audiences/{_seg(audience_id)}", query={"ad_account_id": ad_account_id}
        )

    async def update(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        """``PATCH /ads/audiences/{audienceId}`` - rename. Requires
        ``ads:write``."""
        return await self._client.request(
            "PATCH",
            f"/ads/audiences/{_seg(audience_id)}",
            json=drop_none(
                {"ad_account_id": ad_account_id, "name": name, "description": description}
            ),
        )

    async def delete(self, audience_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``DELETE /ads/audiences/{audienceId}``. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE", f"/ads/audiences/{_seg(audience_id)}", query={"ad_account_id": ad_account_id}
        )

    async def add_members(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        schema: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> Any:
        """``POST /ads/audiences/{audienceId}/members`` - add people to a
        customer list. Send the raw values: OmniSocials normalizes them and
        hashes them with SHA-256 before they leave and stores nothing. At
        most 10,000 rows. ``schema`` keys: email, phone, first_name,
        last_name, city, state, zip, country, external_id, dob_year, gender,
        maid. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/audiences/{_seg(audience_id)}/members",
            json={
                "ad_account_id": ad_account_id,
                "schema": [*schema],
                "rows": [[*row] for row in rows],
            },
        )

    async def remove_members(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        schema: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> Any:
        """``DELETE /ads/audiences/{audienceId}/members`` - remove people
        (the same body as ``add_members()``). Requires ``ads:write``."""
        return await self._client.request(
            "DELETE",
            f"/ads/audiences/{_seg(audience_id)}/members",
            json={
                "ad_account_id": ad_account_id,
                "schema": [*schema],
                "rows": [[*row] for row in rows],
            },
        )

    async def add_companies(
        self,
        audience_id: str,
        *,
        ad_account_id: Union[int, str],
        companies: Sequence[Mapping[str, Any]],
    ) -> Any:
        """``POST /ads/audiences/{audienceId}/companies`` - add companies
        (``name``, ``domain``, ``linkedin_url``) to a company list
        (LinkedIn). Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/audiences/{_seg(audience_id)}/companies",
            json={"ad_account_id": ad_account_id, "companies": [*companies]},
        )


class AsyncAdLeadForms:
    """Lead forms (Meta: the workspace's Page). ``form_id`` is the
    OmniSocials form id; a form's ``external_id`` goes in
    ``settings["lead_form_id"]``."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/lead-forms``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/lead-forms", query={"ad_account_id": ad_account_id}
        )

    async def create(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        privacy_policy_url: str,
        questions: Sequence[Mapping[str, Any]],
        thank_you: Mapping[str, Any],
        locale: Optional[str] = None,
        headline: Optional[str] = None,
        description: Optional[str] = None,
        accept_terms: Optional[bool] = None,
    ) -> Any:
        """``POST /ads/lead-forms``. ``accept_terms=True`` says the person
        accepts the network's lead ad terms (Pinterest refuses a form
        without it): only send it after the person said yes. Requires
        ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/lead-forms",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "privacy_policy_url": privacy_policy_url,
                    "locale": locale,
                    "headline": headline,
                    "description": description,
                    "questions": [*questions],
                    "thank_you": thank_you,
                    "accept_terms": accept_terms,
                }
            ),
        )

    async def get(self, form_id: Union[int, str]) -> Any:
        """``GET /ads/lead-forms/{formId}``. Requires ``ads:read``."""
        return await self._client.request("GET", f"/ads/lead-forms/{_seg(form_id)}")

    async def update(
        self,
        form_id: Union[int, str],
        *,
        status: Optional[str] = None,
        sync_enabled: Optional[bool] = None,
    ) -> Any:
        """``PATCH /ads/lead-forms/{formId}`` - archive or open a form
        (``status`` ``archived`` or ``active``), or switch its lead sync.
        Requires ``ads:write``."""
        return await self._client.request(
            "PATCH",
            f"/ads/lead-forms/{_seg(form_id)}",
            json=drop_none({"status": status, "sync_enabled": sync_enabled}),
        )

    async def delete(self, form_id: Union[int, str]) -> Any:
        """``DELETE /ads/lead-forms/{formId}`` - archive a form (the leads
        already copied stay). Requires ``ads:write``."""
        return await self._client.request("DELETE", f"/ads/lead-forms/{_seg(form_id)}")

    async def send_test_lead(
        self, form_id: Union[int, str], *, fields: Optional[Mapping[str, Any]] = None
    ) -> Any:
        """``POST /ads/lead-forms/{formId}/test-leads`` - a test lead (the
        next sync copies it, marked ``is_test``). Requires ``ads:write``."""
        return await self._client.request(
            "POST", f"/ads/lead-forms/{_seg(form_id)}/test-leads", json=drop_none({"fields": fields})
        )


class AsyncAdLeads:
    """Leads of the workspace, copied from the networks every 15 minutes
    (webhook ``lead.received``). The answers are personal data."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        *,
        form_id: Optional[Union[int, str]] = None,
        status: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/leads`` - newest first (``limit`` at most 200).
        Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/leads",
            query={
                "form_id": form_id,
                "status": status,
                "since": since,
                "until": until,
                "limit": limit,
                "cursor": cursor,
            },
        )

    async def counts(self, *, form_id: Optional[Union[int, str]] = None) -> Any:
        """``GET /ads/leads/counts`` - ``total`` and ``by_status``. Requires
        ``ads:read``."""
        return await self._client.request("GET", "/ads/leads/counts", query={"form_id": form_id})

    async def update(
        self,
        lead_id: Union[int, str],
        *,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Any:
        """``PATCH /ads/leads/{leadId}`` - ``status`` is ``new``,
        ``contacted``, ``qualified``, ``won``, ``lost`` or ``spam``.
        Requires ``ads:write``."""
        return await self._client.request(
            "PATCH",
            f"/ads/leads/{_seg(lead_id)}",
            json=drop_none({"status": status, "note": note}),
        )


class AsyncAdConversions:
    """Pixels, conversion goals, custom conversions and server-side
    conversion events."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def destinations(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/conversions/destinations`` - pixels, datasets,
        conversion tags and conversion actions. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/conversions/destinations", query={"ad_account_id": ad_account_id}
        )

    async def goals(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/conversions/goals`` - the events a campaign can
        optimise for. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/conversions/goals", query={"ad_account_id": ad_account_id}
        )

    async def create_custom(
        self,
        *,
        ad_account_id: Union[int, str],
        name: str,
        destination_id: str,
        event: Optional[str] = None,
        url_contains: Optional[str] = None,
    ) -> Any:
        """``POST /ads/conversions/custom`` - a custom conversion (a URL rule
        and/or an event on a pixel). Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/conversions/custom",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "name": name,
                    "destination_id": destination_id,
                    "event": event,
                    "url_contains": url_contains,
                }
            ),
        )

    async def send_events(
        self,
        *,
        ad_account_id: Union[int, str],
        destination_id: str,
        events: Sequence[Mapping[str, Any]],
    ) -> Any:
        """``POST /ads/conversions/events`` - up to 1,000 conversion events
        from your server. Send the raw email and phone: OmniSocials
        normalizes and SHA-256 hashes them before they leave and stores
        nothing. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/conversions/events",
            json={
                "ad_account_id": ad_account_id,
                "destination_id": destination_id,
                "events": [*events],
            },
        )


class AsyncAdInsights:
    """Numbers: live from the network, per campaign or ad, over time, ranked,
    and what needs attention."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def query(
        self,
        *,
        ad_account_id: Union[int, str],
        level: Optional[str] = None,
        ids: Optional[Sequence[str]] = None,
        metrics: Optional[Sequence[str]] = None,
        breakdowns: Optional[Sequence[str]] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        time_increment: Optional[str] = None,
    ) -> Any:
        """``POST /ads/insights`` - live numbers from the network by day, ad,
        country, age, gender, placement, device or platform (at most 2
        ``breakdowns``). Read-only. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/insights",
            json=_insights_body(
                ad_account_id=ad_account_id,
                level=level,
                ids=ids,
                metrics=metrics,
                breakdowns=breakdowns,
                from_=from_,
                to=to,
                time_increment=time_increment,
            ),
        )

    async def campaign(
        self,
        campaign_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        breakdown: Optional[str] = None,
        time_increment: Optional[str] = None,
        metrics: Union[str, Sequence[str], None] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/analytics`` - numbers of an OmniSocials
        campaign (``breakdown="ad"`` gives one row per ad). Requires
        ``ads:read``."""
        return await self._client.request(
            "GET",
            f"/ads/campaigns/{_seg(campaign_id)}/analytics",
            query={
                "from": from_,
                "to": to,
                "breakdown": breakdown,
                "time_increment": time_increment,
                "metrics": join_list(metrics),
            },
        )

    async def ad(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        breakdown: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/analytics`` - numbers of one
        ad. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            f"{_ad_path(campaign_id, ad_id)}/analytics",
            query={"from": from_, "to": to, "breakdown": breakdown},
        )

    async def timeline(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        platform: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Any:
        """``GET /ads/timeline`` - daily totals of the workspace (``source``
        ``all``, ``omnisocials`` or ``external``). Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/timeline",
            query={"from": from_, "to": to, "platform": platform, "source": source},
        )

    async def performance(
        self,
        *,
        level: Optional[str] = None,
        metric: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        min_impressions: Optional[int] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Any:
        """``GET /ads/performance`` - campaigns or ads ranked by one metric.
        Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/performance",
            query={
                "level": level,
                "metric": metric,
                "order": order,
                "limit": limit,
                "min_impressions": min_impressions,
                "from": from_,
                "to": to,
                "platform": platform,
            },
        )

    async def alerts(self) -> Any:
        """``GET /ads/alerts`` - rejected ads, held campaigns, sign-in or
        payment problems, no delivery. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/alerts")


class AsyncAdReports:
    """Long reports that run in the background (up to 730 days)."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /ads/insights/reports``. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/insights/reports")

    async def start(
        self,
        *,
        ad_account_id: Union[int, str],
        level: Optional[str] = None,
        ids: Optional[Sequence[str]] = None,
        metrics: Optional[Sequence[str]] = None,
        breakdowns: Optional[Sequence[str]] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        time_increment: Optional[str] = None,
    ) -> Any:
        """``POST /ads/insights/reports`` - start a report with the fields of
        ``ads.insights.query()``; poll ``get()``. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/insights/reports",
            json=_insights_body(
                ad_account_id=ad_account_id,
                level=level,
                ids=ids,
                metrics=metrics,
                breakdowns=breakdowns,
                from_=from_,
                to=to,
                time_increment=time_increment,
            ),
        )

    async def get(self, report_id: str) -> Any:
        """``GET /ads/insights/reports/{reportId}`` - ``running``, ``done``
        (with ``rows``) or ``failed``. Requires ``ads:read``."""
        return await self._client.request("GET", f"/ads/insights/reports/{_seg(report_id)}")


class AsyncAdRules:
    """Automated rules: check campaigns on a schedule and notify, pause,
    activate or adjust the budget. A rule that notifies, pauses or lowers a
    budget works with ``ads:write``. A rule that can raise spend
    (``activate``, a positive ``adjust_budget``) needs a key with
    ``ads:spend`` (else ``403 rule_raises_spend``) and
    ``action["max_daily_budget"]``, confirmed by the person as
    ``confirm_max_daily_budget``; it never acts on Google. ``create``,
    ``update`` and ``undo`` are not retried after a 5xx, a timeout or a lost
    connection."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /ads/rules``. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/rules")

    async def create(
        self,
        *,
        name: str,
        conditions: Sequence[Mapping[str, Any]],
        action: Mapping[str, Any],
        ad_account_id: Optional[Union[int, str]] = None,
        enabled: Optional[bool] = None,
        scope: Optional[Mapping[str, Any]] = None,
        every_minutes: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        confirm_max_daily_budget: Optional[float] = None,
    ) -> Any:
        """``POST /ads/rules`` - a new rule, off until ``enabled=True``.

        A rule that can RAISE REAL AD SPEND (``activate``, a positive
        ``adjust_budget``) needs the person's own ceiling as
        ``confirm_max_daily_budget`` and a key with ``ads:spend`` (else
        ``403 rule_raises_spend``). Preview it first with ``preview()``. Not
        retried after a 5xx, a timeout or a lost connection: read the rules
        with ``list()``. Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            "/ads/rules",
            json=_rule_body(
                name=name,
                conditions=conditions,
                action=action,
                ad_account_id=ad_account_id,
                enabled=enabled,
                scope=scope,
                every_minutes=every_minutes,
                cooldown_minutes=cooldown_minutes,
                max_actions_per_run=max_actions_per_run,
                confirm_max_daily_budget=confirm_max_daily_budget,
            ),
            retry=RATE_LIMIT_ONLY,
        )

    async def templates(self) -> Any:
        """``GET /ads/rules/templates`` - ready-made rules. Requires
        ``ads:read``."""
        return await self._client.request("GET", "/ads/rules/templates")

    async def preview(
        self,
        *,
        conditions: Sequence[Mapping[str, Any]],
        action: Mapping[str, Any],
        name: Optional[str] = None,
        ad_account_id: Optional[Union[int, str]] = None,
        scope: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``POST /ads/rules/preview`` - what an unsaved rule would match and
        do now. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/rules/preview",
            json=drop_none(
                {
                    "name": name,
                    "ad_account_id": ad_account_id,
                    "scope": scope,
                    "conditions": [*conditions],
                    "action": action,
                }
            ),
        )

    async def activity(
        self, *, rule_id: Optional[Union[int, str]] = None, limit: Optional[int] = None
    ) -> Any:
        """``GET /ads/rules/activity`` - every change the rules made, with
        before and after. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/rules/activity", query={"rule_id": rule_id, "limit": limit}
        )

    async def undo(
        self, activity_id: Union[int, str], *, confirm_budget_amount: Optional[float] = None
    ) -> Any:
        """``POST /ads/rules/activity/{activityId}/undo`` - undo a change a
        rule made.

        Undo of a pause or of a budget cut RESTARTS or RAISES REAL AD SPEND:
        pass the amount as ``confirm_budget_amount`` after the person agreed,
        with a key that has ``ads:spend`` (else, and on Google always,
        ``403 start_in_app``). Not retried after a 5xx, a timeout or a lost
        connection. Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            f"/ads/rules/activity/{_seg(activity_id)}/undo",
            json=drop_none({"confirm_budget_amount": confirm_budget_amount}),
            retry=RATE_LIMIT_ONLY,
        )

    async def get(self, rule_id: Union[int, str]) -> Any:
        """``GET /ads/rules/{ruleId}``. Requires ``ads:read``."""
        return await self._client.request("GET", f"/ads/rules/{_seg(rule_id)}")

    async def update(
        self,
        rule_id: Union[int, str],
        *,
        name: Optional[str] = None,
        conditions: Optional[Sequence[Mapping[str, Any]]] = None,
        action: Optional[Mapping[str, Any]] = None,
        ad_account_id: Optional[Union[int, str]] = None,
        enabled: Optional[bool] = None,
        scope: Optional[Mapping[str, Any]] = None,
        every_minutes: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        confirm_max_daily_budget: Optional[float] = None,
    ) -> Any:
        """``PATCH /ads/rules/{ruleId}`` - change a rule (also ``enabled``). A
        changed action that can raise spend needs ``confirm_max_daily_budget``
        again and a key with ``ads:spend`` (else ``403 rule_raises_spend``).
        Not retried after a 5xx, a timeout or a lost connection. Requires
        ``ads:write``."""
        return await self._client.request(
            "PATCH",
            f"/ads/rules/{_seg(rule_id)}",
            json=_rule_body(
                name=name,
                conditions=conditions,
                action=action,
                ad_account_id=ad_account_id,
                enabled=enabled,
                scope=scope,
                every_minutes=every_minutes,
                cooldown_minutes=cooldown_minutes,
                max_actions_per_run=max_actions_per_run,
                confirm_max_daily_budget=confirm_max_daily_budget,
            ),
            retry=RATE_LIMIT_ONLY,
        )

    async def delete(self, rule_id: Union[int, str]) -> Any:
        """``DELETE /ads/rules/{ruleId}``. Requires ``ads:write``."""
        return await self._client.request("DELETE", f"/ads/rules/{_seg(rule_id)}")

    async def preview_saved(self, rule_id: Union[int, str]) -> Any:
        """``POST /ads/rules/{ruleId}/preview`` - what a saved rule would
        match and do now. Requires ``ads:read``."""
        return await self._client.request("POST", f"/ads/rules/{_seg(rule_id)}/preview")

    async def runs(self, rule_id: Union[int, str], *, limit: Optional[int] = None) -> Any:
        """``GET /ads/rules/{ruleId}/runs``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", f"/ads/rules/{_seg(rule_id)}/runs", query={"limit": limit}
        )


class AsyncAdResults:
    """Your own numbers per campaign and day (qualified leads, sales,
    revenue). Rules read them as ``results.<metric>``."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
        metric: Optional[str] = None,
    ) -> Any:
        """``GET /ads/campaign-results``. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/campaign-results",
            query={"from": from_, "to": to, "campaign_id": campaign_id, "metric": metric},
        )

    async def upload(self, rows: Sequence[Mapping[str, Any]]) -> Any:
        """``POST /ads/campaign-results`` - up to 5,000 rows of ``day``,
        ``metric``, ``value`` and the campaign (``campaign_id``,
        ``external_campaign_id`` + ``platform``, ``utm_campaign`` or
        ``campaign_name``). Sending a day again replaces it. Requires
        ``ads:write``."""
        return await self._client.request("POST", "/ads/campaign-results", json={"rows": [*rows]})

    async def totals(
        self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
    ) -> Any:
        """``GET /ads/campaign-results/totals`` - totals over a period, with
        the formulas. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/campaign-results/totals",
            query={"from": from_, "to": to, "campaign_id": campaign_id},
        )

    async def metrics(self) -> Any:
        """``GET /ads/campaign-results/metrics`` - your metric names and
        formulas. Requires ``ads:read``."""
        return await self._client.request("GET", "/ads/campaign-results/metrics")

    async def put_metric(
        self,
        key: str,
        *,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        formula: Optional[str] = None,
    ) -> Any:
        """``PUT /ads/campaign-results/metrics/{key}`` - name a metric or
        define a formula (``unit`` ``number``, ``money`` or ``percent``).
        Requires ``ads:write``."""
        return await self._client.request(
            "PUT",
            f"/ads/campaign-results/metrics/{_seg(key)}",
            json=drop_none({"label": label, "unit": unit, "formula": formula}),
        )


class AsyncAdMedia:
    """The network's own image and video library of an ad account. Use an
    id in an ad as ``network[<network>]["media_ref"]``."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        *,
        ad_account_id: Union[int, str],
        type: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/media``. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/media",
            query={"ad_account_id": ad_account_id, "type": type, "cursor": cursor},
        )

    async def upload(
        self,
        *,
        ad_account_id: Union[int, str],
        type: str,
        url: str,
        name: Optional[str] = None,
    ) -> Any:
        """``POST /ads/media`` - upload an image or video to the network
        ahead of an ad. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/media",
            json=drop_none(
                {"ad_account_id": ad_account_id, "type": type, "url": url, "name": name}
            ),
        )

    async def get(
        self, media_id: str, *, ad_account_id: Union[int, str], type: Optional[str] = None
    ) -> Any:
        """``GET /ads/media/{mediaId}`` - the processing status of an upload.
        Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            f"/ads/media/{_seg(media_id)}",
            query={"ad_account_id": ad_account_id, "type": type},
        )

    async def delete(self, media_id: str, *, ad_account_id: Union[int, str], type: str) -> Any:
        """``DELETE /ads/media/{mediaId}``. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE",
            f"/ads/media/{_seg(media_id)}",
            query={"ad_account_id": ad_account_id, "type": type},
        )


class AsyncAdPreviews:
    """Previews drawn by the network."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def create(
        self,
        *,
        ad_account_id: Union[int, str],
        ad: Mapping[str, Any],
        placements: Optional[Sequence[str]] = None,
        objective: Optional[str] = None,
    ) -> Any:
        """``POST /ads/previews`` - previews of a new ad (the shape of a
        draft ad). Read-only. Requires ``ads:read``."""
        return await self._client.request(
            "POST",
            "/ads/previews",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "ad": ad,
                    "placements": None if placements is None else [*placements],
                    "objective": objective,
                }
            ),
        )

    async def for_ad(
        self,
        campaign_id: Union[int, str],
        ad_id: Union[int, str],
        *,
        placements: Union[str, Sequence[str], None] = None,
    ) -> Any:
        """``GET /ads/campaigns/{id}/ads/{adId}/previews`` - previews of an
        existing ad. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            f"{_ad_path(campaign_id, ad_id)}/previews",
            query={"placements": join_list(placements)},
        )


class AsyncAdPartnership:
    """Partnership ads with creators (Meta)."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list_content(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/partnership/content`` - creator posts you may run as
        partnership ads. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/partnership/content", query={"ad_account_id": ad_account_id}
        )

    async def list_permissions(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/partnership/permissions``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/partnership/permissions", query={"ad_account_id": ad_account_id}
        )

    async def set_permission(self, *, ad_account_id: Union[int, str], **fields: Any) -> Any:
        """``POST /ads/partnership/permissions`` - ask for or set a
        permission; Meta's fields pass through as keyword arguments.
        Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/partnership/permissions",
            json={**fields, "ad_account_id": ad_account_id},
        )


class AsyncAdAccountsAdmin:
    """Ad account admin: identities, health, finance, settings, people,
    change log, businesses, DSA and the manager hierarchy. ``account_id`` is
    the OmniSocials ad account id."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def identities(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/identities`` - Pages, profiles and
        identities an ad can run as. Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "identities"))

    async def health(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/health`` - status, payment, spend
        limit, Page and pixel before an ad starts. A check that cannot be
        read is ``unknown``; failed checks carry a ``fix_url``. Requires
        ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "health"))

    async def finance(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/finance`` - spend limit, amount
        spent, balance and payment method. Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "finance"))

    async def update_settings(
        self,
        account_id: Union[int, str],
        *,
        spend_cap: Union[float, None, NotGiven] = NOT_GIVEN,
        dsa_beneficiary: Optional[str] = None,
        dsa_payor: Optional[str] = None,
        name: Optional[str] = None,
        confirm_budget_amount: Optional[Union[float, str]] = None,
    ) -> Any:
        """``PATCH /ads/accounts/{accountId}/settings`` - spend cap, DSA payer
        and beneficiary, name.

        A higher ``spend_cap`` ALLOWS MORE REAL AD SPEND: pass the new cap as
        ``confirm_budget_amount`` after the person agreed; ``spend_cap=None``
        removes the cap and needs ``confirm_budget_amount="remove"``. A spend
        cap change: needs a key with the opt-in ``ads:spend`` scope ("Start
        ads"); without it, and on Google (``api_draft_only``) always, the call
        answers ``403 start_in_app`` with the page where a person does it in
        the app. The name and the DSA names stay open. Not retried after a
        5xx, a timeout or a lost connection. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "dsa_beneficiary": dsa_beneficiary,
                "dsa_payor": dsa_payor,
                "name": name,
                "confirm_budget_amount": confirm_budget_amount,
            }
        )
        if not isinstance(spend_cap, NotGiven):
            body["spend_cap"] = spend_cap
        return await self._client.request(
            "PATCH",
            _account_path(account_id, "settings"),
            json=body,
            retry=RATE_LIMIT_ONLY,
        )

    async def list_users(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/users`` - people with access.
        Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "users"))

    async def add_user(
        self,
        account_id: Union[int, str],
        *,
        role: str,
        email: Optional[str] = None,
        member_id: Optional[str] = None,
    ) -> Any:
        """``POST /ads/accounts/{accountId}/users`` - give a person access
        (LinkedIn). Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            _account_path(account_id, "users"),
            json=drop_none({"email": email, "member_id": member_id, "role": role}),
        )

    async def remove_user(self, account_id: Union[int, str], user_id: str) -> Any:
        """``DELETE /ads/accounts/{accountId}/users/{userId}`` - remove a
        person's access. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE", _account_path(account_id, f"users/{_seg(user_id)}")
        )

    async def activity(
        self,
        account_id: Union[int, str],
        *,
        since: Optional[str] = None,
        until: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /ads/accounts/{accountId}/activity`` - the change log of the
        ad account. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            _account_path(account_id, "activity"),
            query={"since": since, "until": until, "cursor": cursor},
        )

    async def businesses(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/businesses`` - Meta business
        portfolios and TikTok Business Centers. Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "businesses"))

    async def dsa(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/dsa`` - the EU DSA payer and
        beneficiary (Meta). Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "dsa"))

    async def hierarchy(self, account_id: Union[int, str]) -> Any:
        """``GET /ads/accounts/{accountId}/hierarchy`` - the manager account
        hierarchy (Google). Requires ``ads:read``."""
        return await self._client.request("GET", _account_path(account_id, "hierarchy"))


class AsyncAdReachFrequency:
    """Meta reach and frequency buying. A prediction spends nothing; a
    reservation does."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def create(
        self,
        *,
        ad_account_id: Union[int, str],
        objective: str,
        targeting: Mapping[str, Any],
        start_at: str,
        end_at: str,
        budget: Optional[Mapping[str, Any]] = None,
        reach: Optional[int] = None,
        frequency_cap: Optional[int] = None,
        frequency_interval_days: Optional[int] = None,
    ) -> Any:
        """``POST /ads/reach-frequency`` - a prediction (``objective``
        ``awareness``, ``engagement`` or ``video_views``; exactly one
        country in ``targeting``; ``budget`` in major units or ``reach``).
        It spends nothing; Meta needs the reach and frequency capability on
        the ad account. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            "/ads/reach-frequency",
            json=drop_none(
                {
                    "ad_account_id": ad_account_id,
                    "objective": objective,
                    "targeting": targeting,
                    "start_at": start_at,
                    "end_at": end_at,
                    "budget": budget,
                    "reach": reach,
                    "frequency_cap": frequency_cap,
                    "frequency_interval_days": frequency_interval_days,
                }
            ),
        )

    async def get(self, prediction_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/reach-frequency/{predictionId}``. Requires
        ``ads:read``."""
        return await self._client.request(
            "GET",
            f"/ads/reach-frequency/{_seg(prediction_id)}",
            query={"ad_account_id": ad_account_id},
        )

    async def cancel(self, prediction_id: str, *, ad_account_id: Union[int, str]) -> Any:
        """``DELETE /ads/reach-frequency/{predictionId}`` - cancel a
        prediction or a reservation. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE",
            f"/ads/reach-frequency/{_seg(prediction_id)}",
            query={"ad_account_id": ad_account_id},
        )

    async def reserve(
        self,
        prediction_id: str,
        *,
        ad_account_id: Union[int, str],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/reach-frequency/{predictionId}/reserve`` - COMMITS REAL
        AD SPEND: pass the prediction's budget as ``confirm_budget_amount``
        after the person agreed. Needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Not retried after a 5xx, a timeout or a
        lost connection: read the prediction with ``get()``. Requires
        ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/reach-frequency/{_seg(prediction_id)}/reserve",
            json={"ad_account_id": ad_account_id, "confirm_budget_amount": confirm_budget_amount},
            retry=RATE_LIMIT_ONLY,
        )


class AsyncAdStudies:
    """A/B tests and lift studies (Meta)."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/studies``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/studies", query={"ad_account_id": ad_account_id}
        )

    async def create(self, *, ad_account_id: Union[int, str], **fields: Any) -> Any:
        """``POST /ads/studies`` - an A/B test between existing campaigns or
        ad sets; Meta's fields pass through as keyword arguments. Needs a key
        with the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Requires ``ads:write``."""
        return await self._client.request(
            "POST", "/ads/studies", json={**fields, "ad_account_id": ad_account_id}
        )


class AsyncAdBudgetSchedules:
    """Planned budget increases of a campaign for high-demand periods
    (Meta)."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self, campaign_id: Union[int, str]) -> Any:
        """``GET /ads/campaigns/{id}/budget-schedules``. Requires
        ``ads:read``."""
        return await self._client.request(
            "GET", f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules"
        )

    async def create(
        self,
        campaign_id: Union[int, str],
        *,
        start_at: str,
        end_at: str,
        budget_increase: Mapping[str, Any],
        confirm_budget_amount: float,
    ) -> Any:
        """``POST /ads/campaigns/{id}/budget-schedules`` - plan a budget
        increase (``budget_increase={"type": "absolute" | "multiplier",
        "value": ...}``).

        NEW REAL AD SPEND in that period: pass the increase per day (absolute)
        or the campaign budget times the multiplier as
        ``confirm_budget_amount`` after the person agreed. Needs a key with
        the opt-in ``ads:spend`` scope ("Start ads"); without it, and on
        Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
        Not retried after a 5xx, a timeout or a lost connection: read the
        schedules with ``list()``. Requires ``ads:write``.
        """
        return await self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules",
            json={
                "start_at": start_at,
                "end_at": end_at,
                "budget_increase": budget_increase,
                "confirm_budget_amount": confirm_budget_amount,
            },
            retry=RATE_LIMIT_ONLY,
        )

    async def delete(self, campaign_id: Union[int, str], schedule_id: str) -> Any:
        """``DELETE /ads/campaigns/{id}/budget-schedules/{scheduleId}``.
        Requires ``ads:write``."""
        return await self._client.request(
            "DELETE",
            f"/ads/campaigns/{_seg(campaign_id)}/budget-schedules/{_seg(schedule_id)}",
        )


class AsyncAdGoogle:
    """Google reports (read-only; every API caller stops at the draft on
    Google)."""

    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def search_terms(
        self,
        *,
        ad_account_id: Union[int, str],
        campaign_id: Optional[Union[int, str]] = None,
        external_campaign_id: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """``GET /ads/google/search-terms``. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/google/search-terms",
            query={
                "ad_account_id": ad_account_id,
                "campaign_id": campaign_id,
                "external_campaign_id": external_campaign_id,
                "from": from_,
                "to": to,
                "limit": limit,
            },
        )

    async def recommendations(
        self, *, ad_account_id: Union[int, str], types: Union[str, Sequence[str], None] = None
    ) -> Any:
        """``GET /ads/google/recommendations``. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/google/recommendations",
            query={"ad_account_id": ad_account_id, "types": join_list(types)},
        )

    async def keywords(
        self,
        *,
        ad_account_id: Union[int, str],
        external_campaign_id: Optional[str] = None,
        external_ad_set_id: Optional[str] = None,
    ) -> Any:
        """``GET /ads/google/keywords`` - search keywords and negative
        keywords. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/google/keywords",
            query={
                "ad_account_id": ad_account_id,
                "external_campaign_id": external_campaign_id,
                "external_ad_set_id": external_ad_set_id,
            },
        )

    async def assets(self, *, ad_account_id: Union[int, str], type: Optional[str] = None) -> Any:
        """``GET /ads/google/assets`` - sitelinks, callouts and structured
        snippets. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/google/assets", query={"ad_account_id": ad_account_id, "type": type}
        )

    async def shared_budgets(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/shared-budgets``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/google/shared-budgets", query={"ad_account_id": ad_account_id}
        )

    async def bid_strategies(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/bid-strategies`` - portfolio bid strategies.
        Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/google/bid-strategies", query={"ad_account_id": ad_account_id}
        )

    async def ad_schedule(
        self, *, ad_account_id: Union[int, str], external_campaign_id: str
    ) -> Any:
        """``GET /ads/google/ad-schedule`` - the days and hours of a Google
        campaign. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/google/ad-schedule",
            query={"ad_account_id": ad_account_id, "external_campaign_id": external_campaign_id},
        )

    async def labels(self, *, ad_account_id: Union[int, str]) -> Any:
        """``GET /ads/google/labels``. Requires ``ads:read``."""
        return await self._client.request(
            "GET", "/ads/google/labels", query={"ad_account_id": ad_account_id}
        )

    async def local_services_leads(
        self, *, ad_account_id: Union[int, str], since: Optional[str] = None
    ) -> Any:
        """``GET /ads/google/local-services-leads``. Requires ``ads:read``."""
        return await self._client.request(
            "GET",
            "/ads/google/local-services-leads",
            query={"ad_account_id": ad_account_id, "since": since},
        )

class AsyncAds:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client
        self.drafts = AsyncAdDrafts(client)
        #: Campaigns, ad sets and ads of an ad account, also the ones made outside OmniSocials, and their import.
        self.objects = AsyncAdObjects(client)
        #: The ads of an OmniSocials campaign.
        self.campaign_ads = AsyncAdCampaignAds(client)
        #: Comments on ads.
        self.comments = AsyncAdComments(client)
        #: Targeting search, browse, reach estimate and bid suggestions.
        self.targeting = AsyncAdTargeting(client)
        #: Custom audiences: customer lists, lookalikes, company lists.
        self.audiences = AsyncAdAudiences(client)
        #: Lead forms.
        self.lead_forms = AsyncAdLeadForms(client)
        #: Leads copied from the lead forms.
        self.leads = AsyncAdLeads(client)
        #: Pixels, conversion goals, custom conversions, server-side events.
        self.conversions = AsyncAdConversions(client)
        #: Live numbers, campaign and ad analytics, timeline, ranking, alerts.
        self.insights = AsyncAdInsights(client)
        #: Background reports.
        self.reports = AsyncAdReports(client)
        #: Automated rules.
        self.rules = AsyncAdRules(client)
        #: Your own numbers per campaign and day.
        self.results = AsyncAdResults(client)
        #: The network's own image and video library.
        self.media = AsyncAdMedia(client)
        #: Previews drawn by the network.
        self.previews = AsyncAdPreviews(client)
        #: Partnership ads (Meta).
        self.partnership = AsyncAdPartnership(client)
        #: Ad account admin (health, finance, settings, people, change log).
        self.accounts = AsyncAdAccountsAdmin(client)
        #: Meta reach and frequency.
        self.reach_frequency = AsyncAdReachFrequency(client)
        #: A/B tests and lift studies (Meta).
        self.studies = AsyncAdStudies(client)
        #: Planned budget increases (Meta).
        self.budget_schedules = AsyncAdBudgetSchedules(client)
        #: Google reports.
        self.google = AsyncAdGoogle(client)

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
        ``coming_soon``), and per network the ``features`` its API offers,
        ``targeting_types``, ``bid_strategies``, ``settings`` and
        ``ad_fields``, plus ``api_goals``, ``api_draft_only`` (networks where
        every API caller stops at the draft, also a key with ``ads:spend``:
        Google) and ``api_stop_in_app`` (networks where the API may not even
        pause or delete a campaign that reached the network: Google). Requires
        ``ads:read``."""
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
        """``POST /ads/boost`` - boost a published post. Creates a DRAFT boost
        that spends nothing; the person starts it in the app. ``budget`` is
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

    async def update(
        self,
        campaign_id: Union[int, str],
        *,
        name: Optional[str] = None,
        budget: Optional[Mapping[str, Any]] = None,
        confirm_budget_amount: Optional[float] = None,
        targeting: Optional[Mapping[str, Any]] = None,
        schedule: Optional[Mapping[str, Any]] = None,
        objective: Optional[str] = None,
        settings: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """``PATCH /ads/campaigns/{id}`` - change the name, budget, targeting
        or schedule of a draft; ``objective`` and ``settings`` only while the
        campaign is a draft (``400 settings_locked`` after the start:
        duplicate it).

        A campaign that reached the network changes only with a key that has
        ``ads:spend``; without it, and on Google always, the call answers
        ``403 start_in_app`` and a person changes it in the app. A higher
        budget on a running campaign RAISES REAL AD SPEND: show the person the
        new amount and get their yes first, then pass it again as
        ``confirm_budget_amount``. Not retried after a 5xx, a timeout or a
        lost connection: read the campaign with ``get()`` to see what
        happened. Requires ``ads:write``.
        """
        body = drop_none(
            {
                "name": name,
                "budget": budget,
                "confirm_budget_amount": confirm_budget_amount,
                "targeting": targeting,
                "schedule": schedule,
                "objective": objective,
                "settings": settings,
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

        Needs a key with the opt-in ``ads:spend`` scope ("Start ads"); without
        it, and on Google (``api_draft_only``) always, the call answers
        ``403 start_in_app`` with the page where a person does it in the app.
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

        Needs a key with ``ads:spend``: without it, and on Google always, a
        result answers ``ok: false`` with code ``start_in_app`` and the page
        where a person starts it. Every campaign's budget must equal
        ``confirm_budget_amount``; show the person the total (amount x
        campaigns) and get their yes first. Answers ``{"results": [...]}``.
        Not retried after a 5xx, a timeout or a lost connection: read the
        campaigns with ``get()`` to see what happened. Requires ``ads:write``.
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
        in review). Open with ``ads:write``, except on the networks in
        ``api_stop_in_app`` (Google): there a campaign that reached the
        network answers ``403 start_in_app``. Requires ``ads:write``."""
        return await self._client.request(
            "POST", f"/ads/campaigns/{_seg(campaign_id)}/pause"
        )

    async def resume(self, campaign_id: Union[int, str]) -> Any:
        """``POST /ads/campaigns/{id}/resume`` - resume a paused campaign: it
        STARTS REAL AD SPEND again. Needs a key with the opt-in ``ads:spend``
        scope ("Start ads"); without it, and on Google (``api_draft_only``)
        always, the call answers ``403 start_in_app`` with the page where a
        person does it in the app. Only a paused campaign resumes
        (``409 not_paused``). Show the person the budget and get their yes
        first. Not retried after a 5xx, a timeout or a lost connection: read
        the campaign with ``get()`` to see what happened. Requires
        ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/resume",
            retry=RATE_LIMIT_ONLY,
        )

    async def bulk_status(
        self,
        *,
        campaign_ids: Sequence[Union[int, str]],
        status: str,
        confirm_budget_amount: Optional[float] = None,
    ) -> Any:
        """``POST /ads/campaigns/bulk-status`` - pause or resume up to 50
        campaigns (``status`` ``paused`` or ``active``).

        Resuming RESTARTS REAL AD SPEND: every campaign's budget must equal
        ``confirm_budget_amount`` (one amount for all), checked before any
        change; show the person the total and get their yes first. Resuming
        needs a key with ``ads:spend``: without it, and on Google always, a
        result answers ``start_in_app``. Pausing stays open (Google:
        ``start_in_app``). Answers ``{"data": {"results": [...]}}``. Not
        retried after a 5xx, a timeout or a lost connection. Requires
        ``ads:write``.
        """
        return await self._client.request(
            "POST",
            "/ads/campaigns/bulk-status",
            json=drop_none(
                {
                    "campaign_ids": [*campaign_ids],
                    "status": status,
                    "confirm_budget_amount": confirm_budget_amount,
                }
            ),
            retry=RATE_LIMIT_ONLY,
        )

    async def duplicate(self, campaign_id: Union[int, str], *, name: Optional[str] = None) -> Any:
        """``POST /ads/campaigns/{id}/duplicate`` - copy a campaign as a new
        draft (same ad account, goal, budget, targeting, settings and ads).
        A draft never spends. Requires ``ads:write``."""
        return await self._client.request(
            "POST",
            f"/ads/campaigns/{_seg(campaign_id)}/duplicate",
            json=drop_none({"name": name}),
        )

    async def delete(self, campaign_id: Union[int, str]) -> Any:
        """``DELETE /ads/campaigns/{id}`` - delete a campaign on the network
        too. A campaign that spent is archived: its spend stays in the totals.
        Open with ``ads:write``, except on the networks in ``api_stop_in_app``
        (Google): there a campaign that reached the network answers
        ``403 start_in_app``. Requires ``ads:write``."""
        return await self._client.request(
            "DELETE", f"/ads/campaigns/{_seg(campaign_id)}"
        )

    async def overview(self) -> Any:
        """``GET /ads/overview`` - accounts, campaigns per status and the
        totals. ``totals["spend"]`` is ``None`` when the campaigns use more
        than one currency (``totals["currency"]`` names the one currency):
        read ``totals_by_currency`` then, one row per currency with
        ``currency``, ``spend``, ``impressions`` and ``clicks`` (spend is
        never added across currencies). Requires ``ads:read``."""
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
