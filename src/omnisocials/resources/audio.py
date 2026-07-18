"""Audio resource: Instagram Reels licensed audio search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Audio", "AsyncAudio"]


class Audio:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def search(
        self, query: Optional[str] = None, type: Optional[str] = None
    ) -> Any:
        """``GET /audio/search?q=&type=`` - search Meta's licensed audio
        catalog for Instagram Reels. Omit ``query`` for trending audio;
        ``type`` is ``"music"`` (server default) or ``"original_sound"``.
        Use a result's ``audio_id`` as ``instagram.audio_id`` on a reel post
        (with optional ``instagram.audio_volume`` /
        ``instagram.video_volume``, integers 0-100). ``preview_url`` is
        temporary (~1.5 days); never persist it."""
        return self._client.request(
            "GET", "/audio/search", query={"q": query, "type": type}
        )


class AsyncAudio:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def search(
        self, query: Optional[str] = None, type: Optional[str] = None
    ) -> Any:
        """``GET /audio/search?q=&type=`` - search Meta's licensed audio
        catalog for Instagram Reels. Omit ``query`` for trending audio;
        ``type`` is ``"music"`` (server default) or ``"original_sound"``.
        Use a result's ``audio_id`` as ``instagram.audio_id`` on a reel post
        (with optional ``instagram.audio_volume`` /
        ``instagram.video_volume``, integers 0-100). ``preview_url`` is
        temporary (~1.5 days); never persist it."""
        return await self._client.request(
            "GET", "/audio/search", query={"q": query, "type": type}
        )
