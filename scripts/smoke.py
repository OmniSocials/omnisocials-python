"""Offline smoke test for the omnisocials SDK.

Run from sdk/python/:  python3 scripts/smoke.py

Verifies (without any network access):
- the package imports and both clients construct
- every resource exposes every expected method (sync and async)
- verify_webhook_signature round-trips against a signature built exactly
  like backend/services/webhooks/webhookDispatcher.js
- tampered bodies and stale timestamps are rejected
- a missing API key raises AuthenticationError at construction time
- tags calls (and the tag fields on posts and analytics) send the right
  method, path, query and body (through httpx.MockTransport, sync and async)
- limits and feature request calls send the right method, path, query and
  body, return the outcome, and a 409 not_requestable keeps the limit in the
  error body (through httpx.MockTransport, sync and async)
- ads calls send the right method, path and body, and a call that can start
  ad spend is sent once after a 502 or a lost connection while a read is
  retried (through httpx.MockTransport, sync and async)
"""

import asyncio
import hashlib
import hmac
import inspect
import json
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import omnisocials  # noqa: E402
from omnisocials import (  # noqa: E402
    APIConnectionError,
    APIError,
    AsyncOmniSocials,
    AuthenticationError,
    NotFoundError,
    OmniSocials,
    OmniSocialsError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
    WebhookVerificationError,
    verify_webhook_signature,
)

CHECKS = 0


def ok(condition, label):
    global CHECKS
    assert condition, f"FAILED: {label}"
    CHECKS += 1
    print(f"  ok - {label}")


EXPECTED = {
    "posts": [
        "list",
        "get",
        "recent_platform",
        "create",
        "create_and_publish",
        "update",
        "delete",
        "publish",
        "approve",
        "reject",
        "get_approval",
    ],
    "media": [
        "list",
        "get",
        "upload",
        "upload_from_url",
        "upload_from_base64",
        "create_upload_url",
        "check",
        "update",
        "delete",
    ],
    "folders": ["list", "create", "update", "delete"],
    "hashtag_sets": ["list", "get", "create", "update", "delete"],
    "tags": ["list", "create", "update", "delete", "apply"],
    "accounts": ["list", "get"],
    "analytics": ["post", "posts", "overview", "accounts", "best_times", "tags"],
    "locations": ["search", "validate"],
    "pinterest": ["list_products", "validate_product"],
    "automations": ["list", "get", "create", "update", "delete", "list_events"],
    "ads": [
        "list_accounts",
        "capabilities",
        "list",
        "get",
        "boost",
        "boost_multi",
        "create",
        "update",
        "activate",
        "activate_multi",
        "pause",
        "resume",
        "delete",
        "overview",
        "suggestions",
        "research_keywords",
        "keyword_metrics",
    ],
    "webhooks": ["list", "get", "create", "update", "delete", "rotate_secret"],
    "limits": ["list"],
    "feature_requests": ["create", "list", "get"],
}

DRAFT_METHODS = ["defaults", "create", "get", "update", "delete", "attach_account", "launch"]


def check_client_surface():
    print("Client surface:")
    client = OmniSocials(api_key="omsk_test_x")
    for resource, methods in EXPECTED.items():
        namespace = getattr(client, resource, None)
        ok(namespace is not None, f"client.{resource} exists")
        for method in methods:
            fn = getattr(namespace, method, None)
            ok(callable(fn), f"client.{resource}.{method} is callable")
            ok(
                not inspect.iscoroutinefunction(fn),
                f"client.{resource}.{method} is sync",
            )
    for method in DRAFT_METHODS:
        fn = getattr(client.ads.drafts, method, None)
        ok(
            callable(fn) and not inspect.iscoroutinefunction(fn),
            f"client.ads.drafts.{method} is a sync method",
        )
    ok(callable(client.health), "client.health is callable")
    ok(callable(client.close), "client.close is callable")
    with OmniSocials(api_key="omsk_test_x") as ctx:
        ok(ctx is not None, "sync client works as a context manager")
    client.close()

    async_client = AsyncOmniSocials(api_key="omsk_test_x")
    for resource, methods in EXPECTED.items():
        namespace = getattr(async_client, resource, None)
        ok(namespace is not None, f"async client.{resource} exists")
        for method in methods:
            fn = getattr(namespace, method, None)
            ok(callable(fn), f"async client.{resource}.{method} is callable")
            ok(
                inspect.iscoroutinefunction(fn),
                f"async client.{resource}.{method} is async",
            )
    for method in DRAFT_METHODS:
        fn = getattr(async_client.ads.drafts, method, None)
        ok(
            inspect.iscoroutinefunction(fn),
            f"async client.ads.drafts.{method} is async",
        )
    ok(
        inspect.iscoroutinefunction(async_client.health),
        "async client.health is a coroutine function",
    )
    ok(callable(async_client.aclose), "async client.aclose is callable")

    async def close_it():
        async with AsyncOmniSocials(api_key="omsk_test_x") as ctx:
            assert ctx is not None
        await async_client.aclose()

    asyncio.run(close_it())
    ok(True, "async client context manager + aclose work")


def check_construction_guards():
    print("Construction guards:")
    saved = os.environ.pop("OMNISOCIALS_API_KEY", None)
    try:
        try:
            OmniSocials()
        except AuthenticationError:
            ok(True, "missing API key raises AuthenticationError (sync)")
        else:
            raise AssertionError("FAILED: missing key did not raise (sync)")
        try:
            AsyncOmniSocials()
        except AuthenticationError:
            ok(True, "missing API key raises AuthenticationError (async)")
        else:
            raise AssertionError("FAILED: missing key did not raise (async)")

        os.environ["OMNISOCIALS_API_KEY"] = "omsk_test_env"
        env_client = OmniSocials()
        ok(env_client.api_key == "omsk_test_env", "env var API key is picked up")
        arg_client = OmniSocials(api_key="omsk_test_arg")
        ok(
            arg_client.api_key == "omsk_test_arg",
            "constructor arg wins over env var",
        )
        env_client.close()
        arg_client.close()
    finally:
        if saved is None:
            os.environ.pop("OMNISOCIALS_API_KEY", None)
        else:
            os.environ["OMNISOCIALS_API_KEY"] = saved

    # Error hierarchy sanity
    for cls in (
        AuthenticationError,
        PermissionDeniedError,
        NotFoundError,
        ValidationError,
        RateLimitError,
        ServerError,
    ):
        ok(issubclass(cls, APIError), f"{cls.__name__} subclasses APIError")
    ok(issubclass(APIError, OmniSocialsError), "APIError subclasses OmniSocialsError")
    ok(
        issubclass(APIConnectionError, OmniSocialsError),
        "APIConnectionError subclasses OmniSocialsError",
    )
    ok(
        issubclass(WebhookVerificationError, OmniSocialsError),
        "WebhookVerificationError subclasses OmniSocialsError",
    )
    # Structural version check: __version__ must match pyproject.toml, so this
    # script never needs stamping on release (set-version.mjs syncs both).
    import pathlib
    import re as _re

    _pyproject = (pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()
    _expected = _re.search(r'^version = "([^"]+)"', _pyproject, _re.M).group(1)
    ok(omnisocials.__version__ == _expected, f"__version__ matches pyproject.toml ({_expected})")


class StubAPI:
    """Answers requests from a script of statuses (the last one repeats) and
    records them. ``"drop"`` raises a lost connection. Never touches the
    network: it is plugged in through httpx.MockTransport."""

    def __init__(self):
        self.calls = []
        self.answers = [200]

    def reset(self, *answers):
        self.calls = []
        self.answers = list(answers)

    def handler(self, request):
        self.calls.append(request)
        answer = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        if answer == "drop":
            raise httpx.ConnectError("connection lost", request=request)
        if answer >= 400:
            # Retry-After: 0 keeps the retried reads fast.
            return httpx.Response(
                answer,
                json={"error": {"code": "bad_gateway", "message": "upstream"}},
                headers={"Retry-After": "0"},
            )
        return httpx.Response(answer, json={"data": {"ok": True}})

    def body(self, index=-1):
        return json.loads(self.calls[index].content)

    def path(self, index=-1):
        return self.calls[index].url.raw_path.decode()


DRAFT = {
    "name": "Autumn sale",
    "objective": "traffic",
    "platforms": ["meta", {"platform": "linkedin", "budget_amount": 20}],
    "budget": {"amount": 10, "currency": "EUR"},
    "schedule": {"duration_days": None},
    "targeting": {"countries": ["NL", "BE"], "automatic_audience": True},
    "ads": [
        {
            "media": [{"url": "https://example.com/sale.jpg", "type": "image"}],
            "primary_text": "30% off everything this week",
            "link": "https://example.com/sale",
        }
    ],
}


def check_tags_transport():
    print("Tags transport (stubbed, sync):")
    stub = StubAPI()
    client = OmniSocials(api_key="omsk_test_x", max_retries=0)
    client._http.close()
    client._http = httpx.Client(
        transport=httpx.MockTransport(stub.handler), headers=client._default_headers()
    )

    client.tags.list()
    ok(stub.calls[-1].method == "GET" and stub.path() == "/v1/tags", "tags.list GETs /tags")

    client.tags.create(name="Question")
    ok(
        stub.calls[-1].method == "POST" and stub.path() == "/v1/tags"
        and stub.body() == {"name": "Question"},
        "tags.create POSTs /tags with only the given keys",
    )
    client.tags.create(name="Behind the scenes", color="teal")
    ok(stub.body() == {"name": "Behind the scenes", "color": "teal"}, "tags.create sends color")

    client.tags.update(12, color="red")
    ok(
        stub.calls[-1].method == "PATCH" and stub.path() == "/v1/tags/12"
        and stub.body() == {"color": "red"},
        "tags.update PATCHes /tags/{id} with only the given keys",
    )

    result = client.tags.delete(12)
    ok(
        stub.calls[-1].method == "DELETE" and stub.path() == "/v1/tags/12"
        and result == {"data": {"ok": True}},
        "tags.delete DELETEs /tags/{id} and returns the body",
    )

    client.tags.apply(post_ids=["1024", 1025], add=["Question", 7], set=None)
    ok(
        stub.calls[-1].method == "POST" and stub.path() == "/v1/tags/apply"
        and stub.body() == {"post_ids": ["1024", "1025"], "add": ["Question", 7]},
        "tags.apply POSTs /tags/apply, post ids as strings, None dropped",
    )
    client.tags.apply(post_ids=["1024"], set=[])
    ok(stub.body() == {"post_ids": ["1024"], "set": []}, "tags.apply sends set=[] (clear)")

    client.analytics.tags(start_date="2026-08-01", min_posts=3)
    ok(
        stub.calls[-1].method == "GET" and stub.path().startswith("/v1/analytics/tags")
        and stub.calls[-1].url.params
        == httpx.QueryParams({"start_date": "2026-08-01", "min_posts": "3"}),
        "analytics.tags GETs /analytics/tags with only the given filters",
    )

    client.posts.list(tag=["Question", 7])
    ok(
        stub.calls[-1].url.params == httpx.QueryParams({"tag": "Question,7"}),
        "posts.list joins a tag list with commas",
    )
    client.posts.list(tag=7)
    ok(stub.calls[-1].url.params == httpx.QueryParams({"tag": "7"}), "posts.list takes a tag id")

    client.analytics.overview(period="30d", tag="Question")
    ok(
        stub.calls[-1].url.params == httpx.QueryParams({"period": "30d", "tag": "Question"}),
        "analytics.overview sends tag",
    )

    client.posts.create(content="Hi", tags=["Question", 7])
    ok(stub.body() == {"content": "Hi", "tags": ["Question", 7]}, "posts.create sends tags")
    client.posts.create_and_publish(content="Hi", tags=["Question"])
    ok(stub.body()["tags"] == ["Question"], "posts.create_and_publish sends tags")

    client.posts.update("55", tags=None)
    ok(
        stub.calls[-1].method == "PATCH" and stub.body() == {"tags": None},
        "posts.update(tags=None) sends an explicit null (clears)",
    )
    client.posts.update("55", content="New text")
    ok("tags" not in stub.body(), "posts.update leaves tags out when not given")
    client.close()

    print("Tags transport (stubbed, async):")

    async def run_async():
        async_client = AsyncOmniSocials(api_key="omsk_test_x", max_retries=0)
        await async_client._http.aclose()
        async_client._http = httpx.AsyncClient(
            transport=httpx.MockTransport(stub.handler),
            headers=async_client._default_headers(),
        )
        await async_client.tags.list()
        ok(stub.path() == "/v1/tags", "async tags.list GETs /tags")
        await async_client.tags.create(name="Question", color="blue")
        ok(stub.body() == {"name": "Question", "color": "blue"}, "async tags.create sends the body")
        await async_client.tags.update("12", name="Questions")
        ok(
            stub.calls[-1].method == "PATCH" and stub.body() == {"name": "Questions"},
            "async tags.update PATCHes /tags/{id}",
        )
        await async_client.tags.delete("12")
        ok(stub.calls[-1].method == "DELETE", "async tags.delete DELETEs /tags/{id}")
        await async_client.tags.apply(post_ids=["1"], remove=["Question"])
        ok(
            stub.body() == {"post_ids": ["1"], "remove": ["Question"]},
            "async tags.apply sends remove",
        )
        await async_client.analytics.tags(platform="tiktok")
        ok(
            stub.calls[-1].url.params == httpx.QueryParams({"platform": "tiktok"}),
            "async analytics.tags sends platform",
        )
        await async_client.posts.list(tag="Question")
        ok(stub.calls[-1].url.params == httpx.QueryParams({"tag": "Question"}), "async posts.list sends tag")
        await async_client.posts.update("55", tags=[])
        ok(stub.body() == {"tags": []}, "async posts.update sends tags=[]")
        await async_client.aclose()

    asyncio.run(run_async())


FEATURE_REQUEST = {
    "id": 412,
    "title": "Post to a topic of a Telegram group",
    "summary": "Post our daily update to the Announcements topic of our Telegram group.",
    "status": "open",
    "team_answer": None,
    "team_replies": [],
    "votes_count": 1,
    "limit_id": "telegram.forum_topics",
    "platform": "telegram",
    "area": "posts",
    "source": "api",
    "created_at": "2026-11-04T10:00:00.000Z",
    "updated_at": "2026-11-04T10:00:00.000Z",
    "completed_at": None,
}

PLATFORM_LIMIT = {
    "id": "tiktok.delete",
    "kind": "platform",
    "kind_label": "The platform does not allow it",
    "area": "posts",
    "platforms": ["tiktok"],
    "title": "Delete a TikTok video",
    "says": "TikTok's API cannot delete a video.",
    "instead": "Delete the video in the TikTok app.",
    "requestable": False,
}


class FeatureRequestStub:
    """Answers like the /limits and /feature-requests routes and records the
    requests (through httpx.MockTransport, no network)."""

    def __init__(self):
        self.calls = []

    def handler(self, request):
        self.calls.append(request)
        path = request.url.raw_path.decode().split("?")[0]
        body = json.loads(request.content) if request.content else {}
        if path == "/v1/limits":
            return httpx.Response(
                200, json={"data": [PLATFORM_LIMIT], "kinds": {"platform": "The platform does not allow it"}}
            )
        if request.method == "POST" and body.get("limit_id") == "tiktok.delete":
            return httpx.Response(
                409,
                json={
                    "error": {
                        "code": "not_requestable",
                        "message": "TikTok's API cannot delete a video. A request cannot change this, so nothing was sent.",
                        "limit": PLATFORM_LIMIT,
                    }
                },
            )
        if request.method == "POST" and body.get("summary", "").startswith("Again"):
            return httpx.Response(200, json={"outcome": "already_requested", "data": FEATURE_REQUEST})
        if request.method == "POST":
            return httpx.Response(201, json={"outcome": "voted", "data": FEATURE_REQUEST})
        if path == "/v1/feature-requests":
            return httpx.Response(200, json={"data": [FEATURE_REQUEST]})
        return httpx.Response(200, json={"data": FEATURE_REQUEST})

    def last(self):
        return self.calls[-1]

    def path(self):
        return self.last().url.raw_path.decode()

    def body(self):
        return json.loads(self.last().content)


def check_feature_requests_transport():
    print("Limits and feature requests transport (stubbed, sync):")
    stub = FeatureRequestStub()
    client = OmniSocials(api_key="omsk_test_x", max_retries=0)
    client._http.close()
    client._http = httpx.Client(
        transport=httpx.MockTransport(stub.handler), headers=client._default_headers()
    )

    limits = client.limits.list(platform="tiktok", area="posts")
    ok(
        stub.last().method == "GET" and stub.path().startswith("/v1/limits")
        and stub.last().url.params == httpx.QueryParams({"platform": "tiktok", "area": "posts"}),
        "limits.list GETs /limits with platform and area",
    )
    ok(
        limits["data"][0]["requestable"] is False and "platform" in limits["kinds"],
        "limits.list returns data and kinds",
    )
    client.limits.list()
    ok(stub.path() == "/v1/limits", "limits.list() without filters sends no query")

    created = client.feature_requests.create(
        summary="Post our daily update to the Announcements topic of our Telegram group.",
        platform="telegram",
        limit_id="telegram.forum_topics",
    )
    ok(
        stub.last().method == "POST" and stub.path() == "/v1/feature-requests"
        and stub.body()
        == {
            "summary": "Post our daily update to the Announcements topic of our Telegram group.",
            "platform": "telegram",
            "limit_id": "telegram.forum_topics",
        },
        "feature_requests.create POSTs only the given keys (never source)",
    )
    ok(
        created["outcome"] == "voted" and created["data"]["id"] == 412,
        "feature_requests.create returns outcome and data",
    )
    again = client.feature_requests.create(summary="Again: post to a Telegram topic, please.")
    ok(again["outcome"] == "already_requested", "a 200 already_requested keeps the outcome")

    try:
        client.feature_requests.create(
            summary="Delete my TikTok videos from OmniSocials.", limit_id="tiktok.delete"
        )
        ok(False, "a not_requestable limit raises")
    except APIError as error:
        ok(
            error.status == 409 and error.code == "not_requestable"
            and error.body["error"]["limit"]["instead"] == "Delete the video in the TikTok app.",
            "409 not_requestable raises APIError with the limit in the body",
        )

    mine = client.feature_requests.list()
    ok(
        stub.last().method == "GET" and stub.path() == "/v1/feature-requests"
        and mine["data"][0]["status"] == "open",
        "feature_requests.list GETs /feature-requests",
    )
    one = client.feature_requests.get(412)
    ok(
        stub.path() == "/v1/feature-requests/412" and one["data"]["limit_id"] == "telegram.forum_topics",
        "feature_requests.get GETs /feature-requests/{id}",
    )
    client.close()

    print("Limits and feature requests transport (stubbed, async):")

    async def run_async():
        async_client = AsyncOmniSocials(api_key="omsk_test_x", max_retries=0)
        await async_client._http.aclose()
        async_client._http = httpx.AsyncClient(
            transport=httpx.MockTransport(stub.handler),
            headers=async_client._default_headers(),
        )
        await async_client.limits.list(area="inbox")
        ok(
            stub.last().url.params == httpx.QueryParams({"area": "inbox"}),
            "async limits.list sends area",
        )
        result = await async_client.feature_requests.create(
            summary="Reply to Google reviews from the inbox.", area="inbox", title="Google review replies"
        )
        ok(
            stub.body()
            == {"summary": "Reply to Google reviews from the inbox.", "title": "Google review replies", "area": "inbox"}
            and result["outcome"] == "voted",
            "async feature_requests.create sends the body and returns the outcome",
        )
        await async_client.feature_requests.list()
        ok(stub.path() == "/v1/feature-requests", "async feature_requests.list GETs /feature-requests")
        await async_client.feature_requests.get("412")
        ok(stub.path() == "/v1/feature-requests/412", "async feature_requests.get GETs /feature-requests/{id}")
        await async_client.aclose()

    asyncio.run(run_async())


def money_calls(ads):
    """Every ads call that can start or raise spend, with valid arguments."""
    return {
        "drafts.launch": lambda: ads.drafts.launch("g-1", confirm_budget_amount=10),
        "activate": lambda: ads.activate(7, 25),
        "activate_multi": lambda: ads.activate_multi([7, 8], 25),
        "resume": lambda: ads.resume(7),
        "update": lambda: ads.update(7, budget={"amount": 50, "currency": "EUR"}, confirm_budget_amount=50),
    }


def check_ads_transport():
    print("Ads transport (stubbed, sync):")
    stub = StubAPI()
    client = OmniSocials(api_key="omsk_test_x", max_retries=2)
    client._http.close()
    client._http = httpx.Client(
        transport=httpx.MockTransport(stub.handler), headers=client._default_headers()
    )

    stub.reset(201)
    client.ads.drafts.create(**DRAFT)
    ok(
        stub.calls[-1].method == "POST" and stub.path() == "/v1/ads/drafts",
        "ads.drafts.create POSTs /ads/drafts",
    )
    ok(stub.body() == DRAFT, "ads.drafts.create sends the draft (nested None kept)")

    stub.reset(200)
    client.ads.drafts.update("g 1/x", **DRAFT)
    ok(
        stub.calls[-1].method == "PUT" and stub.path() == "/v1/ads/drafts/g%201%2Fx",
        "ads.drafts.update PUTs /ads/drafts/{group_id} with the id encoded",
    )
    ok(stub.body() == DRAFT, "ads.drafts.update sends the full body")

    client.ads.drafts.launch("g-1", confirm_budget_amount=10)
    ok(
        stub.calls[-1].method == "POST" and stub.path() == "/v1/ads/drafts/g-1/launch",
        "ads.drafts.launch POSTs /ads/drafts/{group_id}/launch",
    )
    ok(stub.body() == {"confirm_budget_amount": 10}, "ads.drafts.launch sends the confirmed amount")
    client.ads.drafts.launch("g-1", confirm_budget_amounts={"7": 10, "8": 20})
    ok(
        stub.body() == {"confirm_budget_amounts": {"7": 10, "8": 20}},
        "ads.drafts.launch sends per campaign amounts",
    )

    client.ads.activate(7, 25)
    ok(
        stub.calls[-1].method == "POST" and stub.path() == "/v1/ads/campaigns/7/activate",
        "ads.activate POSTs /ads/campaigns/{id}/activate",
    )
    ok(stub.body() == {"confirm_budget_amount": 25}, "ads.activate sends confirm_budget_amount")

    client.ads.activate("51", 25)
    ok(
        stub.path() == "/v1/ads/campaigns/51/activate",
        "ads.activate takes the id as a string (the API sends ids as strings)",
    )

    client.ads.activate_multi([7, 8], 25)
    ok(
        stub.path() == "/v1/ads/campaigns/activate-multi"
        and stub.body() == {"campaign_ids": [7, 8], "confirm_budget_amount": 25},
        "ads.activate_multi sends campaign_ids and confirm_budget_amount",
    )

    client.ads.drafts.attach_account("g-1", platform="meta", ad_account_id=3)
    ok(
        stub.path() == "/v1/ads/drafts/g-1/account"
        and stub.body() == {"platform": "meta", "ad_account_id": 3},
        "ads.drafts.attach_account POSTs the platform and the ad account",
    )

    client.ads.list(status="active", limit=5)
    ok(
        stub.calls[-1].method == "GET"
        and stub.calls[-1].url.params == httpx.QueryParams({"status": "active", "limit": "5"}),
        "ads.list sends only the given filters",
    )

    for name, call in money_calls(client.ads).items():
        stub.reset(502)
        try:
            call()
        except ServerError:
            pass
        else:
            raise AssertionError(f"FAILED: ads.{name} did not raise on a 502")
        ok(len(stub.calls) == 1, f"ads.{name} after a 502 is sent exactly once")

    stub.reset("drop")
    try:
        client.ads.drafts.launch("g-1", confirm_budget_amount=10)
    except APIConnectionError:
        pass
    else:
        raise AssertionError("FAILED: a lost connection did not raise")
    ok(len(stub.calls) == 1, "ads.drafts.launch after a lost connection is sent exactly once")

    stub.reset(429, 200)
    client.ads.activate(7, 25)
    ok(len(stub.calls) == 2, "ads.activate after a 429 is retried")

    stub.reset(502, 200)
    result = client.ads.capabilities()
    ok(
        len(stub.calls) == 2 and result == {"data": {"ok": True}},
        "ads.capabilities (a read) after a 502 is retried",
    )
    client.close()

    print("Ads transport (stubbed, async):")

    async def run_async():
        async_client = AsyncOmniSocials(api_key="omsk_test_x", max_retries=2)
        await async_client._http.aclose()
        async_client._http = httpx.AsyncClient(
            transport=httpx.MockTransport(stub.handler),
            headers=async_client._default_headers(),
        )

        stub.reset(200)
        await async_client.ads.drafts.update("g-1", **DRAFT)
        ok(
            stub.calls[-1].method == "PUT" and stub.path() == "/v1/ads/drafts/g-1",
            "async ads.drafts.update PUTs /ads/drafts/{group_id}",
        )

        for name, call in money_calls(async_client.ads).items():
            stub.reset(502)
            try:
                await call()
            except ServerError:
                pass
            else:
                raise AssertionError(f"FAILED: async ads.{name} did not raise on a 502")
            ok(len(stub.calls) == 1, f"async ads.{name} after a 502 is sent exactly once")

        stub.reset(502, 200)
        await async_client.ads.capabilities()
        ok(len(stub.calls) == 2, "async ads.capabilities after a 502 is retried")
        await async_client.aclose()

    asyncio.run(run_async())


def build_signature(secret, timestamp, raw_body):
    """Mirror backend/services/webhooks/webhookDispatcher.js signPayload():
    HMAC-SHA256 hex over `${timestamp}.${rawBody}`, header `t=<ts>,v1=<hex>`.
    """
    signed_value = f"{timestamp}.{raw_body}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), signed_value, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def check_webhook_verification():
    print("Webhook verification:")
    secret = "whsec_test_secret_abc123"
    event = {
        "id": "e7c9a1b2-3d4e-5f6a-7b8c-9d0e1f2a3b4c",
        "type": "post.published",
        "created_at": "2026-07-14T10:00:05Z",
        "data": {"post_id": "123", "status": "posted"},
    }
    raw_body = json.dumps(event)
    timestamp = int(time.time())
    signature = build_signature(secret, timestamp, raw_body)

    parsed = verify_webhook_signature(raw_body, signature, secret)
    ok(parsed == event, "valid signature verifies and returns the parsed event (str)")

    parsed_bytes = verify_webhook_signature(raw_body.encode("utf-8"), signature, secret)
    ok(parsed_bytes == event, "valid signature verifies with bytes payload")

    rejected = {
        "id": "e7c9a1b2-3d4e-5f6a-7b8c-9d0e1f2a3b4d",
        "type": "post.rejected",
        "created_at": "2026-10-02T09:00:05.000Z",
        "data": {
            "post_id": "123456",
            "workspace_id": 789,
            "status": "rejected",
            "targets": [],
            "approval": {
                "status": "rejected",
                "decided_by": "c4a09e1d",
                "reason": "Wrong product photo",
            },
        },
    }
    rejected_body = json.dumps(rejected)
    parsed_rejected = verify_webhook_signature(
        rejected_body, build_signature(secret, timestamp, rejected_body), secret
    )
    ok(
        parsed_rejected["type"] == "post.rejected"
        and parsed_rejected["data"]["approval"] == rejected["data"]["approval"],
        "post.rejected event keeps its approval object",
    )

    ad_event = {
        "id": "b1f2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
        "type": "ad.status_changed",
        "created_at": "2026-07-13T10:00:05Z",
        "data": {
            "campaign_id": 42,
            "workspace_id": "456",
            "name": "Boost: Summer launch post",
            "platform": "meta",
            "campaign_type": "boost",
            "status": "active",
            "previous_status": "pending_review",
            "external_campaign_id": "23851234567890123",
            "budget": {"type": "daily", "amount": 10, "currency": "EUR"},
        },
    }
    ad_body = json.dumps(ad_event)
    parsed_ad = verify_webhook_signature(
        ad_body, build_signature(secret, timestamp, ad_body), secret
    )
    ok(
        parsed_ad["type"] == "ad.status_changed" and parsed_ad["data"] == ad_event["data"],
        "ad.status_changed event verifies and keeps its campaign data",
    )

    tampered = raw_body.replace("posted", "hacked")
    try:
        verify_webhook_signature(tampered, signature, secret)
    except WebhookVerificationError:
        ok(True, "tampered body raises WebhookVerificationError")
    else:
        raise AssertionError("FAILED: tampered body did not raise")

    stale_ts = int(time.time()) - 3600
    stale_signature = build_signature(secret, stale_ts, raw_body)
    try:
        verify_webhook_signature(raw_body, stale_signature, secret)
    except WebhookVerificationError:
        ok(True, "stale timestamp (1h old) raises WebhookVerificationError")
    else:
        raise AssertionError("FAILED: stale timestamp did not raise")

    parsed_stale = verify_webhook_signature(
        raw_body, stale_signature, secret, tolerance=None
    )
    ok(parsed_stale == event, "tolerance=None skips the timestamp check")

    try:
        verify_webhook_signature(raw_body, signature, "wrong_secret")
    except WebhookVerificationError:
        ok(True, "wrong secret raises WebhookVerificationError")
    else:
        raise AssertionError("FAILED: wrong secret did not raise")

    for bad_header in ("", "v1=abc", f"t={timestamp}", "t=notanint,v1=abc", None):
        try:
            verify_webhook_signature(raw_body, bad_header, secret)
        except WebhookVerificationError:
            ok(True, f"malformed header {bad_header!r} raises")
        else:
            raise AssertionError(f"FAILED: malformed header {bad_header!r} did not raise")


if __name__ == "__main__":
    check_client_surface()
    check_construction_guards()
    check_tags_transport()
    check_feature_requests_transport()
    check_ads_transport()
    check_webhook_verification()
    print(f"\nAll {CHECKS} checks passed.")
