"""Pinterest resource: product Pins for product tagging (list + validate)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Pinterest", "AsyncPinterest"]


class Pinterest:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list_products(
        self,
        *,
        source: Optional[str] = None,
        product_group_id: Optional[str] = None,
        bookmark: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Any:
        """``GET /pinterest/products`` - list the product Pins of the
        connected Pinterest account.

        Pass a result's ``pin_id`` in ``pinterest["product_tags"]`` on a
        post to tag the product on the Pin (max 24 per Pin). Pinterest only
        accepts a product Pin that is public, belongs to the same account
        and links to a website that account claimed; products of other
        merchants cannot be tagged.

        ``source="catalog"`` reads the Pinterest catalog (with ``price``,
        ``currency``, ``availability``, ``item_id``) and needs catalog
        access, which is given one time in the OmniSocials composer
        (Pinterest options, Add products, Connect catalog).
        ``product_group_id`` and ``page_size`` (1 to 100, default 25) apply
        to this source only. ``source="pins"`` reads the account's own Pins
        and works on every connection; one call scans up to 250 Pins, so
        ``products`` can be empty while ``bookmark`` is set (call again with
        the bookmark). When ``source`` is left out the API uses ``catalog``
        when the connection has catalog access, else ``pins``.

        The response is not the usual ``{"data"}`` envelope:
        ``{"products": [...], "bookmark", "source", "catalog_access"}`` on
        success (plus ``product_groups`` and ``product_group_id`` for the
        catalog source), or ``{"error": {"code", "message"}}`` without
        ``products`` when the list could not be read, both with HTTP 200
        (codes: ``pinterest_not_connected``,
        ``pinterest_catalog_access_required``, ``platform_error``). A bad
        ``source`` or ``product_group_id`` raises a 400
        ``ValidationError`` instead.
        """
        return self._client.request(
            "GET",
            "/pinterest/products",
            query={
                "source": source,
                "product_group_id": product_group_id,
                "bookmark": bookmark,
                "page_size": page_size,
            },
        )

    def validate_product(self, id: str) -> Any:
        """``GET /pinterest/products/validate?id=`` - check whether a Pin
        can be used in ``pinterest["product_tags"]`` before creating the
        post. ``id`` is a Pin id or a Pin link
        (``https://www.pinterest.com/pin/<id>/``). Returns
        ``{"valid", "pin_id", ...}``; ``unverified: True`` means the check
        could not run and the publish step is the final check."""
        return self._client.request(
            "GET", "/pinterest/products/validate", query={"id": id}
        )


class AsyncPinterest:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list_products(
        self,
        *,
        source: Optional[str] = None,
        product_group_id: Optional[str] = None,
        bookmark: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Any:
        """``GET /pinterest/products`` - list the product Pins of the
        connected Pinterest account.

        Pass a result's ``pin_id`` in ``pinterest["product_tags"]`` on a
        post to tag the product on the Pin (max 24 per Pin). Pinterest only
        accepts a product Pin that is public, belongs to the same account
        and links to a website that account claimed; products of other
        merchants cannot be tagged.

        ``source="catalog"`` reads the Pinterest catalog (with ``price``,
        ``currency``, ``availability``, ``item_id``) and needs catalog
        access, which is given one time in the OmniSocials composer
        (Pinterest options, Add products, Connect catalog).
        ``product_group_id`` and ``page_size`` (1 to 100, default 25) apply
        to this source only. ``source="pins"`` reads the account's own Pins
        and works on every connection; one call scans up to 250 Pins, so
        ``products`` can be empty while ``bookmark`` is set (call again with
        the bookmark). When ``source`` is left out the API uses ``catalog``
        when the connection has catalog access, else ``pins``.

        The response is not the usual ``{"data"}`` envelope:
        ``{"products": [...], "bookmark", "source", "catalog_access"}`` on
        success (plus ``product_groups`` and ``product_group_id`` for the
        catalog source), or ``{"error": {"code", "message"}}`` without
        ``products`` when the list could not be read, both with HTTP 200
        (codes: ``pinterest_not_connected``,
        ``pinterest_catalog_access_required``, ``platform_error``). A bad
        ``source`` or ``product_group_id`` raises a 400
        ``ValidationError`` instead.
        """
        return await self._client.request(
            "GET",
            "/pinterest/products",
            query={
                "source": source,
                "product_group_id": product_group_id,
                "bookmark": bookmark,
                "page_size": page_size,
            },
        )

    async def validate_product(self, id: str) -> Any:
        """``GET /pinterest/products/validate?id=`` - check whether a Pin
        can be used in ``pinterest["product_tags"]`` before creating the
        post. ``id`` is a Pin id or a Pin link
        (``https://www.pinterest.com/pin/<id>/``). Returns
        ``{"valid", "pin_id", ...}``; ``unverified: True`` means the check
        could not run and the publish step is the final check."""
        return await self._client.request(
            "GET", "/pinterest/products/validate", query={"id": id}
        )
