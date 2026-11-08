"""Internal helpers shared by the client core and the resource classes."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Union
from urllib.parse import quote

__all__ = [
    "NotGiven",
    "NOT_GIVEN",
    "RATE_LIMIT_ONLY",
    "check_path",
    "drop_none",
    "join_list",
    "path_segment",
]


class NotGiven:
    """Sentinel distinguishing "omitted" from an explicit ``None``.

    A few endpoints treat ``null`` as meaningful (for example
    ``media.update(folder_id=None)`` moves a file to the root folder), so
    ``None`` cannot double as "not provided" there.
    """

    _instance: Optional["NotGiven"] = None

    def __new__(cls) -> "NotGiven":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()

# ``request(..., retry=RATE_LIMIT_ONLY)``: retry only a 429. A call that can
# start ad spend uses it: after a 5xx, a timeout or a lost connection the first
# attempt may have gone through, so it is never sent again.
RATE_LIMIT_ONLY = "rate_limit"


def drop_none(mapping: Mapping[str, Any]) -> Dict[str, Any]:
    """Drop ``None`` and NOT_GIVEN values (top level only).

    Nested values are passed through untouched, so platform option dicts can
    still carry meaningful ``None`` values (e.g. ``x={"thread_parts": None}``
    on update clears an X thread).
    """
    return {
        key: value
        for key, value in mapping.items()
        if value is not None and not isinstance(value, NotGiven)
    }


def join_list(value: Union[str, Sequence[str], None]) -> Optional[str]:
    """Join a sequence into a comma-separated string; pass strings through."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return ",".join(str(item) for item in value)


def path_segment(value: Union[int, str]) -> str:
    """Percent-encode a caller-supplied id as exactly one URL path segment.

    ``safe=""`` also encodes ``/``, ``?``, ``#`` and ``%``, so an id cannot add a
    segment, start a query or a fragment, or carry an escape of its own (an id
    such as ``../webhooks/wh_1/rotate-secret#`` would otherwise move the call to
    another endpoint of the same API key). Every id that goes into a request
    path goes through this function.
    """
    return quote(str(value), safe="")


def check_path(path: str) -> str:
    """Refuse a request path with an empty, ``.`` or ``..`` segment.

    ``path_segment`` leaves ``.`` and ``..`` as they are, and URL normalisation
    drops such a segment or climbs one level, so an id of ``..`` would reach
    another endpoint. An empty id would reach the list route. Raises
    ``ValueError`` before anything is sent.
    """
    for segment in path.split("?", 1)[0].split("/")[1:]:
        if segment in ("", ".", ".."):
            raise ValueError(
                f"Invalid request path {path!r}: an id cannot be empty, '.' or '..'."
            )
    return path
