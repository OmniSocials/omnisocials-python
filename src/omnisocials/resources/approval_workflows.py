"""Approval workflows resource: the workflows configured in the dashboard
(Approvals). List them here and route a post through one at create time via
``approval_workflow_id`` on ``posts.create``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["ApprovalWorkflows", "AsyncApprovalWorkflows"]


class ApprovalWorkflows:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /approval-workflows`` - the workflows this workspace can use
        (company-wide plus workspace-bound), with steps and named approvers."""
        return self._client.request("GET", "/approval-workflows")


class AsyncApprovalWorkflows:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /approval-workflows`` - the workflows this workspace can use
        (company-wide plus workspace-bound), with steps and named approvers."""
        return await self._client.request("GET", "/approval-workflows")
