"""Webhook signature verification.

OmniSocials signs every webhook delivery with HMAC-SHA256 (Stripe-style):

- Header: ``X-OmniSocials-Signature: t=<unix>,v1=<hex>``
- Signed value: ``"{timestamp}.{raw_body}"`` (UTF-8), keyed with the
  webhook's secret, hex digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional, Union

from ._errors import WebhookVerificationError

__all__ = ["verify_webhook_signature"]


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature: str,
    secret: str,
    tolerance: Optional[int] = 300,
) -> Dict[str, Any]:
    """Verify an OmniSocials webhook delivery and return the parsed event.

    Args:
        payload: The raw request body, exactly as received (``str`` or
            ``bytes``). Do not parse and re-serialize it first - the
            signature is over the raw bytes.
        signature: The ``X-OmniSocials-Signature`` header value, of the form
            ``t=<unix>,v1=<hex>``.
        secret: The webhook's signing secret (returned once when the webhook
            is created, or via rotate_secret).
        tolerance: Maximum allowed age (and future skew) of the signed
            timestamp, in seconds. Defaults to 300. Pass ``None`` to skip
            the timestamp check (not recommended).

    Returns:
        The parsed event as a dict.

    Raises:
        WebhookVerificationError: If the header is malformed, the timestamp
            is outside the tolerance window, or the signature does not match.
    """
    if isinstance(payload, (bytes, bytearray)):
        try:
            body_str = bytes(payload).decode("utf-8")
        except UnicodeDecodeError:
            raise WebhookVerificationError("Payload is not valid UTF-8.") from None
    elif isinstance(payload, str):
        body_str = payload
    else:
        raise WebhookVerificationError(
            f"payload must be str or bytes, got {type(payload).__name__}."
        )

    if not isinstance(signature, str) or not signature:
        raise WebhookVerificationError("Missing signature header.")

    timestamp: Optional[int] = None
    candidates: List[str] = []
    for pair in signature.split(","):
        key, _, value = pair.strip().partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                raise WebhookVerificationError(
                    "Malformed signature header: non-integer timestamp."
                ) from None
        elif key == "v1":
            candidates.append(value)

    if timestamp is None:
        raise WebhookVerificationError(
            "Malformed signature header: missing 't=' timestamp."
        )
    if not candidates:
        raise WebhookVerificationError(
            "Malformed signature header: missing 'v1=' signature."
        )

    if tolerance is not None:
        now = int(time.time())
        if abs(now - timestamp) > tolerance:
            raise WebhookVerificationError(
                f"Timestamp outside the tolerance window "
                f"({abs(now - timestamp)}s > {tolerance}s). "
                "The delivery may be stale or replayed."
            )

    signed_value = f"{timestamp}.{body_str}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_value, hashlib.sha256).hexdigest()

    if not any(hmac.compare_digest(expected, candidate) for candidate in candidates):
        raise WebhookVerificationError(
            "Signature mismatch: the payload was not signed with this secret, "
            "or the body was modified in transit."
        )

    try:
        event = json.loads(body_str)
    except ValueError:
        raise WebhookVerificationError("Payload is not valid JSON.") from None
    if not isinstance(event, dict):
        raise WebhookVerificationError("Payload is not a JSON object.")
    return event
