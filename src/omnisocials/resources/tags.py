"""Tags resource: the workspace's own labels for its posts (a hook style, a
format), to filter and compare posts in Analytics. Tags never go to a
platform.

Set them on a post with ``tags=`` on posts.create / create_and_publish /
update, in bulk with :meth:`Tags.apply`, filter with ``tag=`` on posts.list
and analytics.overview, and compare them with analytics.tags."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .._utils import drop_none, join_list

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Tags", "AsyncTags", "TagRef", "TagFilter"]

# A tag reference: a tag id, or a tag name (case-insensitive). In ``add`` /
# ``set`` (and ``tags=`` on posts) a name that does not exist yet becomes a
# new tag of the workspace.
TagRef = Union[str, int]
# The ``tag`` filter: one id or name, or several (a post matches any of them).
TagFilter = Union[str, int, Sequence[TagRef]]


def tag_query(tag: Optional[TagFilter]) -> Optional[str]:
    """Serialize the ``tag`` filter: one id or name, or a list joined with ","."""
    if tag is None:
        return None
    if isinstance(tag, (str, int)):
        return str(tag)
    return join_list([str(item) for item in tag])


def _apply_body(
    post_ids: Sequence[Union[str, int]],
    add: Optional[Sequence[TagRef]],
    remove: Optional[Sequence[TagRef]],
    set: Optional[Sequence[TagRef]],
) -> dict:
    return drop_none(
        {
            "post_ids": [str(post_id) for post_id in post_ids],
            "add": add,
            "remove": remove,
            "set": set,
        }
    )


class Tags:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /tags`` - every tag of the workspace, by name. Each tag is
        ``{"id", "name", "color", "created_at"}``. Scope ``posts:read``."""
        return self._client.request("GET", "/tags")

    def create(self, *, name: str, color: Optional[str] = None) -> Any:
        """``POST /tags`` - create a tag. ``name`` is at most 40 characters
        and unique in the workspace (case-insensitive); ``color`` is one of
        blue, green, orange, red, purple, pink, teal, yellow, brown, gray
        (omit it to get the next colour). At most 200 tags per workspace.

        Errors: ``409 tag_exists`` (the existing tag is in
        ``error.body["error"]["tag"]``), ``409 tag_limit_reached``,
        ``400 invalid_tag_name`` / ``invalid_tag_color``.
        """
        return self._client.request(
            "POST", "/tags", json=drop_none({"name": name, "color": color})
        )

    def update(
        self,
        tag_id: Union[str, int],
        *,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Any:
        """``PATCH /tags/{id}`` - rename or recolour a tag. Only the keys
        you pass are sent; posts keep the tag. Errors: ``404 tag_not_found``,
        ``409 tag_exists``."""
        body = drop_none({"name": name, "color": color})
        return self._client.request("PATCH", f"/tags/{tag_id}", json=body)

    def delete(self, tag_id: Union[str, int]) -> Any:
        """``DELETE /tags/{id}`` - delete a tag and take it off every post
        (the posts stay). Returns ``{"data": {"tag", "posts_untagged"}}``."""
        return self._client.request("DELETE", f"/tags/{tag_id}")

    def apply(
        self,
        *,
        post_ids: Sequence[Union[str, int]],
        add: Optional[Sequence[TagRef]] = None,
        remove: Optional[Sequence[TagRef]] = None,
        set: Optional[Sequence[TagRef]] = None,
    ) -> Any:
        """``POST /tags/apply`` - add, remove or replace the tags of up to
        500 posts at once, published ones included.

        ``add``, ``remove`` and ``set`` take tag ids or names; a new name in
        ``add`` or ``set`` becomes a tag. ``set`` replaces a post's tags
        (``set=[]`` removes them all), ``add`` and ``remove`` change only the
        tags you name. Returns ``{"data": {"updated", "posts": [{"id",
        "tags"}], "not_found"}}``; ``not_found`` lists the post ids that are
        not posts of this workspace. Errors: ``400 invalid_post_ids`` /
        ``too_many_posts`` / ``too_many_tags`` / ``invalid_tags``,
        ``404 tag_not_found``.
        """
        return self._client.request(
            "POST", "/tags/apply", json=_apply_body(post_ids, add, remove, set)
        )


class AsyncTags:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /tags`` - every tag of the workspace (see :class:`Tags`)."""
        return await self._client.request("GET", "/tags")

    async def create(self, *, name: str, color: Optional[str] = None) -> Any:
        """``POST /tags`` - create a tag (see :meth:`Tags.create`)."""
        return await self._client.request(
            "POST", "/tags", json=drop_none({"name": name, "color": color})
        )

    async def update(
        self,
        tag_id: Union[str, int],
        *,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Any:
        """``PATCH /tags/{id}`` - rename or recolour a tag."""
        body = drop_none({"name": name, "color": color})
        return await self._client.request("PATCH", f"/tags/{tag_id}", json=body)

    async def delete(self, tag_id: Union[str, int]) -> Any:
        """``DELETE /tags/{id}`` - delete a tag and take it off every post."""
        return await self._client.request("DELETE", f"/tags/{tag_id}")

    async def apply(
        self,
        *,
        post_ids: Sequence[Union[str, int]],
        add: Optional[Sequence[TagRef]] = None,
        remove: Optional[Sequence[TagRef]] = None,
        set: Optional[Sequence[TagRef]] = None,
    ) -> Any:
        """``POST /tags/apply`` - tag up to 500 posts at once (see
        :meth:`Tags.apply`)."""
        return await self._client.request(
            "POST", "/tags/apply", json=_apply_body(post_ids, add, remove, set)
        )
