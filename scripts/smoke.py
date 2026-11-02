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
"""

import asyncio
import hashlib
import hmac
import inspect
import json
import os
import sys
import time

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
    "webhooks": ["list", "get", "create", "update", "delete", "rotate_secret"],
}


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
    check_webhook_verification()
    print(f"\nAll {CHECKS} checks passed.")
