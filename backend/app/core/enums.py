"""Shared RBAC roles for the AssetFlow foundation.

Every module's ``deps.py`` imports :class:`Role` from here when the foundation is
present (falling back to a byte-identical local definition otherwise). Because
all modules resolve to this one enum, principals minted by
:mod:`app.core.security` compare equal to the roles each module's ``require_roles``
gate checks against.
"""
from __future__ import annotations

import enum


class Role(str, enum.Enum):
    """RBAC roles, sourced from the authenticated principal's ``role`` claim."""

    EMPLOYEE = "employee"
    DEPARTMENT_HEAD = "department_head"
    TECHNICIAN = "technician"
    ASSET_MANAGER = "asset_manager"
    ADMIN = "admin"
