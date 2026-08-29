"""Inbox resource: social inbox conversations, messages, and replies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import quote

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Inbox", "AsyncInbox"]


def _encode_id(conversation_id: str) -> str:
    """Percent-encode a conversation id for use as a single path segment.

    LinkedIn conversation ids contain reserved characters such as ``:`` and
    ``()`` (e.g. ``linkedin_comment_urn:li:activity:123``), so every reserved
    character must be encoded; ``safe=""`` leaves nothing unescaped.
    """
    return quote(conversation_id, safe="")


def _reply_body(
    *,
    text: str,
    attachment_url: Optional[str],
    attachment_type: Optional[str],
) -> Dict[str, Any]:
    return drop_none(
        {
            "text": text,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
        }
    )


class Inbox:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list_conversations(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        unread: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``, ``"tiktok"``, ``"youtube"``, ``"x"``, ``"threads"``),
        ``type`` (``"dm"``, ``"comment"``, ``"mention"``), and ``unread``.
        ``limit`` is 1-100. Uses cursor pagination: pass the previous
        response's ``pagination.next_cursor`` as ``cursor`` to keep paging
        while ``pagination.has_more`` is true.

        Threads conversations are ``type`` ``"comment"`` (replies people
        leave on your Threads posts; ``conversation_id`` looks like
        ``threads_comment_<rootPostId>``) and ``"mention"``
        (``threads_mention_<postId>``); there are no Threads DMs. Threads
        inbox is currently rolling out; until Meta approves the permissions
        it is disabled on production, and it needs a Threads connection with
        the reply permission.
        """
        return self._client.request(
            "GET",
            "/inbox/conversations",
            query={
                "platform": platform,
                "type": type,
                "unread": unread,
                "limit": limit,
                "cursor": cursor,
            },
        )

    def get_messages(
        self,
        conversation_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations/{id}/messages`` - full message thread for
        one conversation, newest first.

        Uses cursor pagination (``limit`` / ``cursor``). The id is URL-encoded
        for you, so pass it exactly as returned (LinkedIn ids contain ``:`` and
        ``()``).
        """
        return self._client.request(
            "GET",
            f"/inbox/conversations/{_encode_id(conversation_id)}/messages",
            query={"limit": limit, "cursor": cursor},
        )

    def mark_read(self, conversation_id: str) -> Any:
        """``POST /inbox/conversations/{id}/read`` - mark every message in the
        conversation as read.

        Returns ``{"conversation_id", "marked_read"}`` where ``marked_read`` is
        the count of messages that were newly marked read.
        """
        return self._client.request(
            "POST", f"/inbox/conversations/{_encode_id(conversation_id)}/read"
        )

    def reply(
        self,
        conversation_id: str,
        text: str,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        Optionally attach a single media asset by public URL with
        ``attachment_url`` + ``attachment_type`` (``"image"``, ``"video"``,
        ``"audio"``, or ``"file"``). Returns the created outbound message.

        X DM replies cost 2 prepaid credits per send, debited from the
        company balance before the send and auto-refunded if the send fails.
        Can fail with ``402`` and code ``insufficient_credits`` (balance
        can't cover the 2 credits) or ``x_inbox_suspended`` (the workspace's
        X inbox auto-suspended at zero balance; top up and re-enable it in
        the dashboard to resume - DMs that arrive while suspended are not
        recovered).

        Threads replies publish as native Threads replies. Threads inbox is
        currently rolling out; until Meta approves the permissions it is
        disabled on production, and it needs a Threads connection with the
        reply permission: a ``401`` with code ``reauth_required`` means the
        connection lacks it (reconnect Threads).
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
        return self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )

    def hide(self, message_id: str, *, hide: bool = True) -> Any:
        """``POST /inbox/messages/{id}/hide`` - hide or unhide a reply
        someone left on one of your Threads posts, as the post owner
        (Threads only for now).

        ``hide=True`` (the default) hides the reply, ``hide=False`` unhides
        it. Only incoming top-level replies can be hidden (Threads does not
        allow hiding nested replies); the message keeps its place in the
        conversation. Returns ``{"data": <message>}`` with ``hidden``
        flipped. Requires the ``inbox:write`` scope.

        Threads inbox is currently rolling out; until Meta approves the
        permissions it is disabled on production and calls return a clear
        error. Errors: ``400`` ``unsupported_platform`` (not an incoming
        Threads reply, or Threads inbox not available yet), ``400``
        ``not_hideable`` (nested reply or Threads refused), ``401``
        ``reauth_required`` (the Threads connection lacks the reply
        permission; reconnect Threads), ``404`` ``not_found`` (message not
        in this workspace) or ``account_not_connected`` (no Threads
        account).
        """
        return self._client.request(
            "POST",
            f"/inbox/messages/{_encode_id(message_id)}/hide",
            json={"hide": hide},
        )


class AsyncInbox:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list_conversations(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        unread: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``, ``"tiktok"``, ``"youtube"``, ``"x"``, ``"threads"``),
        ``type`` (``"dm"``, ``"comment"``, ``"mention"``), and ``unread``.
        ``limit`` is 1-100. Uses cursor pagination: pass the previous
        response's ``pagination.next_cursor`` as ``cursor`` to keep paging
        while ``pagination.has_more`` is true.

        Threads conversations are ``type`` ``"comment"`` (replies people
        leave on your Threads posts; ``conversation_id`` looks like
        ``threads_comment_<rootPostId>``) and ``"mention"``
        (``threads_mention_<postId>``); there are no Threads DMs. Threads
        inbox is currently rolling out; until Meta approves the permissions
        it is disabled on production, and it needs a Threads connection with
        the reply permission.
        """
        return await self._client.request(
            "GET",
            "/inbox/conversations",
            query={
                "platform": platform,
                "type": type,
                "unread": unread,
                "limit": limit,
                "cursor": cursor,
            },
        )

    async def get_messages(
        self,
        conversation_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations/{id}/messages`` - full message thread for
        one conversation, newest first.

        Uses cursor pagination (``limit`` / ``cursor``). The id is URL-encoded
        for you, so pass it exactly as returned (LinkedIn ids contain ``:`` and
        ``()``).
        """
        return await self._client.request(
            "GET",
            f"/inbox/conversations/{_encode_id(conversation_id)}/messages",
            query={"limit": limit, "cursor": cursor},
        )

    async def mark_read(self, conversation_id: str) -> Any:
        """``POST /inbox/conversations/{id}/read`` - mark every message in the
        conversation as read.

        Returns ``{"conversation_id", "marked_read"}`` where ``marked_read`` is
        the count of messages that were newly marked read.
        """
        return await self._client.request(
            "POST", f"/inbox/conversations/{_encode_id(conversation_id)}/read"
        )

    async def reply(
        self,
        conversation_id: str,
        text: str,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        Optionally attach a single media asset by public URL with
        ``attachment_url`` + ``attachment_type`` (``"image"``, ``"video"``,
        ``"audio"``, or ``"file"``). Returns the created outbound message.

        X DM replies cost 2 prepaid credits per send, debited from the
        company balance before the send and auto-refunded if the send fails.
        Can fail with ``402`` and code ``insufficient_credits`` (balance
        can't cover the 2 credits) or ``x_inbox_suspended`` (the workspace's
        X inbox auto-suspended at zero balance; top up and re-enable it in
        the dashboard to resume - DMs that arrive while suspended are not
        recovered).

        Threads replies publish as native Threads replies. Threads inbox is
        currently rolling out; until Meta approves the permissions it is
        disabled on production, and it needs a Threads connection with the
        reply permission: a ``401`` with code ``reauth_required`` means the
        connection lacks it (reconnect Threads).
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
        return await self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )

    async def hide(self, message_id: str, *, hide: bool = True) -> Any:
        """``POST /inbox/messages/{id}/hide`` - hide or unhide a reply
        someone left on one of your Threads posts, as the post owner
        (Threads only for now).

        ``hide=True`` (the default) hides the reply, ``hide=False`` unhides
        it. Only incoming top-level replies can be hidden (Threads does not
        allow hiding nested replies); the message keeps its place in the
        conversation. Returns ``{"data": <message>}`` with ``hidden``
        flipped. Requires the ``inbox:write`` scope.

        Threads inbox is currently rolling out; until Meta approves the
        permissions it is disabled on production and calls return a clear
        error. Errors: ``400`` ``unsupported_platform`` (not an incoming
        Threads reply, or Threads inbox not available yet), ``400``
        ``not_hideable`` (nested reply or Threads refused), ``401``
        ``reauth_required`` (the Threads connection lacks the reply
        permission; reconnect Threads), ``404`` ``not_found`` (message not
        in this workspace) or ``account_not_connected`` (no Threads
        account).
        """
        return await self._client.request(
            "POST",
            f"/inbox/messages/{_encode_id(message_id)}/hide",
            json={"hide": hide},
        )
