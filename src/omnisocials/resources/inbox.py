"""Inbox resource: social inbox conversations, messages, and replies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union
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
    text: Optional[str],
    attachment_url: Optional[str],
    attachment_type: Optional[str],
    include_next: Optional[bool],
) -> Dict[str, Any]:
    return drop_none(
        {
            "text": text,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
            "include_next": include_next,
        }
    )


def _next_query(
    *,
    platform: Optional[str],
    type: Optional[str],
    order: Optional[str],
    include_read: Optional[bool],
    exclude: Optional[Union[Sequence[str], str]],
) -> Dict[str, Any]:
    if exclude is not None and not isinstance(exclude, str):
        exclude = ",".join(exclude) or None
    return {
        "platform": platform,
        "type": type,
        "order": order,
        "include_read": include_read,
        "exclude": exclude,
    }


class Inbox:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list_conversations(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        unread: Optional[bool] = None,
        unanswered: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``, ``"tiktok"``, ``"youtube"``, ``"x"``, ``"threads"``),
        ``type`` (``"dm"``, ``"comment"``, ``"mention"``), ``unread``, and
        ``unanswered`` (only conversations that still need an answer: the
        customer's latest DM has no reply after it, for Instagram/Facebook
        DMs within the 24-hour messaging window only, or a comment/mention
        that has not been replied to and is not hidden; replies typed in
        the native apps count as answers, and read state is ignored, so use
        ``next()`` for a work queue). ``limit`` is 1-100. Uses cursor
        pagination: pass the previous
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
                "unanswered": unanswered,
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
        text: Optional[str] = None,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
        include_next: Optional[bool] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        On Facebook and Instagram DMs, optionally attach a single media asset
        by public URL with ``attachment_url`` + ``attachment_type``
        (``"image"``, ``"video"``, ``"audio"``, or ``"file"``); ``text`` is
        optional when ``attachment_url`` is set (an attachment-only reply is
        allowed). Other platforms are text-only. Returns the created
        outbound message, whose ``attachment`` field carries the same shape
        when the message has media.

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

        Pass ``include_next=True`` to also get ``"next"`` (the next
        conversation that needs an answer, the same object ``next()``
        returns under ``"data"``, using its default queue order and
        filters; ``None`` when nothing is waiting) and ``"remaining"`` in
        the response. Saves the extra call when working through the inbox.
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
            include_next=include_next,
        )
        return self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )

    def hide(self, message_id: str, *, hide: bool = True) -> Any:
        """``POST /inbox/messages/{id}/hide`` - hide or unhide a comment
        someone left on one of your posts, on the platform, as the post
        owner.

        Facebook, Instagram, TikTok, YouTube and Threads comments (Threads:
        incoming top-level replies only; Threads does not allow hiding
        nested replies). ``hide=True`` (the default) hides the comment,
        ``hide=False`` unhides it. On YouTube, hide sets the comment's
        moderation status to rejected, which removes it and its replies
        from public view; unhide publishes it again. The message keeps its
        place in the conversation and ``"hidden"`` flips on the returned
        message (``{"data": <message>}``); a hidden comment no longer
        counts as unanswered. Requires the ``inbox:write`` scope. The
        account must have been connected with the moderation permission
        (Facebook ``pages_manage_engagement``, Instagram
        ``instagram_business_manage_comments``).

        Errors: ``400`` ``unsupported_platform`` (not an incoming comment
        on a supported platform), ``400`` ``not_hideable`` (Threads nested
        reply, or Threads refused), ``401`` ``reauth_required`` (the
        Threads reply permission or the TikTok comments authorization is
        missing or expired), ``403`` ``reconnect_required`` (the account
        was connected without the comment-moderation permission; reconnect
        it in the dashboard), ``404`` ``not_found`` (message not in this
        workspace) or ``account_not_connected``, ``429`` ``quota_exceeded``
        (YouTube's daily API quota is used up; retry after midnight
        Pacific), ``502`` ``platform_error`` (the platform rejected the
        call). Threads inbox is currently rolling out; until Meta approves
        the permissions it is disabled on production and Threads calls
        return a clear error.
        """
        return self._client.request(
            "POST",
            f"/inbox/messages/{_encode_id(message_id)}/hide",
            json={"hide": hide},
        )

    def delete_message(self, message_id: str) -> Any:
        """``DELETE /inbox/messages/{id}`` - delete a comment someone left on
        one of your posts, on the platform and from the inbox.

        Facebook, Instagram and TikTok comments only: YouTube's API does not
        let a channel delete other people's comments, hide those instead
        (``hide()``). Replies under the deleted comment go with it (the
        platforms cascade the delete and the inbox mirrors that); their
        inbox ids come back as ``"removed_reply_ids"``. A comment that is
        already gone on the platform is still removed from the inbox. This
        cannot be undone. Returns ``{"data": {"id", "conversation_id",
        "removed_reply_ids"}}``. Requires the ``inbox:write`` scope.

        Errors: ``400`` ``unsupported_platform`` (not an incoming Facebook,
        Instagram or TikTok comment), ``401`` ``reauth_required`` (the
        TikTok comments authorization expired), ``403``
        ``reconnect_required`` (the account was connected without the
        comment-moderation permission; reconnect it in the dashboard),
        ``404`` ``not_found`` (message not in this workspace) or
        ``account_not_connected``, ``502`` ``platform_error`` (the platform
        rejected the call).
        """
        return self._client.request(
            "DELETE", f"/inbox/messages/{_encode_id(message_id)}"
        )

    def next(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        order: Optional[str] = None,
        include_read: Optional[bool] = None,
        exclude: Optional[Union[Sequence[str], str]] = None,
    ) -> Any:
        """``GET /inbox/next`` - the next conversation that needs an answer:
        a work queue for answering the inbox.

        Returns the oldest (by default) item that still needs a reply,
        together with its conversation so far and the post it belongs to,
        so a reply can be drafted from one call. An item needs an answer
        when it is the customer's latest DM with no reply after it
        (Instagram/Facebook DMs within the 24-hour messaging window only,
        since Meta refuses replies outside it), or a comment/mention that
        has not been replied to and is not hidden. Replies typed in the
        native apps count as answers (they are mirrored into the inbox), so
        a thread a colleague answered on their phone is not served again.
        Instagram mentions are skipped (no reply path). Looks at the last
        30 days of activity. Requires the ``inbox:read`` scope.

        Only unread items are served by default: marking a conversation
        read (``mark_read()``) is how to skip one for good; pass
        ``include_read=True`` to include read-but-unanswered items.
        ``exclude`` is a session-local skip: conversation ids (a sequence,
        or a comma-separated string) to leave out of this call, up to 100.
        ``order`` is ``"oldest"`` (default: the item that has waited
        longest first) or ``"newest"``. ``platform`` and ``type``
        (``"dm"``, ``"comment"``, ``"mention"``) narrow the queue.

        Returns ``{"data": ..., "remaining": int}``. ``"data"`` is
        ``{"conversation", "message", "messages"}``, or ``None`` when
        nothing is waiting. ``"message"`` is the unanswered incoming item
        itself (the customer's latest DM, or the specific comment): its
        ``"id"`` is what ``hide()`` and ``delete_message()`` take, its
        ``"conversation_id"`` is what ``reply()`` takes. ``"messages"`` is
        the conversation so far, oldest first (the most recent 50 messages
        for long DM threads). ``"remaining"`` is the number of unanswered
        items still waiting after this one (capped at 500), ``0`` when
        ``"data"`` is ``None``. To chain the queue, pass
        ``include_next=True`` to ``reply()`` and it returns the next item
        in the same response. Errors: ``400`` ``validation_error``
        (unknown platform, type or order).
        """
        return self._client.request(
            "GET",
            "/inbox/next",
            query=_next_query(
                platform=platform,
                type=type,
                order=order,
                include_read=include_read,
                exclude=exclude,
            ),
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
        unanswered: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``, ``"tiktok"``, ``"youtube"``, ``"x"``, ``"threads"``),
        ``type`` (``"dm"``, ``"comment"``, ``"mention"``), ``unread``, and
        ``unanswered`` (only conversations that still need an answer: the
        customer's latest DM has no reply after it, for Instagram/Facebook
        DMs within the 24-hour messaging window only, or a comment/mention
        that has not been replied to and is not hidden; replies typed in
        the native apps count as answers, and read state is ignored, so use
        ``next()`` for a work queue). ``limit`` is 1-100. Uses cursor
        pagination: pass the previous
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
                "unanswered": unanswered,
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
        text: Optional[str] = None,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
        include_next: Optional[bool] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        On Facebook and Instagram DMs, optionally attach a single media asset
        by public URL with ``attachment_url`` + ``attachment_type``
        (``"image"``, ``"video"``, ``"audio"``, or ``"file"``); ``text`` is
        optional when ``attachment_url`` is set (an attachment-only reply is
        allowed). Other platforms are text-only. Returns the created
        outbound message, whose ``attachment`` field carries the same shape
        when the message has media.

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

        Pass ``include_next=True`` to also get ``"next"`` (the next
        conversation that needs an answer, the same object ``next()``
        returns under ``"data"``, using its default queue order and
        filters; ``None`` when nothing is waiting) and ``"remaining"`` in
        the response. Saves the extra call when working through the inbox.
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
            include_next=include_next,
        )
        return await self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )

    async def hide(self, message_id: str, *, hide: bool = True) -> Any:
        """``POST /inbox/messages/{id}/hide`` - hide or unhide a comment
        someone left on one of your posts, on the platform, as the post
        owner.

        Facebook, Instagram, TikTok, YouTube and Threads comments (Threads:
        incoming top-level replies only; Threads does not allow hiding
        nested replies). ``hide=True`` (the default) hides the comment,
        ``hide=False`` unhides it. On YouTube, hide sets the comment's
        moderation status to rejected, which removes it and its replies
        from public view; unhide publishes it again. The message keeps its
        place in the conversation and ``"hidden"`` flips on the returned
        message (``{"data": <message>}``); a hidden comment no longer
        counts as unanswered. Requires the ``inbox:write`` scope. The
        account must have been connected with the moderation permission
        (Facebook ``pages_manage_engagement``, Instagram
        ``instagram_business_manage_comments``).

        Errors: ``400`` ``unsupported_platform`` (not an incoming comment
        on a supported platform), ``400`` ``not_hideable`` (Threads nested
        reply, or Threads refused), ``401`` ``reauth_required`` (the
        Threads reply permission or the TikTok comments authorization is
        missing or expired), ``403`` ``reconnect_required`` (the account
        was connected without the comment-moderation permission; reconnect
        it in the dashboard), ``404`` ``not_found`` (message not in this
        workspace) or ``account_not_connected``, ``429`` ``quota_exceeded``
        (YouTube's daily API quota is used up; retry after midnight
        Pacific), ``502`` ``platform_error`` (the platform rejected the
        call). Threads inbox is currently rolling out; until Meta approves
        the permissions it is disabled on production and Threads calls
        return a clear error.
        """
        return await self._client.request(
            "POST",
            f"/inbox/messages/{_encode_id(message_id)}/hide",
            json={"hide": hide},
        )

    async def delete_message(self, message_id: str) -> Any:
        """``DELETE /inbox/messages/{id}`` - delete a comment someone left on
        one of your posts, on the platform and from the inbox.

        Facebook, Instagram and TikTok comments only: YouTube's API does not
        let a channel delete other people's comments, hide those instead
        (``hide()``). Replies under the deleted comment go with it (the
        platforms cascade the delete and the inbox mirrors that); their
        inbox ids come back as ``"removed_reply_ids"``. A comment that is
        already gone on the platform is still removed from the inbox. This
        cannot be undone. Returns ``{"data": {"id", "conversation_id",
        "removed_reply_ids"}}``. Requires the ``inbox:write`` scope.

        Errors: ``400`` ``unsupported_platform`` (not an incoming Facebook,
        Instagram or TikTok comment), ``401`` ``reauth_required`` (the
        TikTok comments authorization expired), ``403``
        ``reconnect_required`` (the account was connected without the
        comment-moderation permission; reconnect it in the dashboard),
        ``404`` ``not_found`` (message not in this workspace) or
        ``account_not_connected``, ``502`` ``platform_error`` (the platform
        rejected the call).
        """
        return await self._client.request(
            "DELETE", f"/inbox/messages/{_encode_id(message_id)}"
        )

    async def next(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        order: Optional[str] = None,
        include_read: Optional[bool] = None,
        exclude: Optional[Union[Sequence[str], str]] = None,
    ) -> Any:
        """``GET /inbox/next`` - the next conversation that needs an answer:
        a work queue for answering the inbox.

        Returns the oldest (by default) item that still needs a reply,
        together with its conversation so far and the post it belongs to,
        so a reply can be drafted from one call. An item needs an answer
        when it is the customer's latest DM with no reply after it
        (Instagram/Facebook DMs within the 24-hour messaging window only,
        since Meta refuses replies outside it), or a comment/mention that
        has not been replied to and is not hidden. Replies typed in the
        native apps count as answers (they are mirrored into the inbox), so
        a thread a colleague answered on their phone is not served again.
        Instagram mentions are skipped (no reply path). Looks at the last
        30 days of activity. Requires the ``inbox:read`` scope.

        Only unread items are served by default: marking a conversation
        read (``mark_read()``) is how to skip one for good; pass
        ``include_read=True`` to include read-but-unanswered items.
        ``exclude`` is a session-local skip: conversation ids (a sequence,
        or a comma-separated string) to leave out of this call, up to 100.
        ``order`` is ``"oldest"`` (default: the item that has waited
        longest first) or ``"newest"``. ``platform`` and ``type``
        (``"dm"``, ``"comment"``, ``"mention"``) narrow the queue.

        Returns ``{"data": ..., "remaining": int}``. ``"data"`` is
        ``{"conversation", "message", "messages"}``, or ``None`` when
        nothing is waiting. ``"message"`` is the unanswered incoming item
        itself (the customer's latest DM, or the specific comment): its
        ``"id"`` is what ``hide()`` and ``delete_message()`` take, its
        ``"conversation_id"`` is what ``reply()`` takes. ``"messages"`` is
        the conversation so far, oldest first (the most recent 50 messages
        for long DM threads). ``"remaining"`` is the number of unanswered
        items still waiting after this one (capped at 500), ``0`` when
        ``"data"`` is ``None``. To chain the queue, pass
        ``include_next=True`` to ``reply()`` and it returns the next item
        in the same response. Errors: ``400`` ``validation_error``
        (unknown platform, type or order).
        """
        return await self._client.request(
            "GET",
            "/inbox/next",
            query=_next_query(
                platform=platform,
                type=type,
                order=order,
                include_read=include_read,
                exclude=exclude,
            ),
        )
