"""Internal helpers shared by the client core and the resource classes."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Union

__all__ = ["NotGiven", "NOT_GIVEN", "drop_none", "join_list"]


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
