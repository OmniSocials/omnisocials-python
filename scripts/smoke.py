"""Offline smoke test for the omnisocials SDK.

Run from sdk/python/:  python3 scripts/smoke.py

Verifies (without any network access):
- the package imports and both clients construct
- every resource exposes every expected method (sync and async)
- verify_webhook_signature round-trips against a signature built exactly
  like backend/services/webhooks/webhookDispatcher.js
- tampered bodies and stale timestamps are rejected
- a missing API key raises AuthenticationError at construction time
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
    "accounts": ["list", "get"],
    "analytics": ["post", "posts", "overview", "accounts", "best_times"],
    "locations": ["search", "validate"],
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
    check_webhook_verification()
    print(f"\nAll {CHECKS} checks passed.")
